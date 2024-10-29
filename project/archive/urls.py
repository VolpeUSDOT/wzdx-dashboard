from django.urls import path

from . import views

urlpatterns = [
    path("", views.ArchiveListView.as_view(), name="archive-list"),
    path("zip", views.download_all_in_zip, name="archive-zip"),
    path("<int:pk>/", views.archive_json, name="archive-details"),
]
