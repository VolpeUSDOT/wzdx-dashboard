import re

import markdown
from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe
from docs.markdown_extensions import SlugFieldExtension

register = template.Library()

MD_EXTENSIONS = [
    "fenced_code",
    "codehilite",
    "footnotes",
    "smarty",
    "nl2br",
    SlugFieldExtension(),
]
md = markdown.Markdown(extensions=MD_EXTENSIONS)


@register.filter
@stringfilter
def render_markdown(value):

    return mark_safe(md.convert(value))


@register.filter
@stringfilter
def render_no_p_markdown(value):
    return mark_safe(re.sub("(^<P>|</P>$)", "", md.convert(value), flags=re.IGNORECASE))
