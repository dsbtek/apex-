import redis
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from backend import models
from ..companies.serializer import CompanySerializer

from drf_spectacular.utils import extend_schema_serializer
from decouple import config

class UniqueAddressTrackerSerializer(serializers.ModelSerializer):
	class Meta:
		model = models.UniqueAddressTracker
		fields = '__all__'


class DeviceSerializer(serializers.ModelSerializer):
	Company = CompanySerializer(read_only=True)
	Company_id = serializers.PrimaryKeyRelatedField(queryset=models.Companies.objects.all(), source='Company', write_only=True, required=False)
	Site = serializers.CharField(source='get_site.Name', read_only=True, default="")

	class Meta:
		model = models.Devices
		fields = ['Device_id', 'Name', 'Device_unique_address','Company', 'Company_id',
				'Site', 'Phone_number', 'Created_at', 'Updated_at', 'Deleted_at',
				'transmit_interval', 'available',  'Active', 'ForPump', 'Used']
		extra_kwargs = {'Device_id': {'read_only': True}}
		

class DeviceRedisOnlineSerializer(serializers.ModelSerializer):
	SiteID = serializers.PrimaryKeyRelatedField(read_only=True, source='get_site.Site_id', default=None)
	Site_Name = serializers.CharField(source='get_site.Name', default="")
	seen = serializers.SerializerMethodField()

	class Meta:
		model = models.Devices
		fields = ['Name', 'Device_unique_address', 'SiteID', 'Site_Name', 'seen']
		#r = redis.Redis(host='127.0.0.1', port=6379, db=0) Testing redis works
	def get_seen(self, obj):
		r = redis.Redis(host=config('REDIS_HOST'), port=config('REDIS_PORT'), db=0)
		return r.get(obj.Device_unique_address)

	def to_representation(self, obj):
		primitive_repr = super(DeviceRedisOnlineSerializer, self).to_representation(obj)
		primitive_repr['Serial Number'] = primitive_repr.pop('Name')
		primitive_repr['MAC Address'] = primitive_repr.pop('Device_unique_address')
		primitive_repr['Site Name'] = primitive_repr.pop('Site_Name')
		primitive_repr['Last Seen'] = primitive_repr.pop('seen')

		return primitive_repr
	

class DeviceActivationDetailSerializer(serializers.Serializer):
	action = serializers.CharField(required=True)


class ADCSensorSerializer(serializers.Serializer):
	mac_address = serializers.CharField()


class TankDatailsSerializer(serializers.Serializer):
	Name = serializers.CharField()
	Controller = serializers.CharField()
	Controller_id = serializers.IntegerField()
	Tank_index = serializers.CharField()
