from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from backend import models
from ..companies.serializer import CompanySerializer
from ..devices.serializer import DeviceSerializer

class SiteSerializer(serializers.ModelSerializer):
	'''
	Validate Device id
	'''
	Company = CompanySerializer(read_only=True)
	Device = DeviceSerializer(read_only=True)
	Company_id = serializers.PrimaryKeyRelatedField(
		queryset=models.Companies.objects.all(),
		source='Company',
		write_only=True)
	Device_id = serializers.PrimaryKeyRelatedField (
		queryset=models.Devices.objects.all(),
		source='Device',
		write_only=True,
		allow_null=True)

	class Meta:
		model = models.Sites
		fields = ('Company_id', 'Company', 'Device_id', 'Device', 'Site_id',
		'Name','Country', 'State', 'City', 'Address', 'Latitude', 'Longitude',
		'Location_status','Site_type','Notes','SIM_provided_details','Number_of_tanks',
		'tank_count','Reorder_mail','Critical_level_mail','Contact_person_name',
		'Contact_person_designation','Contact_person_mail','Contact_person_phone',
		'Created_at','Updated_at','Active','Email_Notification','genhours_access','smarttank_access','smartpump_access')
	
	def validate(self, data):	
		'''
		Validate that device id selected belongs to the company
		Also, validate that the device is available
		'''
		company = data['Company']
		device = data['Device']
		# if not company.devices.filter(pk=device.pk).exists():
		# 	raise serializers.ValidationError("Device selected doesn't belong to the company")
		# if not device.available and not device.ForPump:
		# 	raise serializers.ValidationError("Device selected is not available")
		return data

class SiteSerializerUpdate(serializers.ModelSerializer):
	Device = DeviceSerializer(read_only=True)
	Device_id = serializers.PrimaryKeyRelatedField (
		queryset=models.Devices.objects.all(),
		source='Device',
		write_only=True,
		allow_null=True)
		

	class Meta:
		model = models.Sites
		fields = ('Company', 'Device_id', 'Device', 'Site_id',
		'Name','Country', 'State', 'City', 'Address', 'Latitude', 'Longitude',
		'Location_status','Site_type','Notes','SIM_provided_details','Number_of_tanks',
		'tank_count','Reorder_mail','Critical_level_mail','Contact_person_name',
		'Contact_person_designation','Contact_person_mail','Contact_person_phone',
		'Created_at','Updated_at','Active','Email_Notification','genhours_access','smarttank_access','smartpump_access')

	
	def validate(self, data):	
		'''
		Check if the Device was changed, company can not be updated
		'''
		company = self.instance.Company
		device = data.get('Device', None)
		if device and device.pk != self.instance.Device.pk:
			if not company.devices.filter(pk=device.pk).exists():
				raise serializers.ValidationError("Device selected doesn't belong to the company")
			if not device.available:
				raise serializers.ValidationError("Device selected is not available")
		return data


class SiteSerializerWithOnlyName(serializers.ModelSerializer):
	Company = serializers.CharField(source='Company.Name')
	class Meta:
		model = models.Sites
		fields = ('Site_id','Name', 'Company')