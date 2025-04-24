from dashboard.models import Feed
from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer


class FeedPointsSerializer(
    GeoFeatureModelSerializer,
):
    status_type = serializers.SerializerMethodField()

    def get_status_type(self, obj):
        feed_status = obj.feed_status()

        if feed_status:
            return feed_status.status_type

        return ""

    class Meta:
        model = Feed
        fields = ("status_type", "issuingorganization", "pk")
        geo_field = "geocoded_column"
        auto_bbox = True


class FeedSerializer(serializers.ModelSerializer):

    feed_data = serializers.SerializerMethodField()

    def get_feed_data(self, obj):
        return obj.feed_data()

    class Meta:
        model = Feed
        fields = "__all__"
