from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from .forms import DocsContentForm
from .models import DocsContent

# Create your views here.


class StaffMemberRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff  # type: ignore


def docs_redirect(request):
    docs_first = DocsContent.objects.first()

    if docs_first is None:
        raise Http404("No docs exist.")

    return redirect(docs_first)


class DocsContentView(DetailView):
    model = DocsContent
    context_object_name = "docs_content"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["all_docs"] = DocsContent.objects.filter(parent_content=None).only(
            "title", "slug"
        )
        return context


class DocsContentCreateView(StaffMemberRequiredMixin, CreateView):
    model = DocsContent
    form_class = DocsContentForm


class DocsContentUpdateView(StaffMemberRequiredMixin, UpdateView):
    model = DocsContent
    form_class = DocsContentForm


class DocsContentDeleteView(StaffMemberRequiredMixin, DeleteView):
    model = DocsContent
    success_url = reverse_lazy("docs-redirect")
