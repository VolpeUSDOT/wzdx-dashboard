from rest_framework import routers

from .views import FeedPointsViewSet, FeedViewSet

router = routers.DefaultRouter()
router.register(r"points", FeedPointsViewSet, basename="Points")
router.register(r"feeds", FeedViewSet, basename="Feeds")

urlpatterns = router.urls
