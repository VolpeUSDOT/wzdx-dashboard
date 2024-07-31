from django.contrib.gis.db.models import Field
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.utils.safestring import SafeText
from django.views.decorators.csrf import csrf_exempt

from .forms import SearchForm
from .models import Feed


# Create your views here.
@csrf_exempt
def index(request):
    headers = [
        field.verbose_name  # type: ignore
        for field in Feed._meta.get_fields()
        if issubclass(type(field), Field)
    ]
    feed_list = Feed.objects.order_by("sdate").values()

    if request.method == "POST":
        form = SearchForm(request.POST)
        feed_redirect = form.data["feed_to_find"]

        return HttpResponseRedirect(f"/feeds/{feed_redirect}")
    else:
        form = SearchForm()
        rendered_form = form.render()  # type: ignore

    context = {"feeds": feed_list, "headers": headers, "form": rendered_form}

    return render(request, "dashboard/index.html", context)


def feed(request, feedname):
    try:
        feed = Feed.objects.get(pk=feedname)
    except Feed.DoesNotExist:
        raise Http404("Feed does not exist")

    context = {"feed": feed}
    return render(request, "dashboard/feed.html", context)
