from datetime import timedelta

import humanize
import markdown
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def precisedelta(value):
    return humanize.precisedelta(value)
