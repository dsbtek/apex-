from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from backend import models


class HourlyResponseSerializer(serializers.Serializer):
    equipments = serializers.ListField()
    dates = serializers.ListField()
    sources = serializers.DictField()


class HourlyRequestSerializer(serializers.Serializer):
    equipment_id = serializers.IntegerField()
    date = serializers.CharField()


class FlowmeterLogsSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.FlowmeterLogs
        fields = "__all__"


class TransactionCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.FlowmeterTransactionComment
        fields = "__all__"
        validators = [
            UniqueTogetherValidator(
                queryset=model.objects.all(),
                fields=('equipment', 'trx_end_time'),
                message='Comment already added. You can only edit'
            )
        ]


class EquipmentConsumptionResponseSerializer(serializers.Serializer):
    equipments = serializers.ListField()
    dates = serializers.ListField()
    sources = serializers.DictField()


class EquipmentRequestSerializer(serializers.Serializer):
    site_ids = serializers.ListField()
    start = serializers.CharField()
    end = serializers.CharField()


# EquipmentDashboard Serializer classes
class EquipmentDashboardViewSerializer(serializers.Serializer):
    site_ids = serializers.ListField()


class EquipmentDashboardResponseSerializer(serializers.Serializer):
    equipment = serializers.CharField()
    site_name = serializers.CharField()
    online_status = serializers.BooleanField()
    totaliser_hours = serializers.IntegerField()
    last_updated_time = serializers.CharField()


class EquipmentLogsSerializer(serializers.Serializer):
    equipment_id = serializers.IntegerField()
    # equipment_id = serializers.ListField()
    start = serializers.CharField()
    end = serializers.CharField()


class GenLoggerSerializer(serializers.Serializer):
    gen_hour_logs = serializers.CharField()


class GenPowerLoggerSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PowermeterLogs
        fields = "__all__"


class PowerMeterSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PowerMeter
        fields = "__all__"


class SiteSerializer(serializers.ModelSerializer):
    Company = serializers.StringRelatedField()

    class Meta:
        model = models.Sites
        fields = ['Site_id', 'Name', 'Company']


class PowerMeterListSerializer(serializers.ModelSerializer):
    site = SiteSerializer()
    equipment = serializers.StringRelatedField()

    class Meta:
        model = models.PowerMeter
        fields = ['id', 'serial_number', 'site', 'meter_type',
                  'address', 'active', 'created_at', 'equipment']


class PowermeterLogsSerializer(serializers.ModelSerializer):
    equipment = serializers.StringRelatedField()

    class Meta:
        model = models.PowermeterLogs
        fields = "__all__"


class EquipmentListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Equipment
        fields = "__all__"


class FlowmeterTimestamp(serializers.Serializer):
    timestamp = serializers.ListField()
    sources = serializers.DictField()


class EquipmentFlowmeterSourceDataSerializer(serializers.Serializer):
    Consumption_rates = serializers.FloatField()
    Forward_rates = serializers.FloatField()
    Reverse_rates = serializers.FloatField()


class EquipmentFlowmeterResponseSerializer(serializers.Serializer):
    timestamps = serializers.DateField()
    sources = EquipmentFlowmeterSourceDataSerializer()
