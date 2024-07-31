from django.db.models import BooleanField, ExpressionWrapper, F, Func, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, render

from .models import MarkdownContent


# Create your views here.
class Lower(Func):
    function = "LOWER"


def docs(request, docspage=""):
    markdown_content = get_object_or_404(MarkdownContent, slug=docspage)
    all_docs = MarkdownContent.objects.annotate(
        current_page=ExpressionWrapper(
            Q(slug__exact=docspage),
            BooleanField(),
        )
    ).values("title", "slug", "current_page")

    context = {
        "markdown_content": markdown_content,
        "all_docs": all_docs,
    }

    return render(request, "docs/markdown.html", context=context)
