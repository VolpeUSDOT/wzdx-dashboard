import markdown
from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe
from docs.markdown_extensions import SlugFieldExtension

register = template.Library()

MD_EXTENSIONS = ["fenced_code", "toc", SlugFieldExtension()]


@register.filter
@stringfilter
def render_markdown(value):
    md = markdown.Markdown(extensions=MD_EXTENSIONS)
    return mark_safe(md.convert(value))


@register.filter
@stringfilter
def get_toc(value):
    md = markdown.Markdown(extensions=MD_EXTENSIONS)
    html = md.convert(value)
    return md.toc_tokens  # type: ignore
