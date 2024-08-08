from dashboard.models import Feed, FeedData
from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer


class FeedPointsSerializer(
    GeoFeatureModelSerializer,
):
    class Meta:
        model = Feed
        fields = "__all__"
        geo_field = "geocoded_column"
        auto_bbox = True


class FeedDataSerializer(serializers.ModelSerializer):

    class Meta:
        model = FeedData
        fields = "__all__"


class FeedSerializer(serializers.ModelSerializer):

    class Meta:
        model = Feed
        fields = "__all__"
