from collections import Counter
from datetime import datetime, timedelta, timezone

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
from shared.schema_check import (
    find_all_instances_key,
    get_formatted_errors,
    get_version_schema_errors,
)

# FEED CHECKER FUNCTIONS


def is_offline(feed: Feed) -> bool:
    """Checks if feed response code was 200 and that JSON data was written."""

    if feed.url is None or feed.url == "":
        return True

    if not feed.active:
        return True

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


def get_feed_schema_errors(feed: Feed):
    feed_data = feed.feed_data()
    feed_version = feed.version

    return get_version_schema_errors(feed_data, feed_version)


def outdated(feed: Feed):
    """If feed events haven't been updated in the last 14 days. Assumes feed matches the schema."""
    fourteen_days_ago = datetime.now(tz=timezone.utc) - timedelta(days=14)

    # Recursively get all instances of "update_date"
    all_update_dates = [
        iso8601.parse_date(update_date_string, default_timezone=timezone.utc)
        for update_date_string in find_all_instances_key(
            feed.feed_data(), "update_date"  # type: ignore
        )
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
            self.stdout.write(self.style.NOTICE(f"At URL {feed.url}..."))
            previous_status = feed.feed_status()

            # OFFLINE
            if is_offline(feed):
                self.stdout.write(
                    self.style.WARNING(f"Feed {feed.feedname} is offline.")
                )
                feed_status = OfflineErrorStatus.objects.create(feed=feed)

            else:
                # ERROR
                errors = get_feed_schema_errors(feed)
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

        self.style.SUCCESS("Finished analyzing feeds!")
