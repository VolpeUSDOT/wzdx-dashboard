from typing import Union

from django.contrib.gis.db.models import Max, OuterRef, Subquery
from django.core.paginator import Page, Paginator
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView

from .forms import SearchForm
from .models import Feed, FeedStatus


def get_page_button_array(paginator: Paginator, page: Page) -> list[Union[int, str]]:
    """Create what pages to use, based on guidelines from USWDS page https://designsystem.digital.gov/components/pagination/"""
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


@method_decorator(csrf_exempt, name="dispatch")
class FeedListView(ListView):
    model = Feed
    paginate_by = 5

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_range"] = get_page_button_array(
            context["paginator"], context["page_obj"]
        )
        context["form"] = SearchForm()

        return context

    def post(self, request, *args, **kwargs):
        form = SearchForm(request.POST)
        feed_redirect = form.data["feed_to_find"]

        return HttpResponseRedirect(f"/feeds/{feed_redirect}")


def feed(request, feedname):
    try:
        feed = Feed.objects.get(pk=feedname)
    except Feed.DoesNotExist:
        raise Http404("Feed does not exist")

    context = {"feed": feed}
    return render(request, "dashboard/feed_object.html", context)
