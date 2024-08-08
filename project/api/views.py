from dashboard.models import Feed, FeedData
from rest_framework import viewsets
from rest_framework_gis import filters

from .serializers import FeedDataSerializer, FeedPointsSerializer, FeedSerializer


# Create your views here.
class FeedPointsViewSet(
    viewsets.ReadOnlyModelViewSet,
):
    bbox_filter_field = "geocoded_column"
    filter_backends = [filters.InBBoxFilter]
    queryset = Feed.objects.all()
    serializer_class = FeedPointsSerializer


class FeedDataViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = FeedData.objects.all()
    serializer_class = FeedDataSerializer

    def get_queryset(self):
        feed = self.kwargs["feed"]
        return FeedData.objects.filter(feed=feed)


class FeedViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Feed.objects.all()
    serializer_class = FeedSerializer
