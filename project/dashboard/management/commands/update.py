from django.core import management
from django.core.management.base import BaseCommand

from .checkfeeds import Command as CheckFeeds
from .syncdatahub import Command as SyncDataHub


class Command(BaseCommand):
    """
    Update feeds from DataHub and check their validity
    """

    def handle(self, *args, **options):
        management.call_command(SyncDataHub(), *args, **options)
        management.call_command(CheckFeeds(), *args, **options)
