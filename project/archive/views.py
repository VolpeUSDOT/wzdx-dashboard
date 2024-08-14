from typing import Optional, Union

from django.core.paginator import Page, Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin

from .filter import ArchiveFilter
from .models import Archive
from .tables import ArchiveTable

# Create your views here.


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


class ArchiveListView(SingleTableMixin, FilterView):
    model = Archive
    table_class = ArchiveTable
    context_object_name = "archives"
    queryset = Archive.objects.only("id", "feed", "datetime_archived", "size").all()
    template_name = "archive/archive.html"

    filterset_class = ArchiveFilter


def archive_json(request, pk):
    data = get_object_or_404(Archive.objects, pk=pk)

    return JsonResponse(data.data)
