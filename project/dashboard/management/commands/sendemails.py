from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """
    Sends weekly status email regarding feeds
    """

    def handle(self, *args, **options):
        # email = EmailMessage(
        #     f"WZDx Status: {datetime.today().strftime('%Y-%m-%d')}",
        #     "this is a test email :3",
        #     "wzdx-dashboard@dot.gov",
        #     ["diego.temkin@dot.gov"],
        # )

        # email.send()
        pass
