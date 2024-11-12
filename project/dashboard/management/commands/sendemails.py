from datetime import date, datetime, timedelta

from dashboard.models import Feed, FeedStatus
from django.contrib.auth.models import User
from django.contrib.gis.db.models import Count
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.utils.html import strip_tags


class Command(BaseCommand):
    """
    Sends weekly status email regarding feeds
    """

    def handle(self, *args, **options):

        feed_context = Feed.objects.all()

        enddate = date.today()
        startdate = enddate - timedelta(days=14)

        status_summary: dict[str, list[tuple[str, str]]] = {}
        for feed in feed_context:

            total_status_count = FeedStatus.objects.filter(
                feed=feed.pk, datetime_checked__range=[startdate, enddate]
            ).count()

            status_summary[feed.pk] = [
                (
                    FeedStatus.StatusType(status["status_type"]).label,
                    str(round(status["count"] / total_status_count * 100, 2)),
                )
                for status in (
                    FeedStatus.objects.filter(
                        feed=feed.pk,
                        datetime_checked__range=[startdate, enddate],
                    )
                    .values("status_type")
                    .annotate(count=Count("status_type"))
                    .order_by("-count")
                )
            ]

        subject, from_email, to = (
            f"WZDx Status: {datetime.today().strftime('%Y-%m-%d')}",
            "wzdx-dashboard@dot.gov",
            [
                staff_user.email
                for staff_user in (
                    User.objects.filter(is_staff=True)
                    .exclude(email__isnull=True)
                    .exclude(email__exact="")
                    .all()
                )
            ],
        )

        html_content = render_to_string(
            "dashboard/sendemails.html",
            {"feeds": feed_context, "status_summary": status_summary},
        )
        text_content = strip_tags(html_content)
        send_mail(subject, text_content, from_email, to, html_message=html_content)
