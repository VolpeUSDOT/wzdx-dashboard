from dashboard.models import Feed
from rest_framework_gis.serializers import GeoFeatureModelSerializer


class FeedPointsSerializer(
    GeoFeatureModelSerializer,
):
    class Meta:
        model = Feed
        fields = ("feedname", "issuingorganization")
        geo_field = "geocoded_column"
        auto_bbox = True
