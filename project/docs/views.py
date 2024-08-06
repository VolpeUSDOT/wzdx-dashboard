from typing import Any

from django.db.models import BooleanField, ExpressionWrapper, Q
from django.views.generic.detail import DetailView

from .models import MarkdownContent

# Create your views here.


class MarkdownContentView(DetailView):
    model = MarkdownContent
    template_name = "docs/markdown.html"
    context_object_name = "markdown_content"

    def get_object(self):
        pk = self.kwargs.get(self.pk_url_kwarg)
        slug = self.kwargs.get(self.slug_url_kwarg)

        if pk is None and slug is None:
            self.kwargs["slug"] = ""

        return super().get_object()

    def get_context_data(self, **kwargs: Any):
        context = super().get_context_data(**kwargs)

        context["all_docs"] = (
            MarkdownContent.objects.annotate(
                current_page=ExpressionWrapper(
                    Q(slug__exact=self.kwargs["slug"]),
                    BooleanField(),
                )
            )
            .values("title", "slug", "current_page")
            .order_by("id")
        )

        return context
