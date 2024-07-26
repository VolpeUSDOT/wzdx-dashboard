from django.http import Http404, HttpResponse
from django.shortcuts import render

from .models import Feed


# Create your views here.
def index(request):
    feed_list = Feed.objects.order_by("sdate").values()
    headers = [
        field.verbose_name  # type: ignore
        for field in Feed._meta.get_fields()
        if hasattr(field, "verbose_name")
    ]
    context = {"feeds": feed_list, "headers": headers}
    return render(request, "dashboard/index.html", context)


def feed(request, feedname):
    try:
        feed = Feed.objects.get(pk=feedname)
    except Feed.DoesNotExist:
        raise Http404("Feed does not exist")

    context = {"feed": feed}
    return render(request, "polls/detail.html", context)
