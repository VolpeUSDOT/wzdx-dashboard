from rest_framework import routers

from .views import FeedPointsViewSet

router = routers.DefaultRouter()
router.register(r"points", FeedPointsViewSet)

urlpatterns = router.urls
