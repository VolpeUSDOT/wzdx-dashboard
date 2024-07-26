import os
from typing import Union

import requests
from dashboard.models import APIKey, Feed
from django.core.management.base import BaseCommand, CommandError


# load_dotenv()
def get_feed_full_url(feed_name: str, feed_url: Union[str, None]):

    try:
        api_key = APIKey.objects.get(pk=feed_name)
    except APIKey.DoesNotExist:
        return None

    if feed_url is None:
        return None

    new_url = "=".join(feed_url.split("=")[:-1]) + "=" + api_key.key

    return new_url


class Command(BaseCommand):
    help = "Syncs every entry in Feed with the current feeds on https://data.transportation.gov/d/69qe-yiui/"

    def handle(self, *args, **options):

        try:
            datahub_request = requests.get(
                "https://data.transportation.gov/resource/69qe-yiui.json"
            )
        except requests.exceptions.RequestException as e:
            raise CommandError(f"DataHub request failed: {e}")

        if datahub_request.status_code != requests.codes.ok:
            raise CommandError(
                f"DataHub returned invalid request status code {datahub_request.status_code}"
            )

        feeds_prior = [feed.feedname for feed in Feed.objects.all()]
        datahub_json = datahub_request.json()
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
            feed.url = feed_requested.get("url").get("url")
            feed.format = feed_requested.get("format")
            feed.active = feed_requested.get("active")
            feed.datafeed_frequency_update = feed_requested.get(
                "datafeed_frequency_update"
            )
            feed.version = feed_requested.get("version")
            feed.sdate = feed_requested.get("sdate")
            feed.edate = feed_requested.get("edate")
            feed.needapikey = feed_requested.get("needapikey")
            feed.apikeyurl = (
                feed_requested.get("apikeyurl").get("url")
                if feed_requested.get("apikeyurl")
                else None
            )
            feed.pipedtosandbox = feed_requested.get("pipedtosandbox")
            feed.lastingestedtosandbox = feed_requested.get("lastingestedtosandbox")
            feed.pipedtosocrata = feed_requested.get("pipedtosocrata")
            feed.socratadatasetid = feed_requested.get("socratadatasetid", "")
            feed.geocoded_column = feed_requested.get("geocoded_column")

            if feed_requested.get("apikeyurl"):
                feed_data_url = get_feed_full_url(
                    feed_requested.get("feedname"),
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
                feed_data_request = requests.get(feed_data_url)
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

            try:
                feeds_prior.remove(feed.issuingorganization)
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

        self.stdout.write(
            self.style.SUCCESS("Successfully synced feed list with DataHub!")
        )
