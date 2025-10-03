import os
import re
from datetime import datetime, timedelta, timezone
from typing import Literal, Optional, TypedDict, Union
from zoneinfo import ZoneInfo

import requests
import semver
from dashboard.models import APIKey, Feed, FeedData
from django.contrib.gis.geos import Point
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError
from localflavor.us import us_states

eastern_tz = ZoneInfo("America/New_York")


class PointJSON(TypedDict):
    type: Literal["Point"]
    coordinates: tuple[float, float]


class DataHubResponse(TypedDict):
    state: str
    issuingorganization: str
    feedname: str
    url: dict[Literal["url"], str]
    format: str
    active: bool
    datafeed_frequency_update: str
    version: str
    sdate: str
    edate: Optional[str]
    needapikey: bool
    apikeyurl: Optional[dict[Union[Literal["url"], Literal["description"]], str]]
    pipedtosandbox: bool
    lastingestedtosandbox: Optional[str]
    pipedtosocrata: bool
    socratadatasetid: Optional[str]
    geocoded_column: PointJSON


def get_api_key(feed_name: str):
    try:
        api_key = APIKey.objects.get(feed__pk=feed_name).key
        in_db = True
        if not api_key:
            in_db = False
            api_key = os.environ.get(feed_name)
    except APIKey.DoesNotExist:
        api_key = os.environ.get(feed_name)
        in_db = None

    return (in_db, api_key)


# load_dotenv()
def get_feed_full_url(api_key: Union[str, None], feed_url: Union[str, None]):

    if api_key is None:
        return None

    if feed_url is None:
        return None

    new_url = "=".join(feed_url.split("=")[:-1]) + "=" + api_key

    return new_url


time_regex = re.compile(
    r"((?P<hours>\d+?)h)?((?P<minutes>\d+?)m)?((?P<seconds>\d+?)s)?"
)


def parse_time(time_str: Union[str, None]):
    if time_str is None:
        return None

    parts = time_regex.match(time_str)
    if not parts:
        return
    parts = parts.groupdict()
    time_params = {}
    for name, param in parts.items():
        if param:
            time_params[name] = int(param)
    return timedelta(**time_params)


def parse_bool(val):
    """
    Normalize typical boolean-ish values coming from the table/JSON.
    Returns True, False or None (when blank/unrecognized).
    """
    if isinstance(val, bool):
        return val
    if val is None:
        return None
    # if numeric-like
    if isinstance(val, (int, float)):
        return bool(val)
    if isinstance(val, str):
        v = val.strip().lower()
        if v in ("t", "true", "1", "yes"):
            return True
        if v in ("f", "false", "0", "no"):
            return False
        # treat empty-like as None so DB null is used for unknown
        if v == "" or v in ("null", "none", "na"):
            return None
    return None


