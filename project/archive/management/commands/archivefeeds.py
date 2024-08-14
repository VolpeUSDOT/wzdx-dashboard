import json
import sys

from archive.models import Archive
from dashboard.models import Feed
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Archive all feeds into a separate database table."

    def handle(self, *args, **options):
        for feed in Feed.objects.all():
            self.stdout.write(self.style.NOTICE(f"Archiving {feed.feedname}..."))
            feed_data = feed.feed_data()
            if feed_data:
                Archive.objects.create(
                    feed=feed,
                    data=feed_data,
                    size=(sys.getsizeof(json.dumps(feed_data)) - sys.getsizeof("")),
                )

        self.stdout.write(self.style.SUCCESS("Done archiving!"))
