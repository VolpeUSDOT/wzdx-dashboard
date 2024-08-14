from django.urls import path

from . import views

urlpatterns = [
    path("", views.ArchiveListView.as_view(), name="archive-list"),
    path("<int:pk>/", views.archive_json, name="archive-details"),
]
