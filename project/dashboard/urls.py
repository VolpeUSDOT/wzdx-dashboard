from django.urls import path

from . import views

urlpatterns = [
    path("", views.FeedListView.as_view(), name="feed-list"),
    path("<str:pk>/", views.FeedDetailView.as_view(), name="feed-detail"),
]
