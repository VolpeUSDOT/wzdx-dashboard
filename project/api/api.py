from rest_framework import routers

from .views import FeedDataViewSet, FeedPointsViewSet, FeedViewSet

router = routers.DefaultRouter()
router.register(r"points", FeedPointsViewSet, basename="Points")
router.register(r"data/(?P<feed>.+)", FeedDataViewSet, basename="FeedData")
router.register(r"feeds", FeedViewSet, basename="Feeds")

urlpatterns = router.urls
