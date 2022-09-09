from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from backend import models
from ..sites.serializer import SiteSerializerWithOnlyName


class FlowMeterSerializer(serializers.ModelSerializer):
    site = SiteSerializerWithOnlyName(read_only=True)
    site_id = serializers.PrimaryKeyRelatedField(
        queryset=models.Sites.objects.all(),
        write_only=True,
        source='site', allow_null=True)
    available = serializers.BooleanField(read_only=True)

    class Meta:
        model = models.Flowmeter
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=model.objects.all(),
                fields=('site', 'address', 'meter_type'),
                message='Flowmeter address already assigned for this meter type in this site'
            )
        ]


class FlowMeterSerializerWithName(serializers.ModelSerializer):
    class Meta:
        model = models.Flowmeter
        fields = ('id', 'serial_number')


class FlowmeterActivationDetailSerializer(serializers.Serializer):
    action = serializers.CharField()