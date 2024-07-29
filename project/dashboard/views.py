from django.contrib.gis.db.models import Field
from django.http import Http404, HttpResponse
from django.shortcuts import render

from .models import Feed


# Create your views here.
def index(request):
    headers = [
        field.verbose_name  # type: ignore
        for field in Feed._meta.get_fields()
        if issubclass(type(field), Field)
    ]
    feed_list = Feed.objects.order_by("sdate").values()
    context = {"feeds": feed_list, "headers": headers}
    return render(request, "dashboard/index.html", context)


def feed(request, feedname):
    try:
        feed = Feed.objects.get(pk=feedname)
    except Feed.DoesNotExist:
        raise Http404("Feed does not exist")

    context = {"feed": feed}
    return render(request, "polls/detail.html", context)
