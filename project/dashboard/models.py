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
    def status(self):
        try:
            return FeedStatus.objects.filter(feed=self)[0].status_type
        except FeedStatus.DoesNotExist:
            return ""

    @property
    def status_last_checked(self):
        return FeedStatus.objects.filter(feed=self)[0].datetime_checked

    @property
    def status_details(self):
        try:
            return FeedStatus.objects.filter(feed=self)[0].details
        except FeedStatus.DoesNotExist:
            return ""


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

    def is_error(self):
        return self.status_type in {
            self.StatusType.ERROR,
            self.StatusType.OUTDATED,
            self.StatusType.STALE,
            self.StatusType.OFFLINE,
        }

    def __str__(self):
        return f"{self.feed.feedname}: {self.StatusType(self.status_type).label} {self.datetime_checked}"

    @property
    def details(self):
        """Detailed status..."""
        if self.status_type == self.StatusType.OK:
            return "All good!"
        elif self.status_type == self.StatusType.ERROR:
            most_common_error = (
                SchemaError.objects.filter(error_status=self)
                .annotate(
                    count=Count("schema_error_type", output_field=models.IntegerField())
                )
                .order_by("-count")[0]
                .schema_error_type
            )
            schema_error_count = SchemaError.objects.filter(
                schema_error_type=most_common_error
            ).count()
            return f"Schema error detected! The most common error is: {most_common_error}. This error appeared {schema_error_count} time{'s' if schema_error_count > 1 else ''}."  # type: ignore
        elif self.status_type == self.StatusType.OUTDATED:
            return f"Event data last updated: {humanize.naturaldate(OutdatedError.objects.filter(error_status=self)[0].update_date)}"
        elif self.status_type == self.StatusType.STALE:
            stale_error = StaleError.objects.filter(error_status=self)[0]
            return f" {stale_error.amount_events_before_end_date} events have ended over 14 days ago."
        elif self.status_type == self.StatusType.OFFLINE:
            return "Feed unreachable at URL"
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
    schema_error_type = models.CharField(_("Schema Error Type"), max_length=150)
    schema_error_field = models.CharField(_("Schema Error Field"), max_length=150)

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
