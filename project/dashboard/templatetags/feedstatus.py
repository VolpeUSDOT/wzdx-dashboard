from django import template
from django.template.defaultfilters import stringfilter

from ..models import FeedStatus

register = template.Library()


@register.filter
@stringfilter
def get_status_label(value: str):
    try:
        label = FeedStatus.StatusType(value).label
    except:
        return ""

    return label
