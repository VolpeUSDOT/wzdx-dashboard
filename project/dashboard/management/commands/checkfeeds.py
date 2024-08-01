import json
import os
from datetime import datetime, timedelta, timezone, tzinfo
from pathlib import Path
from typing import Any, Optional, Sequence

import iso8601
import requests
from dashboard.models import Feed, FeedStatus, OutdatedError, SchemaError, StaleError
from django.core.management.base import BaseCommand
from jsonschema import Draft7Validator, ValidationError
from jsonschema.exceptions import best_match
from referencing import Registry, Resource

# CONSTANTS
SCHEMA_FOLDER = Path(os.path.dirname(__file__)) / "schemas"

VERSION_TO_SCHEMA = {
    "4.2": "https://raw.githubusercontent.com/usdot-jpo-ode/wzdx/main/schemas/4.2/WorkZoneFeed.json",
    "4.1": "https://raw.githubusercontent.com/usdot-jpo-ode/wzdx/main/schemas/4.1/WorkZoneFeed.json",
    "4.0": "https://raw.githubusercontent.com/usdot-jpo-ode/wzdx/main/schemas/4.0/WZDxFeed.json",
    "3.1": "https://raw.githubusercontent.com/usdot-jpo-ode/wzdx/main/schemas/3.1/WZDxFeed.json",
    "3.0": "https://raw.githubusercontent.com/usdot-jpo-ode/wzdx/main/schemas/3.0/WZDxFeed.json",
    "2.0": "https://raw.githubusercontent.com/usdot-jpo-ode/wzdx/main/schemas/2.0/WZDxFeed.json",
}


# HELPER CLASSES


def get_schema_json(filename: str):
    with open(SCHEMA_FOLDER / filename, "r") as f:
        return json.load(f)


def retrieve_via_web(uri: str):
    print(f"requesting {uri}...")
    response = requests.get(uri)
    return Resource.from_contents(response.json())


def format_as_index(container: str, indices: Sequence):
    """Construct a single string containing indexing operations for the indices."""
    if not indices:
        return container
    return f"{container}[{']['.join(repr(index) for index in indices)}]"


def find_all_instances_key(
    obj: dict[str, Any], key: str, key_to_skip: Optional[str] = None
) -> list:
    values_found = []

    if key in obj:
        values_found.append(obj[key])
    for k, v in obj.items():
        if (k is None or k != key_to_skip) and isinstance(v, dict):
            item = find_all_instances_key(v, key, key_to_skip)
            if item:
                values_found += item

    return values_found


# GET ALL SCHEMAS AND SAVE IN REGISTRY (minimizes time to analyze schema)
REGISTRY = Registry(retrieve=retrieve_via_web).with_resources(
    [
        (
            "https://raw.githubusercontent.com/usdot-jpo-ode/wzdx/main/schemas/4.2/WorkZoneFeed.json",
            Resource.from_contents(get_schema_json("wzdx42.schema.json")),
        ),
        (
            "https://raw.githubusercontent.com/usdot-jpo-ode/wzdx/main/schemas/4.1/WorkZoneFeed.json",
            Resource.from_contents(get_schema_json("wzdx41.schema.json")),
        ),
        (
            "https://raw.githubusercontent.com/usdot-jpo-ode/wzdx/main/schemas/4.0/WZDxFeed.json",
            Resource.from_contents(get_schema_json("wzdx40.schema.json")),
        ),
        (
            "https://raw.githubusercontent.com/usdot-jpo-ode/wzdx/main/schemas/3.1/WZDxFeed.json",
            Resource.from_contents(get_schema_json("wzdx31.schema.json")),
        ),
    ]
)


# FEED CHECKER CLASSES
def is_offline(feed: Feed):
    """If feed cannot be reached at the correct URL"""
    return not bool(feed.feed_data)


def get_schema_errors(feed: Feed):
    """If feed fails to validate against JSON schema"""
    feed_data = feed.feed_data
    feed_version = feed.version

    errors: list[ValidationError] = []
    v = Draft7Validator({"$ref": VERSION_TO_SCHEMA[feed_version]}, registry=REGISTRY)

    for error in sorted(v.iter_errors(feed_data), key=str):
        errors.append(error)

    return errors


