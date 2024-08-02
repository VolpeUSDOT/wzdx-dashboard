import humanize
from django.contrib.gis.db import models
from django.contrib.gis.db.models import Count
from django.utils.translation import gettext_lazy as _

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
    def status(self):
        status = FeedStatus.objects.filter(feed=self).first()

        if status is None:
            return ""

        return status.status_type

    @property
    def status_last_checked(self):
        status = FeedStatus.objects.filter(feed=self).first()

        if status is None:
            return ""

        return status.datetime_checked

    @property
    def status_details(self):
        status = FeedStatus.objects.filter(feed=self).first()

        if status is None:
            return ""

        return status.details


class FeedStatus(models.Model):
    feed = models.ForeignKey(
        Feed,
        on_delete=models.CASCADE,
    )

    class StatusType(models.TextChoices):
        OK = "OK", _("ok")
        ERROR = "ER", _("error")
        OUTDATED = "OU", _("outdated")
        STALE = "ST", _("stale")
        OFFLINE = "OF", _("offline")

    status_type = models.CharField(
        max_length=2,
        choices=StatusType.choices,
        default=StatusType.OK,
    )

    datetime_checked = models.DateTimeField(
        auto_now_add=True,
    )

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
        """Detailed status..."""
        if self.status_type == self.StatusType.OK:
            events = self.feed.work_zone_events
            return f"All good! {len(events)} work zone events."
        elif self.status_type == self.StatusType.ERROR:
            most_common_error = (
                SchemaError.objects.filter(error_status=self)
                .annotate(
                    count=Count("schema_error_type", output_field=models.IntegerField())
                )
                .order_by("-count")
                .first()
            )
            if most_common_error is None:
                return "No errors were found."
            most_common_error_count = SchemaError.objects.filter(
                error_status=self, schema_error_type=most_common_error.schema_error_type
            ).count()
            total_schema_errors = SchemaError.objects.filter(error_status=self).count()
            other_errors = total_schema_errors - most_common_error_count
            return f"{most_common_error_count} event{'s' if most_common_error_count != 1 else ''} {'have' if most_common_error_count != 1 else 'has'} the following error: {most_common_error.schema_error_type}. There {'are' if other_errors != 1 else 'is'} {other_errors} other error{'s' if other_errors != 1 else ''}."
        elif self.status_type == self.StatusType.OUTDATED:
            outdated_error = OutdatedError.objects.filter(error_status=self).first()
            if outdated_error is None:
                return "Feed is not outdated."
            return f"Event data last updated: {outdated_error.update_date.date().strftime('%x')}"
        elif self.status_type == self.StatusType.STALE:
            stale_error = StaleError.objects.filter(error_status=self).first()
            if stale_error is None:
                return "Feed is not stale."
            return f"{stale_error.amount_events_before_end_date} events have ended over 14 days ago."
        elif self.status_type == self.StatusType.OFFLINE:
            return "Feed unreachable at URL."
        return ""

    class Meta:
        ordering = ["-datetime_checked"]
        verbose_name_plural = _("feed statuses")


class FeedError(models.Model):
    """Base class for Feed Errors. To be inherited by schema, outdated, stale, etc errors."""

    error_status = models.ForeignKey(
        FeedStatus,
        on_delete=models.CASCADE,
    )

    class Meta:
        abstract = True


class SchemaError(FeedError):
    schema_error_type = models.TextField(_("Schema Error Type"), blank=True)
    schema_error_field = models.TextField(_("Schema Error Field"), blank=True)

    class Meta:
        verbose_name_plural = _("schema errors")


class OutdatedError(FeedError):
    update_date = models.DateTimeField(_("Outdated Update Date"))

    class Meta:
        ordering = ["-update_date"]
        verbose_name_plural = _("outdated errors")


class StaleError(FeedError):
    latest_end_date = models.DateTimeField(_("Stale End Date"))
    amount_events_before_end_date = models.PositiveIntegerField(
        _("Stale Events"), default=0
    )

    class Meta:
        ordering = ["-latest_end_date"]
        verbose_name_plural = _("stale errors")


class APIKey(models.Model):
    feed = models.OneToOneField(Feed, on_delete=models.CASCADE, primary_key=True)
    key = models.TextField(default="")

    def __str__(self):
        return f"{self.feed.feedname.upper()}={self.key}"

    class Meta:
        verbose_name_plural = _("API keys")
