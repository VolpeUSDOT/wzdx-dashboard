from django.urls import path

from .views import (
    DocsContentCreateView,
    DocsContentDeleteView,
    DocsContentUpdateView,
    DocsContentView,
    docs_redirect,
)

urlpatterns = [
    path("add/", DocsContentCreateView.as_view(), name="docs-add"),
    path("<slug:slug>/update/", DocsContentUpdateView.as_view(), name="docs-update"),
    path(
        "<slug:slug>/delete/",
        DocsContentDeleteView.as_view(),
        name="docs-delete",
    ),
    path("<slug:slug>/", DocsContentView.as_view(), name="docs-view"),
    path("", docs_redirect, name="docs-redirect"),
]
