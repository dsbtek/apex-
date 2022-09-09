from rest_framework import serializers
from backend import models
from ..tanks.serializer import TankSerializer


class TankGroupSerializer(serializers.ModelSerializer):

	class Meta:
		model = models.TankGroups
		fields = ('Group_id', 'Name', 'Product', 'Company',
				  'UOM', 'current_capacity','tank_count','Reorder_Level', 'Alarm_LL_Level',
				  'Alarm_HH_Level','Critical_level_mail', 'Reorder_mail',
				  'Notes',
				  'Created_at', 'Updated_at', 'Deleted_at', 'Status',
				  )


class TankGroupWithTankSerializer(serializers.ModelSerializer):
	Tanks = TankSerializer(many=True, read_only=True)

	class Meta:
		model = models.TankGroups
		fields = ('Group_id', 'Name', 'Product', 'Company',
				  'UOM', 'Tanks','current_capacity', 'tank_count', 'Reorder_Level',
				  'Alarm_LL_Level', 'Alarm_HH_Level', 'Critical_level_mail', 'Reorder_mail',
				  'Notes',
				  'Created_at', 'Updated_at', 'Deleted_at', 'Status',
				  )

		