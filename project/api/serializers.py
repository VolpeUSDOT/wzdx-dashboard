from dashboard.models import Feed, FeedData
from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer


class FeedPointsSerializer(
    GeoFeatureModelSerializer,
):
    status_type = serializers.SerializerMethodField()

    def get_status_type(self, obj):
        return obj.feed_status().status_type

    class Meta:
        model = Feed
        fields = ("status_type", "issuingorganization")
        geo_field = "geocoded_column"
        auto_bbox = True


class FeedSerializer(serializers.ModelSerializer):

    feed_data = serializers.SerializerMethodField()

    def get_feed_data(self, obj):
        return obj.feed_data()

    class Meta:
        model = Feed
        fields = "__all__"
