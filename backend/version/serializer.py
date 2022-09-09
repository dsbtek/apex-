from rest_framework import serializers
from backend import models


class VersionSerializer(serializers.ModelSerializer):

	class Meta:
		model = models.Version
		fields = '__all__'


class DeviceDataSerializer(serializers.ModelSerializer):
	Serial_number = serializers.CharField(source='device.Name')
	Site_name = serializers.CharField(default='', source='device.site.Name')

	class Meta:
		model = models.DeviceFirmwareVersion
		fields = '__all__'


	def to_representation(self, obj):
		reprs = super().to_representation(obj)
		reprs['Device_address'] = reprs.pop('device_mac_address')
		reprs['Current_version'] = reprs.pop('version_number')
		reprs['Expected_version'] = reprs.pop('expected_version_number')
		reprs['Version_last_update'] = reprs.pop('updated_at')
		reprs['Device_id'] = reprs.pop('device')

		return reprs



class DeviceFirmwareUpdateSerializer(serializers.Serializer):
	Device = serializers.CharField()
	Version = serializers.CharField()