def outdated(feed: Feed):
    """If feed events haven't been updated in the last 14 days. Assumes feed matches the schema."""
    fourteen_days_ago = datetime.now(tz=timezone.utc) - timedelta(days=14)

    # Recursively get all instances of "update_date"
    all_update_dates = [
        iso8601.parse_date(update_date_string, default_timezone=timezone.utc)
        for update_date_string in find_all_instances_key(feed.feed_data, "update_date")
    ]

    is_outdated = (
        all([update_date < fourteen_days_ago for update_date in all_update_dates])
        if len(all_update_dates) > 0
        else False
    )

    return (
        is_outdated,
        max(all_update_dates),
    )


def stale(feed: Feed):
    """If feed contains events that ended more than 14 days ago. Assumes feed matches the schema."""
    fourteen_days_ago = datetime.now(tz=timezone.utc) - timedelta(days=14)

    # Recursively get all instances of "update_date"
    all_end_dates = [
        iso8601.parse_date(end_date_string, default_timezone=timezone.utc)
        for end_date_string in find_all_instances_key(feed.feed_data, "end_date")
    ]

    stale_events = [
        end_date for end_date in all_end_dates if end_date < fourteen_days_ago
    ]

    return stale_events


class Command(BaseCommand):
    help = "Check every feed for their current status."

    def handle(self, *args, **options):
        for feed in Feed.objects.all():
            self.stdout.write(self.style.NOTICE(f"Checking {feed.feedname}..."))
            feed_status = FeedStatus(feed=feed)

            # OFFLINE
            if is_offline(feed):
                self.stdout.write(
                    self.style.WARNING(f"Feed {feed.feedname} is offline.")
                )
                feed_status.status_type = FeedStatus.StatusType.OFFLINE
                feed_status.save()

                continue

            # ERROR
            errors = get_schema_errors(feed)
            if len(errors) > 0:
                self.stdout.write(
                    self.style.WARNING(
                        f"Feed {feed.feedname} has {len(errors)} error{'s' if len(errors) > 1 else ''}."
                    )
                )
                feed_status.status_type = FeedStatus.StatusType.ERROR
                feed_status.save()
                for error in errors:
                    schema_error = SchemaError(error_status=feed_status)
                    if error.context is None or len(error.context) == 0:
                        # No sub errors
                        schema_error.schema_error_type = error.message
                        schema_error.schema_error_field = format_as_index(
                            feed.feedname, error.path
                        )
                    else:
                        # Get most relevant suberror, save that
                        best_error: ValidationError = best_match(error.context)
                        schema_error.schema_error_type = best_error.message
                        schema_error.schema_error_field = format_as_index(
                            format_as_index(feed.feedname, error.path),
                            best_error.path,
                        )
                    schema_error.save()
                continue

            # OUTDATED
            is_outdated, latest_update = outdated(feed)
            if is_outdated:
                self.stdout.write(
                    self.style.WARNING(f"Feed {feed.feedname} is outdated.")
                )
                feed_status.status_type = FeedStatus.StatusType.OUTDATED
                feed_status.save()
                OutdatedError.objects.create(
                    error_status=feed_status, update_date=latest_update
                )
                continue

            # STALE
            stale_events = stale(feed)
            if len(stale_events) > 0:
                self.stdout.write(self.style.WARNING(f"Feed {feed.feedname} is stale."))
                feed_status.status_type = FeedStatus.StatusType.STALE
                feed_status.save()
                StaleError.objects.create(
                    error_status=feed_status,
                    end_date=max(stale_events),
                    amount_events_before_end_date=len(stale_events),
                )
                continue

            # OK!
            self.stdout.write(self.style.SUCCESS(f"Feed {feed.feedname} is ok."))
            FeedStatus.objects.create(
                feed=feed,
                status_type=FeedStatus.StatusType.OK,
            )

        self.style.SUCCESS(f"Finished analyzing feeds!")
