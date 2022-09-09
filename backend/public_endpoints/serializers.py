from rest_framework import serializers
from backend import models
#from ..devices.serializer import DeviceSerializer


class TankSerializer(serializers.ModelSerializer):
    Product = serializers.SlugRelatedField(
        slug_field='Name',
        read_only=True
        )
    class Meta:
        model = models.Tanks
        fields = ['Name', 'Product', 'Capacity']
        

class TankSiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Tanks
        fields = ['Tank_id']


class GetDeliveriesByTanksSerializer(serializers.Serializer):
    tank_name = serializers.CharField()
    start = serializers.CharField()
    end = serializers.CharField()

class GetTankDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AtgPrimaryLog
        fields = '__all__'

class GetTankInventoryResponseSerializer(serializers.Serializer):
	data = GetTankDataSerializer()
	error = serializers.CharField()
	code = serializers.IntegerField()
	status = serializers.CharField()


class GetTankProductResponseSerializer(serializers.Serializer):
	data = TankSiteSerializer()
	error = serializers.CharField()
	code = serializers.IntegerField()
	status = serializers.CharField()


class GetDailyConsumptionReportSerializer(serializers.Serializer):
	start = serializers.CharField()
	end = serializers.CharField()


class GetDailyConsumptionResponseSerializer(serializers.Serializer):
	data = TankSerializer()
	error = serializers.CharField()
	code = serializers.IntegerField()
	status = serializers.CharField()


class GenerateAPITokenResponseSerializer(serializers.Serializer):
	data = serializers.CharField()
	error = serializers.CharField()
	code = serializers.IntegerField()
	status = serializers.CharField()