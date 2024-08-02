from datetime import datetime
from time import timezone

from django.contrib.gis.db import models
from django.contrib.gis.db.models import Count
from django.db import models as normal_models
from django.utils.translation import gettext_lazy as _
from model_utils.managers import InheritanceManager

# Create your models here.


class Feed(models.Model):
    """
    A model representing the information available at https://data.transportation.gov/d/69qe-yiui/. To be updated regularly via crontab.
    """

    # The following fields are all from the public data hub, https://data.transportation.gov/d/69qe-yiui
    state = models.CharField(_("State"), max_length=150)
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

    # The following fields are needed for data processing
    last_checked = models.DateTimeField(
        _("Last Updated"),
        auto_now=True,
    )
    feed_data = models.JSONField(
        _("Feed Data"),
        default=dict,
    )

    class Meta:
        ordering = ["sdate"]
        verbose_name_plural = _("feeds")

    def __str__(self):
        return self.issuingorganization

    @property
    def work_zone_events(self):
        features = self.feed_data["features"]
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

    @property
    def feed_status(self):
        status = FeedStatus.objects.filter(feed=self).first()

        if status is None:
            return None

        if hasattr(status, "okstatus") and type(status.okstatus) is OKStatus:  # type: ignore
            return status.okstatus  # type: ignore

        if (
            hasattr(status, "schemaerrorstatus")
            and type(status.schemaerrorstatus) is SchemaErrorStatus  # type: ignore
        ):
            return status.schemaerrorstatus  # type: ignore

        if (
            hasattr(status, "outdatederrorstatus")
            and type(status.outdatederrorstatus) is OutdatedErrorStatus  # type: ignore
        ):
            return status.outdatederrorstatus  # type: ignore

        if (
            hasattr(status, "staleerrorstatus")
            and type(status.staleerrorstatus) is StaleErrorStatus  # type: ignore
        ):
            return status.staleerrorstatus  # type: ignore

        if (
            hasattr(status, "offlineerrorstatus")
            and type(status.offlineerrorstatus) is OfflineErrorStatus  # type: ignore
        ):
            return status.offlineerrorstatus  # type: ignore

        return None


class FeedStatus(models.Model):
    """Base class for Feed Errors. To be inherited by schema, outdated, stale, etc errors."""

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

    @property
    def is_error(self):
        return self.status_type in {
            self.StatusType.ERROR,
            self.StatusType.OUTDATED,
            self.StatusType.STALE,
            self.StatusType.OFFLINE,
        }

    @property
    def details(self):
        return "No details available."

    class Meta:
        ordering = ["-datetime_checked"]
        verbose_name_plural = _("feed statuses")


class OKStatus(FeedStatus):
    def __init__(self, *args, **kwargs):
        super(OKStatus, self).__init__(*args, **kwargs)
        self.status_type = FeedStatus.StatusType.OK

    def details(self):
        events = self.feed.work_zone_events
        return f"All good! {len(events)} work zone events."


class SchemaErrorStatus(FeedStatus):
    def __init__(self, *args, **kwargs):
        super(SchemaErrorStatus, self).__init__(*args, **kwargs)
        self.status_type = FeedStatus.StatusType.ERROR

    @property
    def most_common_validation_error(self):
        return (
            SchemaValidationError.objects.filter(error_status=self)
            .annotate(count=Count("error_type"))
            .order_by("-count")
            .first()
        )

    @property
    def details(self):
        most_common_error = self.most_common_validation_error

        if most_common_error is None:
            return "No errors were found."

        most_common_error_count = SchemaValidationError.objects.filter(
            error_status=self, error_type=most_common_error.error_type
        ).count()

        total_schema_errors = SchemaValidationError.objects.filter(
            error_status=self
        ).count()
        other_errors = total_schema_errors - most_common_error_count

        return f"{most_common_error_count} event{'s' if most_common_error_count != 1 else ''} {'have' if most_common_error_count != 1 else 'has'} the following error: {most_common_error.error_type}. There {'are' if other_errors != 1 else 'is'} {other_errors if other_errors != 0 else 'no'} other error{'s' if other_errors != 1 else ''}."


class SchemaValidationError(models.Model):
    error_status = models.ForeignKey(
        SchemaErrorStatus,
        on_delete=models.CASCADE,
    )
    error_type = models.TextField(_("Schema Error Type"), blank=True)
    error_field = models.TextField(_("Schema Error Field"), blank=True)

    def __str__(self):
        return f"{self.error_type} at {self.error_field}"

    class Meta:
        verbose_name_plural = _("schema status")


class OutdatedErrorStatus(FeedStatus):
    def __init__(self, *args, **kwargs):
        super(OutdatedErrorStatus, self).__init__(*args, **kwargs)
        self.status_type = FeedStatus.StatusType.OUTDATED

    update_date = models.DateTimeField(_("Outdated Update Date"))

    @property
    def details(self):
        return f"Event data last updated: {self.update_date.date().strftime('%x')}"

    class Meta:
        ordering = ["-update_date"]
        verbose_name_plural = _("outdated errors")


class StaleErrorStatus(FeedStatus):
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

    @property
    def details(self):
        return (
            f"{self.amount_events_before_end_date} events have ended over 14 days ago."
        )


class OfflineErrorStatus(FeedStatus):
    def __init__(self, *args, **kwargs):
        super(OfflineErrorStatus, self).__init__(*args, **kwargs)
        self.status_type = FeedStatus.StatusType.OFFLINE

    @property
    def details(self):
        return "Feed unreachable at URL."


class APIKey(models.Model):
    feed = models.OneToOneField(Feed, on_delete=models.CASCADE, primary_key=True)
    key = models.TextField(default="")

    def __str__(self):
        return f"{self.feed.feedname.upper()}={self.key}"

    class Meta:
        verbose_name_plural = _("API keys")
