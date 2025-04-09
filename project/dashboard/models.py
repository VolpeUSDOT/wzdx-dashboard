import requests
from django.contrib.gis.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from localflavor.us import models as us_models, us_states

# Create your models here.


class Feed(models.Model):
    """
    A model representing the information available at https://data.transportation.gov/d/69qe-yiui/.

    To be updated regularly via crontab or with management command syncdatahub.

    Feed statuses stored in :model:`dashboard.FeedStatus`. If API key is needed, stored in :model:`dashboard.APIKey`.
    """

    # The following fields are all from the public data hub, https://data.transportation.gov/d/69qe-yiui
    state = us_models.USStateField(_("State"), blank=True, default="")
    issuingorganization = models.CharField(_("Issuing Organization"), max_length=150)
    feedname = models.CharField(_("Feed Name"), primary_key=True, max_length=150)
    url = models.URLField(
        "URL",
    )
    format = models.CharField(_("Format"), max_length=150)
    active = models.BooleanField(
        "Active",
    )
    datafeed_frequency_update = models.DurationField(
        _("Datafeed Update Frequency"),
        null=True,
    )
    version = models.CharField(_("Version"), max_length=150)
    sdate = models.DateField(
        "Start Date",
    )
    edate = models.DateField(
        _("End Date"),
        null=True,
    )
    needapikey = models.BooleanField(_("Need API Key"), default=False)
    apikeyurl = models.URLField(
        "API Key URL",
        null=True,
    )
    pipedtosandbox = models.BooleanField(
        _("Piped to Sandbox"),
    )
    lastingestedtosandbox = models.DateTimeField(
        _("Last Ingested To Sandbox (UTC)"),
        null=True,
    )
    pipedtosocrata = models.BooleanField(
        _("Piped to Socrata"),
    )
    socratadatasetid = models.CharField(
        _("Socrata Dataset ID"), blank=True, max_length=150
    )
    geocoded_column = models.PointField(
        _("State Coordinate"),
        null=True,
    )

    class Meta:
        ordering = ["state"]
        verbose_name_plural = _("feeds")

    def __str__(self):
        return f"{f'{self.state} - ' if self.state else ''}{self.issuingorganization}"

    def work_zone_events(self):
        """
        Returns all features that are classified as work zones (if feed status is OK).
        """

        feed_status = self.feed_status()
        if feed_status is None or feed_status.status_type != FeedStatus.StatusType.OK:
            return []

        feed_data = self.feed_data() or {}

        if not feed_data:
            return []

        features = feed_data.get("features", [])

        if not features:
            return features

        if self.version.startswith("3"):
            events = [
                feature
                for feature in features
                if feature.get("properties", {}).get("event_type", "") == "work-zone"
            ]
        elif self.version.startswith("4"):
            events = [
                feature
                for feature in features
                if feature.get("properties", {})
                .get("core_details", {})
                .get("event_type", "")
                == "work-zone"
            ]
        else:
            events = []

        return events

    def feed_status(self):
        """
        Returns most up-to-date feed status from :model:`dashboard.FeedStatus`.
        """
        status = FeedStatus.objects.filter(feed=self.pk).first()

        if status is None:
            return None

        if status.status_type == status.StatusType.OK:
            return status.okstatus  # type: ignore

        if status.status_type == status.StatusType.ERROR:
            return status.schemaerrorstatus  # type: ignore

        if status.status_type == status.StatusType.OUTDATED:
            return status.outdatederrorstatus  # type: ignore

        if status.status_type == status.StatusType.STALE:
            return status.staleerrorstatus  # type: ignore

        if status.status_type == status.StatusType.OFFLINE:
            return status.offlineerrorstatus  # type: ignore

        return None

    def status_type(self):
        feed_status = self.feed_status()

        if feed_status:
            return feed_status.status_type

    def feed_data(self):
        try:
            feed_data = self.feeddata  # type: ignore
            return feed_data.feed_data
        except ObjectDoesNotExist:
            return None

    def response_code(self):
        try:
            feed_data = self.feeddata  # type: ignore
            return feed_data.response_code
        except ObjectDoesNotExist:
            return None

    def last_checked(self):
        try:
            feed_data = self.feeddata  # type: ignore
            return feed_data.last_checked
        except ObjectDoesNotExist:
            return None

    def state_name(self):
        state_tuple = us_states.STATE_CHOICES

        try:
            state_index = list(zip(*state_tuple))[0].index(self.state)
        except ValueError:
            return None

        return state_tuple[state_index][1]

    def get_absolute_url(self):
        return reverse("feed-detail", kwargs={"pk": self.feedname})


class FeedData(models.Model):
    """Contains :model:`dashboard.Feed` JSON data, and other response information. In it's own model to not pull in all data whenever requesting feed information."""

    feed = models.OneToOneField(
        Feed,
        on_delete=models.CASCADE,
        primary_key=True,
    )
    response_code = models.IntegerField(_("HTML Response Code"), default=0)
    last_checked = models.DateTimeField(
        _("Last Updated"),
        auto_now=True,
    )
    feed_data = models.JSONField(
        _("Feed Data"),
        default=dict,
    )


