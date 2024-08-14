from rest_framework import routers

from .views import FeedPointsViewSet, FeedViewSet

router = routers.DefaultRouter()
router.register(r"points", FeedPointsViewSet, basename="api-points")
router.register(r"feeds", FeedViewSet, basename="api-feeds")

urlpatterns = router.urls
