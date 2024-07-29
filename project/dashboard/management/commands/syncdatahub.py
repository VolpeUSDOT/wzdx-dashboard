import os
import re
from datetime import datetime, timedelta, timezone
from typing import Literal, Optional, TypedDict, Union

import requests
from dashboard.models import APIKey, Feed
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand, CommandError


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
    except APIKey.DoesNotExist:
        api_key = os.environ.get(feed_name)
        in_db = False

    return (in_db, api_key)


# load_dotenv()
def get_feed_full_url(api_key: Union[str, None], feed_url: Union[str, None]):

    if api_key is None:
        return None

    if feed_url is None:
        return None

    new_url = "=".join(feed_url.split("=")[:-1]) + "=" + api_key

    return new_url


regex = re.compile(r"((?P<hours>\d+?)h)?((?P<minutes>\d+?)m)?((?P<seconds>\d+?)s)?")


def parse_time(time_str: Union[str, None]):
    if time_str is None:
        return None

    parts = regex.match(time_str)
    if not parts:
        return
    parts = parts.groupdict()
    time_params = {}
    for name, param in parts.items():
        if param:
            time_params[name] = int(param)
    return timedelta(**time_params)


class Command(BaseCommand):
    help = "Syncs every entry in Feed with the current feeds on https://data.transportation.gov/d/69qe-yiui/"

    def handle(self, *args, **options):

        try:
            datahub_request = requests.get(
                "https://data.transportation.gov/resource/69qe-yiui.json", timeout=20
            )
        except requests.exceptions.RequestException as e:
            raise CommandError(f"DataHub request failed: {e}")

        if datahub_request.status_code != requests.codes.ok:
            raise CommandError(
                f"DataHub returned invalid request status code {datahub_request.status_code}"
            )

        feeds_prior = [feed.feedname for feed in Feed.objects.all()]
        datahub_json: list[DataHubResponse] = datahub_request.json()
        for feed_requested in datahub_json:
            try:
                feed = Feed.objects.get(pk=feed_requested.get("feedname"))
            except Feed.DoesNotExist:
                if feed_requested.get("feedname") is None:
                    raise CommandError("Could not find feedname.")
                else:
                    self.stdout.write(
                        self.style.NOTICE(
                            f"New feed {feed_requested.get('feedname')} found!"
                        )
                    )
                    feed = Feed()

            feed.state = feed_requested.get("state")
            feed.issuingorganization = feed_requested.get("issuingorganization")
            feed.feedname = feed_requested.get("feedname")
            feed.url = feed_requested.get("url").get("url", "")
            feed.format = feed_requested.get("format")
            feed.active = feed_requested.get("active")
            feed.datafeed_frequency_update = parse_time(
                feed_requested.get("datafeed_frequency_update")
            )
            feed.version = feed_requested.get("version")
            feed.sdate = datetime.fromisoformat(feed_requested.get("sdate"))
            feed.edate = (
                datetime.fromisoformat(feed_requested.get("edate") or "")
                if feed_requested.get("edate")
                else None
            )
            feed.needapikey = feed_requested.get("needapikey")
            feed.apikeyurl = (
                (feed_requested.get("apikeyurl") or {}).get("url", "") or ""
                if feed_requested.get("apikeyurl")
                else None
            )
            feed.pipedtosandbox = feed_requested.get("pipedtosandbox")
            feed.lastingestedtosandbox = (
                datetime.fromisoformat(
                    feed_requested.get("lastingestedtosandbox") or ""
                ).replace(tzinfo=timezone.utc)
                if feed_requested.get("lastingestedtosandbox")
                else None
            )
            feed.pipedtosocrata = feed_requested.get("pipedtosocrata")
            feed.socratadatasetid = feed_requested.get("socratadatasetid") or ""
            feed.geocoded_column = (
                Point(
                    feed_requested.get("geocoded_column").get("coordinates"), srid=4326
                )
                if feed_requested.get("geocoded_column")
                and feed_requested.get("geocoded_column").get("coordinates")
                else None
            )
            api_key = get_api_key(feed_requested.get("feedname"))
            if feed_requested.get("apikeyurl"):
                feed_data_url = get_feed_full_url(
                    api_key[1],
                    (feed_requested.get("url").get("url")),
                )
            else:
                feed_data_url = feed_requested.get("url").get("url")

            if feed_data_url is None:
                self.stdout.write(
                    self.style.WARNING(
                        f"Could not find feed {feed_requested.get('feedname')} API key, skipping"
                    )
                )
                continue

            try:
                feed_data_request = requests.get(feed_data_url, timeout=20)
            except requests.exceptions.RequestException as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Feed {feed_requested.get('feedname')} request failed: {e}"
                    )
                )
                continue

            if feed_data_request.status_code != requests.codes.ok:
                self.stdout.write(
                    self.style.ERROR(
                        f"Feed {feed_requested.get('feedname')} returned invalid request status code: {feed_data_request.url}"
                    )
                )
                continue

            feed.feed_data = feed_data_request.json()

            feed.save()

            if feed_requested.get("needapikey") and not api_key[0]:
                self.stdout.write(
                    self.style.WARNING(
                        f"No API key for {feed_requested.get('feedname')} found in database."
                    )
                )
                APIKey.objects.create(
                    feed=feed, key=(api_key[1] if api_key[1] is not None else "")
                )

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
