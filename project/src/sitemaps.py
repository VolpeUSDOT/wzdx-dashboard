from typing import Union

from dashboard.models import Feed, FeedData
from django.contrib.sitemaps import GenericSitemap, Sitemap
from django.urls import reverse
from docs.models import DocsContent


class FeedSites(Sitemap):
    changefreq = "hourly"

    def items(self):
        queryset = Feed.objects.all()
        return [*queryset] + [""]

    def location(self, obj: Union[Feed, str]):
        if isinstance(obj, Feed):
            return obj.get_absolute_url()  # type: ignore
        else:
            return reverse("feed_list")

    def lastmod(self, obj: Union[Feed, str]):
        if isinstance(obj, Feed):
            return obj.last_checked()  # type: ignore
        else:
            latest = FeedData.objects.all().order_by("-last_checked").first()
            if latest is None:
                return None
            else:
                return latest.feed.last_checked()


docs_sites = GenericSitemap(
    {"queryset": DocsContent.objects.all(), "date_field": "last_editted"}
)


sitemaps = {"feeds": FeedSites, "docs": docs_sites}
