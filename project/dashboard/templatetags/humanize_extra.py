import humanize
from django import template

register = template.Library()


@register.filter
def precisedelta(value):
    return humanize.precisedelta(value)
