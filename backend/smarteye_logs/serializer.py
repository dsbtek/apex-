from rest_framework import serializers
from backend import models

class LogSerializer(serializers.ModelSerializer):
	# site_name = serializers.CharField(source='tank.Site.Name', default="")
	# siteId = serializers.PrimaryKeyRelatedField(read_only=True, source='tank.Site.Site_id', default=None)
	# tank_name = serializers.CharField(source='tank.Name', default="")
	# Tank_id = serializers.PrimaryKeyRelatedField(read_only=True, source='tank.Tank_id', default=None)
	# tank_capacity = serializers.IntegerField(source='tank.Capacity', default=0)
	# Unit = serializers.CharField(source='tank.UOM', default="")
	class Meta:
		model = models.AtgPrimaryLog
		fields = ['controller_type', 'multicont_polling_address', 'tank_index',
				'pv', 'sv', 'read_at']
		# ['site_name', 'siteId', 'tank_name', 'Tank_id', 'tank_capacity',
		# 		'Unit',] 

	def to_representation(self, obj):
		primitive_repr = super(LogSerializer, self).to_representation(obj)
		# primitive_repr['Site Name'] = primitive_repr.pop('site_name')
		# primitive_repr['Tank Name'] = primitive_repr.pop('tank_name')
		# primitive_repr['Tank Capacity'] = primitive_repr.pop('tank_capacity')
		# primitive_repr['Controller polling address'] = primitive_repr.pop('multicont_polling_address')
		# primitive_repr['Tank index'] = primitive_repr.pop('tank_index')
		primitive_repr['Volume'] = primitive_repr.pop('pv')
		primitive_repr['Height'] = primitive_repr.pop('sv')
		primitive_repr['Log Time'] = primitive_repr.pop('read_at')
		primitive_repr['Controller_type'] = primitive_repr.pop('controller_type')

		return primitive_repr

# class TankLogsSerializer(serializers.ModelSerializer):
# 	pass
# 	class Meta:
# 		model = models.AtgPrimaryLog
# 		fields = ['']


#EquipmentDashboard Serializer classes
class TankMapSerializer(serializers.Serializer):
	site_ids = serializers.ListField()

class LatestTankLogSerializer(serializers.ModelSerializer):
	class Meta:
		model = models.LatestAtgLog
		fields = (
			'Tank_id','Tank_name','Volume','Height','last_updated_time','Site_id','siteName','Capacity','DisplayUnit','Product','Fill','Tank_controller','Reorder','LL_Level','HH_Level','temperature','water','Tank_Status','Tank_Note'
		)

class TankLogAnomalySerializer(serializers.ModelSerializer):
	class Meta:
		model = models.TankLogAnomaly
		fields = (
			'site_name', 'tank_name', 'anomaly_period',
				'anomaly_difference'
		)