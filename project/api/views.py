from dashboard.models import Feed
from rest_framework import viewsets
from rest_framework_gis import filters

from .serializers import FeedPointsSerializer


# Create your views here.
class FeedPointsViewSet(
    viewsets.ReadOnlyModelViewSet,
):
    bbox_filter_field = "geocoded_column"
    filter_backends = [filters.InBBoxFilter]
    queryset = Feed.objects.all()
    serializer_class = FeedPointsSerializer
