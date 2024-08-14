from rest_framework import routers

from .views import FeedPointsViewSet, FeedViewSet

router = routers.DefaultRouter()
router.register(r"points", FeedPointsViewSet, basename="points")
router.register(r"feeds", FeedViewSet)

urlpatterns = router.urls
