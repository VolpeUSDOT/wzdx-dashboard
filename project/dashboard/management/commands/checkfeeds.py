import json
import os
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional, Sequence

import iso8601
import requests
from dashboard.models import (
    Feed,
    OfflineErrorStatus,
    OKStatus,
    OutdatedErrorStatus,
    SchemaErrorStatus,
    StaleErrorStatus,
)
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


def get_formatted_errors(errors: list[ValidationError], feedname: str):
    error_list: list[tuple[str, str]] = []

    for error in errors:
        if error.context is None or len(error.context) == 0:
            # No sub errors
            error_list.append((error.message, format_as_index(feedname, error.path)))
        else:
            # Get most relevant suberror, save that
            best_error: ValidationError = best_match(error.context)
            if type(best_error) is ValidationError:
                error_list.append(
                    (
                        best_error.message,
                        format_as_index(
                            format_as_index(feedname, error.path),
                            best_error.path,
                        ),
                    )
                )

    return error_list


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
    """Checks if feed response code was 200 and that JSON data was written."""

    response_code = feed.response_code()

    if response_code is None:
        return True

    feed_data = feed.feed_data()

    if feed_data is None:
        return True

    return (
        (response_code == 0)
        or (response_code != requests.codes.ok)
        or (not bool(feed_data))
    )


def get_schema_errors(feed: Feed):
    """If feed fails to validate against JSON schema"""
    feed_data = feed.feed_data()
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
        for update_date_string in find_all_instances_key(feed.feed_data(), "update_date")  # type: ignore
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
        for end_date_string in find_all_instances_key(feed.feed_data(), "end_date")  # type: ignore
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
            previous_status = feed.feed_status()

            # OFFLINE
            if is_offline(feed):
                self.stdout.write(
                    self.style.WARNING(f"Feed {feed.feedname} is offline.")
                )
                feed_status = OfflineErrorStatus.objects.create(feed=feed)

            else:
                # ERROR
                errors = get_schema_errors(feed)
                if len(errors) > 0:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Feed {feed.feedname} has {len(errors)} error{'s' if len(errors) > 1 else ''}."
                        )
                    )
                    formatted_errors = get_formatted_errors(errors, feed.feedname)
                    feed_error_messages: tuple[list[str], list[str]] = list(zip(*formatted_errors))  # type: ignore

                    most_common_type, most_common_count = Counter(
                        feed_error_messages[0]
                    ).most_common(1)[0]
                    most_common_field = feed_error_messages[1][
                        feed_error_messages[0].index(most_common_type)
                    ]

                    feed_status = SchemaErrorStatus.objects.create(
                        feed=feed,
                        most_common_type=most_common_type,
                        most_common_field=most_common_field,
                        most_common_count=most_common_count,
                        total_errors=len(errors),
                    )

                else:
                    # OUTDATED
                    is_outdated, latest_update = outdated(feed)
                    if is_outdated:
                        self.stdout.write(
                            self.style.WARNING(f"Feed {feed.feedname} is outdated.")
                        )
                        feed_status = OutdatedErrorStatus.objects.create(
                            feed=feed, update_date=latest_update
                        )
                    else:
                        # STALE
                        stale_events = stale(feed)
                        if len(stale_events) > 0:
                            self.stdout.write(
                                self.style.WARNING(f"Feed {feed.feedname} is stale.")
                            )
                            feed_status = StaleErrorStatus.objects.create(
                                feed=feed,
                                end_date=max(stale_events),
                                amount_events_before_end_date=len(stale_events),
                            )
                        else:
                            # OK!
                            self.stdout.write(
                                self.style.SUCCESS(f"Feed {feed.feedname} is ok.")
                            )
                            feed_status = OKStatus.objects.create(feed=feed)

            if (
                previous_status is not None
                and previous_status.status_type == feed_status.status_type
            ):
                feed_status.status_since = previous_status.status_since
                feed_status.save()

        self.style.SUCCESS(f"Finished analyzing feeds!")
