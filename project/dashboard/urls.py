from django.urls import path

from . import views

urlpatterns = [
    path("", views.FeedListView.as_view(), name="home"),
    path("<str:feedname>/", views.feed, name="feed"),
]
