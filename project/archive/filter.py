from archive.models import Archive
from dashboard.models import Feed
from django.forms import Select
from django_filters import DateFromToRangeFilter, FilterSet, ModelChoiceFilter

FEED_CHOICES = [("", "Find a feed!")] + [
    (feedname, f"{state + ' - ' if state else ''}{issuingorganization}")
    for (feedname, state, issuingorganization) in Feed.objects.values_list(
        "feedname", "state", "issuingorganization"
    )
]


class ArchiveFilter(FilterSet):
    feed = ModelChoiceFilter(
        field_name="feed",
        queryset=Feed.objects.all(),
        widget=Select(attrs={"class": "usa-select", "name": "feed"}),
    )

    datetime_archived = DateFromToRangeFilter(
        field_name="datetime_archived", label="Date/Time Archived"
    )

    class Meta:
        model = Archive
        fields = ["feed", "datetime_archived"]
