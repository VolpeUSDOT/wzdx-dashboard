from dashboard.models import Feed
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


# Create your models here.
class Archive(models.Model):
    feed = models.ForeignKey(
        Feed,
        on_delete=models.CASCADE,
    )

    datetime_archived = models.DateTimeField(auto_now_add=True)

    data = models.JSONField(
        default=dict,
    )

    size = models.IntegerField(default=0)

    class Meta:
        ordering = ["-datetime_archived"]
        verbose_name_plural = _("archives")

    def __str__(self):
        return f"{self.feed.issuingorganization} on {self.datetime_archived}"

    def get_absolute_url(self):
        return reverse("archive-details", kwargs={"pk": self.pk})
