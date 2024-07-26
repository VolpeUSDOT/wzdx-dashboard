from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="home"),
    path("<str:feedname>/", views.feed, name="feed"),
]
