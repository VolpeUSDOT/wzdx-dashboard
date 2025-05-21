import json
from typing import Any

from django.shortcuts import render
from shared.schema_check import get_version_schema_errors

from .forms import SchemaForm


def index(request):
    # process form response
    context: dict[str, Any] = {}
    if request.method == "POST":
        form = SchemaForm(request.POST)
        if form.is_valid():
            errors = get_version_schema_errors(
                json.loads(form.cleaned_data["feed_data"]), form.cleaned_data["version"]
            )

            if len(errors) < 1:
                errors = ["No errors found!"]

            context["errors"] = errors

    else:
        form = SchemaForm()

    context["form"] = form

    return render(request, "schema/index.html", context)
