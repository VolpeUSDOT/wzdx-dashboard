import django_tables2 as tables
from django.utils.html import format_html

from .models import Archive


def format_bytes(size: float):
    # 2**10 = 1024
    power = 2**10
    n = 0
    power_labels = {0: "", 1: "kilo", 2: "mega", 3: "giga", 4: "tera"}
    while size > power:
        size /= power
        n += 1

    return f"{round(size, 2)} {power_labels[n]}bytes"


class ArchiveTable(tables.Table):
    id = tables.Column(attrs={"th": {"scope": "col", "role": "columnheader"}})
    feed = tables.Column(attrs={"th": {"scope": "col", "role": "columnheader"}})
    datetime_archived = tables.Column(
        attrs={"th": {"scope": "col", "role": "columnheader"}},
        verbose_name="Date Archived",
    )
    size = tables.Column(attrs={"th": {"scope": "col", "role": "columnheader"}})

    class Meta:
        model = Archive
        template_name = "django_tables2/bootstrap.html"
        fields = ("id", "feed", "datetime_archived", "size")
        attrs = {"class": "usa-table width-full", "tabindex": "0"}
        template_name = "archive/usa_table.html"

    def render_id(self, value, record):
        return format_html(
            '<a href="{}" class="usa-link">{}</a>',
            record.get_absolute_url(),
            value,
        )

    def render_size(self, value, record):
        return format_bytes(value)
