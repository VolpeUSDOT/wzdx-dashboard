from django.db.models import BooleanField, ExpressionWrapper, Q
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from .forms import DocsContentForm
from .models import DocsContent

# Create your views here.


def docs_redirect(request):
    docs_first = DocsContent.objects.first()

    if docs_first is None:
        raise Http404("No docs exit.")

    return redirect(docs_first)


class DocsContentView(DetailView):
    model = DocsContent
    context_object_name = "docs_content"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["all_docs"] = (
            DocsContent.objects.annotate(
                current_page=ExpressionWrapper(
                    Q(slug__exact=self.kwargs["slug"]),
                    BooleanField(),
                )
            )
            .values("title", "slug", "current_page")
            .order_by("id")
        )

        return context


class DocsContentCreateView(CreateView):
    model = DocsContent
    form_class = DocsContentForm


class DocsContentUpdateView(UpdateView):
    model = DocsContent
    form_class = DocsContentForm


class DocsContentDeleteView(DeleteView):
    model = DocsContent
    success_url = reverse_lazy("docs-redirect")
