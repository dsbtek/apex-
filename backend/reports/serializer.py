
from rest_framework import serializers
from backend import models

class SiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Sites
        fields = ["Site_id", "Device_id", "Name", ]


class TankSerializer(serializers.ModelSerializer):
    Site = SiteSerializer()
    class Meta:
        model = models.Tanks
        fields = ["Tank_id", "Tank_index", "Controller_polling_address", "Tank_controller", "Site"]


class ConsumptionResponseSerializer(serializers.Serializer):
    data = TankSerializer()
    error = serializers.CharField()
    code = serializers.IntegerField()
    status = serializers.CharField()


class ConsumptionReportSerializer(serializers.Serializer):
    tanks = serializers.ListField(
        child=serializers.IntegerField()
    )
    start = serializers.CharField()
    end = serializers.CharField()
    report_type = serializers.CharField()
