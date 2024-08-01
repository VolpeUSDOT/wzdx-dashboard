from django.contrib.gis.db.models import Max, OuterRef, Subquery
from django.core.paginator import Page, Paginator
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView

from .forms import SearchForm
from .models import Feed, FeedStatus


def get_page_button_array(paginator: Paginator, page: Page):
    total_pages = paginator.num_pages
    page_range = paginator.page_range
    if total_pages < 5:
        return page_range[0:total_pages]
    else:
        current_page = page.number
        if current_page < 4:
            return page_range[0:5]
        else:
            first_page = current_page - 3
            last_page = current_page + 5
            return page_range[first_page:last_page]


@method_decorator(csrf_exempt, name="dispatch")
class FeedListView(ListView):
    model = Feed
    paginate_by = 6

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
