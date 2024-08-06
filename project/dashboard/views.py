from mimetypes import init
from typing import Optional, Union

from django.core.paginator import Page, Paginator
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView, FormView, ListView
from django.views.generic.detail import SingleObjectMixin

from .forms import SearchForm
from .models import Feed


def get_page_button_array(
    paginator: Optional[Paginator], page: Page
) -> list[Union[int, str]]:
    """Create what pages to use, based on guidelines from USWDS page https://designsystem.digital.gov/components/pagination/"""

    if paginator is None:
        return []

    total_pages = paginator.num_pages
    current_page = page.number

    if total_pages < 7:
        return list(range(1, total_pages + 1))

    else:
        if current_page == 1 or current_page == 2 or current_page == 3:
            return [1, 2, 3, 4, 5, "...", total_pages]
        elif (
            current_page == total_pages
            or current_page == total_pages - 1
            or current_page == total_pages - 2
        ):
            return [
                1,
                "...",
                total_pages - 4,
                total_pages - 3,
                total_pages - 2,
                total_pages - 1,
                total_pages,
            ]
        else:
            return [
                1,
                "...",
                current_page - 1,
                current_page,
                current_page + 1,
                "...",
                total_pages,
            ]


# @method_decorator(csrf_exempt, name="dispatch")
class FeedListView(ListView):
    model = Feed
    paginate_by = 8
    context_object_name = "feeds"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_range"] = get_page_button_array(
            context["paginator"], context["page_obj"]
        )
        context["search_form"] = SearchForm()

        return context


class FeedDetailView(DetailView):
    model = Feed
    context_object_name = "feed"

    # def get_object(self):
    #     obj = super().get_object()
    #     # Get more data here!
    #     return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["search_form"] = SearchForm(initial={"search_feed": context["feed"].pk})

        return context
