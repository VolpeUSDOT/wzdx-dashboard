import markdown
from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe
from docs.markdown_extensions import SlugFieldExtension

register = template.Library()

MD_EXTENSIONS = ["fenced_code", "codehilite", SlugFieldExtension()]


@register.filter
@stringfilter
def render_markdown(value):
    md = markdown.Markdown(extensions=MD_EXTENSIONS)
    return mark_safe(md.convert(value))