class FeedStatus(models.Model):
    """Base class for status of feed in :model:`dashboard.Feed`. To be inherited by schema, outdated, stale, etc. errors."""

    class StatusType(models.TextChoices):
        NULL = "NA", ("null")
        OK = "OK", _("ok")
        ERROR = "ER", _("error")
        OUTDATED = "OU", _("outdated")
        STALE = "ST", _("stale")
        OFFLINE = "OF", _("offline")

    feed = models.ForeignKey(
        Feed,
        on_delete=models.CASCADE,
    )

    status_type = models.CharField(
        max_length=2,
        choices=StatusType.choices,
        default=StatusType.NULL,
    )

    datetime_checked = models.DateTimeField(
        auto_now_add=True,
    )

    status_since = models.DateTimeField(auto_now_add=True)

    notif_sent = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.feed.feedname}: {self.StatusType(self.status_type).label} {self.datetime_checked}"

    def is_error(self):
        return self.status_type in {
            self.StatusType.ERROR,
            self.StatusType.OUTDATED,
            self.StatusType.STALE,
            self.StatusType.OFFLINE,
        }

    def details(self):
        """Base function for feed status details. Should be overridden by subclasses."""
        return "No details available."

    class Meta:
        ordering = ["-datetime_checked"]
        verbose_name_plural = _("feed statuses")


class OKStatus(FeedStatus):
    """
    Represents a :model:`dashboard.FeedStatus` for a feed without errors.
    """

    def __init__(self, *args, **kwargs):
        super(OKStatus, self).__init__(*args, **kwargs)
        self.status_type = FeedStatus.StatusType.OK

    def details(self):
        """Returns a string with detailed status. In this case, details how many work zone events are present"""
        events = self.feed.work_zone_events()
        return f"All good! {len(events)} work zone events."


class SchemaErrorStatus(FeedStatus):
    """
    Represents a :model:`dashboard.FeedStatus` for a feed with schema errors.
    """

    def __init__(self, *args, **kwargs):
        super(SchemaErrorStatus, self).__init__(*args, **kwargs)
        self.status_type = FeedStatus.StatusType.ERROR

    most_common_type = models.TextField(_("Most Common Schema Error Type"), blank=True)
    most_common_field = models.TextField(
        _("Most Common Schema Error Field"), blank=True
    )

    most_common_count = models.IntegerField(_("Occurences of Most Common Error"))
    total_errors = models.IntegerField(_("Total Schema Errors"))

    def details(self):
        """Returns a string with detailed status. In this case, details most common error and how many are present."""

        most_common_error = (
            self.most_common_type or "Most common error cannot be determined"
        )

        other_errors = self.total_errors - self.most_common_count

        return f"{self.most_common_count} schema error{'s' if self.most_common_count != 1 else ''} detected: {most_common_error}.{(' There ' + ('are ' if other_errors != 1 else 'is ') + str(other_errors) + ' other error' + ('s' if other_errors != 1 else '') + '.') if other_errors > 0 else ''}"


class OutdatedErrorStatus(FeedStatus):
    """
    Represents a :model:`dashboard.FeedStatus` for a feed that has not been updated in over 14 days.
    """

    def __init__(self, *args, **kwargs):
        super(OutdatedErrorStatus, self).__init__(*args, **kwargs)
        self.status_type = FeedStatus.StatusType.OUTDATED

    update_date = models.DateTimeField(_("Outdated Update Date"))

    def details(self):
        """Returns a string with detailed status. In this case, details last time event data was updated."""
        return f"Event data last updated: {self.update_date.strftime('%m/%d/%Y')}"

    class Meta:
        ordering = ["-update_date"]
        verbose_name_plural = _("outdated errors")


class StaleErrorStatus(FeedStatus):
    """
    Represents a :model:`dashboard.FeedStatus` for a feed that has events which ended over 14 days ago.
    """

    def __init__(self, *args, **kwargs):
        super(StaleErrorStatus, self).__init__(*args, **kwargs)
        self.status_type = FeedStatus.StatusType.STALE

    latest_end_date = models.DateTimeField(_("Stale End Date"))
    amount_events_before_end_date = models.PositiveIntegerField(
        _("Stale Events"), default=0
    )

    class Meta:
        ordering = ["-latest_end_date"]
        verbose_name_plural = _("stale errors")

    def details(self):
        """Returns a string with detailed status. In this case, details how many events have ended over 14 days ago."""
        return (
            f"{self.amount_events_before_end_date} events have ended over 14 days ago."
        )


class OfflineErrorStatus(FeedStatus):
    """
    Represents a :model:`dashboard.FeedStatus` for a feed that was unable to be reached at its URL.
    """

    def __init__(self, *args, **kwargs):
        super(OfflineErrorStatus, self).__init__(*args, **kwargs)
        self.status_type = FeedStatus.StatusType.OFFLINE

    def details(self):
        """Returns a string with detailed status. Rather than storing information twice, uses stored feed data to generate message."""

        if self.feed.url is None or self.feed.url == "" or not self.feed.active:
            return "Feed is not active."

        response_code, json_data = self.feed.response_code(), self.feed.feed_data()

        if response_code == 0:
            return "Feed is unreachable at URL due to request error."

        if response_code != requests.codes.ok:
            return f"Feed is unreachable at URL due to HTTP status code {response_code}"

        if not bool(json_data):
            return "Feed is unreachable at URL due to JSON decode error."

        return "Feed unreachable at URL."


class APIKey(models.Model):
    """
    API keys for various feeds. Any feed where DataHub says a key is needed is added automatically.
    """

    feed = models.OneToOneField(Feed, on_delete=models.CASCADE, primary_key=True)
    key = models.TextField(default="")

    def __str__(self):
        return f"{self.feed.feedname.upper()}={self.key}"

    class Meta:
        verbose_name_plural = _("API keys")