class Command(BaseCommand):
    help = "Syncs every entry in Feed with the current feeds on https://data.transportation.gov/d/69qe-yiui/"

    def handle(self, *args, **options):
        if os.environ.get("DATAHUB_APP_TOKEN") is None:
            self.stdout.write(self.style.WARNING("No app token found for DataHub."))

        try:
            datahub_request = requests.get(
                "https://data.transportation.gov/resource/69qe-yiui.json",
                timeout=20,
                headers={
                    "X-App-Token": os.environ.get("DATAHUB_APP_TOKEN"),
                    "Accept": "application/json",
                },
            )
        except requests.exceptions.RequestException as e:
            raise CommandError(f"DataHub request failed: {e}")

        if datahub_request.status_code != requests.codes.ok:
            raise CommandError(
                f"DataHub returned invalid request status code {datahub_request.status_code}"
            )
        else:
            self.stdout.write(
                self.style.HTTP_SUCCESS(
                    "DataHub returned a valid list of feeds! Scanning now..."
                )
            )

        feeds_prior = [feed.feedname for feed in Feed.objects.all()]
        datahub_json: list[DataHubResponse] = datahub_request.json()
        for feed_requested in datahub_json:
            self.stdout.write("looking for " + str(feed_requested.get("feedname")))
            try:
                feed = Feed.objects.get(pk=feed_requested.get("feedname"))
            except Feed.DoesNotExist:
                if feed_requested.get("feedname") is None:
                    raise CommandError("Could not find feedname.")
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"New feed {feed_requested.get('feedname')} found!"
                        )
                    )
                    feed = Feed()
            try:
                state = feed_requested.get("state")
                if state is not None and state in us_states.STATES_NORMALIZED.keys():
                    feed.state = us_states.STATES_NORMALIZED[state]
                else:
                    feed.state = ""

                feed.issuingorganization = feed_requested.get("issuingorganization")
                feed.feedname = feed_requested.get("feedname")
                feed.url = (
                    feed_requested.get("url", {}).get("url", "")
                    if "url" in feed_requested
                    else ""
                )
                feed.format = feed_requested.get("format")
                feed.active = parse_bool(feed_requested.get("active")) or True
                feed.datafeed_frequency_update = parse_time(
                    feed_requested.get("datafeed_frequency_update")
                )
                feed.version = (
                    str(
                        semver.Version.parse(
                            feed_requested.get("version"), optional_minor_and_patch=True
                        )
                    )[0:3]
                    if "version" in feed_requested
                    else ""
                )

                feed.sdate = (
                    datetime.fromisoformat(feed_requested.get("sdate"))
                    .replace(tzinfo=eastern_tz)
                    .date()
                )
                feed.edate = (
                    datetime.fromisoformat(feed_requested.get("edate") or "")
                    .replace(tzinfo=eastern_tz)
                    .date()
                    if feed_requested.get("edate")
                    else None
                )
                feed.needapikey = parse_bool(feed_requested.get("needapikey")) or False
                feed.apikeyurl = (
                    (feed_requested.get("apikeyurl") or {}).get("url", "") or ""
                    if feed_requested.get("apikeyurl")
                    else None
                )
                feed.pipedtosandbox = (
                    parse_bool(feed_requested.get("pipedtosandbox")) or False
                )
                feed.lastingestedtosandbox = (
                    datetime.fromisoformat(
                        feed_requested.get("lastingestedtosandbox") or ""
                    ).replace(tzinfo=timezone.utc)
                    if feed_requested.get("lastingestedtosandbox")
                    else None
                )
                feed.pipedtosocrata = (
                    parse_bool(feed_requested.get("pipedtosocrata")) or False
                )
                feed.socratadatasetid = feed_requested.get("socratadatasetid") or ""
                feed.geocoded_column = (
                    Point(
                        feed_requested.get("geocoded_column").get("coordinates"),
                        srid=4326,
                    )
                    if feed_requested.get("geocoded_column")
                    and feed_requested.get("geocoded_column").get("coordinates")
                    else None
                )
                api_key = get_api_key(feed_requested.get("feedname"))
                if feed_requested.get("apikeyurl") and "url" in feed_requested:
                    feed_data_url = get_feed_full_url(
                        api_key[1],
                        (feed_requested.get("url").get("url")),
                    )
                else:
                    feed_data_url = feed_requested.get("url", {}).get("url", None)

                feed.save()
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(
                        f"Failed to process feed {feed_requested.get('feedname')}: {e}"
                    )
                )
                # optional: log stack trace using traceback module
                continue

            try:
                feed_data_model = feed.feeddata  # type: ignore
            except ObjectDoesNotExist:
                feed_data_model = FeedData(feed=feed)

            request_status = 0
            feed_data = dict()

            if feed_data_url is not None:
                try:
                    feed_data_request = requests.get(
                        feed_data_url, timeout=20, verify=False
                    )
                except requests.exceptions.RequestException as e:
                    self.stdout.write(
                        self.style.HTTP_BAD_REQUEST(
                            f"Feed {feed_requested.get('feedname')} request failed: {e}"
                        )
                    )
                else:
                    request_status = feed_data_request.status_code
                    if feed_data_request.status_code != requests.codes.ok:
                        self.stdout.write(
                            self.style.HTTP_BAD_REQUEST(
                                f"Feed {feed_requested.get('feedname')} returned invalid request status code ({feed_data_request.status_code}): {feed_data_request.url}"
                            )
                        )
                    else:
                        try:
                            feed_data = feed_data_request.json()
                        except ValueError:
                            self.stdout.write(
                                self.style.ERROR(
                                    f"Feed {feed_requested.get('feedname')} was unable to be converted to JSON."
                                )
                            )

            feed_data_model.response_code = request_status
            feed_data_model.feed_data = feed_data
            feed_data_model.save()

            if feed_requested.get("needapikey") and api_key[0] is None:
                self.stdout.write(
                    self.style.WARNING(
                        f"No API key for {feed_requested.get('feedname')} found in database."
                    )
                )
                APIKey.objects.create(feed=feed, key=(api_key[1] or ""))
            elif feed_requested.get("needapikey") and not api_key[0] and api_key[1]:
                self.stdout.write(
                    self.style.WARNING(
                        f"No API key for {feed_requested.get('feedname')} found in database, adding from environment."
                    )
                )
                api_key_object = APIKey.objects.get(feed=feed)
                api_key_object.key = api_key[1]
                api_key_object.save()

            try:
                feeds_prior.remove(feed_requested.get("feedname"))
            except ValueError:
                pass

        # Remove all feeds not updated
        for feed_not_found in feeds_prior:
            try:
                feed_to_delete = Feed.objects.get(pk=feed_not_found)
            except Feed.DoesNotExist:
                raise CommandError(
                    f"Tried to delete feed {feed_not_found} that does not exist"
                )

            feed_to_delete.delete()
            self.stdout.write(self.style.WARNING(f"Feed {feed_not_found} deleted."))

        self.stdout.write(
            self.style.SUCCESS("Successfully synced feed list with DataHub!")
        )
