from django.urls import path

from .views import MarkdownContentView

urlpatterns = [
    # path("", views.docs, name="docs"),
    # path("<slug:docspage>/", views.docs, name="docs"),
    path("", MarkdownContentView.as_view(), name="docs"),
    path("<slug:docspage>/", MarkdownContentView.as_view(), name="docs"),
]
