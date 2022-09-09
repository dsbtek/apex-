from django.db import transaction
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from backend import models

from ..equipments.serializer import EquipmentSerializer


class MaintenanceConfigSerializer(serializers.ModelSerializer):
    equipment = EquipmentSerializer(read_only=True)
    equipment_id = serializers.PrimaryKeyRelatedField(
        queryset=models.Equipment.objects.all(),
        source='equipment',
        write_only=True
    )
    
    class Meta:
        model = models.MaintenanceConfig
        fields = '__all__'

    def validate(self, data):
        mode = data.get('mode')
        if mode == 'HR/D':
            #check that scheduled_days is None
            if data['scheduled_days'] is not None:
                raise serializers.ValidationError("Should not set scheduled days in Hours/Days mode")
            if data['hours'] is None or data['days'] is None:
                raise serializers.ValidationError("Must set hours and days in Hours/Days mode. Put 0 to disable")
        elif mode == 'SCH':
            if data['hours'] is not None:
                raise serializers.ValidationError("Should not set hours in scheduled days mode")
            if data['days'] is not None:
                raise serializers.ValidationError("Should not set  days in scheduled days mode")
            if data['scheduled_days'] is None:
                raise serializers.ValidationError("Must set scheduled days in Scheduled days mode")
        return data



class MaintenanceInfoImageSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.MaintenanceInfoImage
        fields = ('image',)


class MaintenanceInfoSerializer(serializers.ModelSerializer):
    equipment = EquipmentSerializer(read_only=True)
    equipment_id = serializers.PrimaryKeyRelatedField(
        queryset=models.Equipment.objects.all(),
        source='equipment',
        write_only=True
    )
    images = MaintenanceInfoImageSerializer(source='info_images', many=True, read_only=True)

    class Meta:
        model = models.MaintenanceInfo
        fields = '__all__'
    
    def create(self, validated_data):
        image_data = self.context.get('request').data.getlist('images')
        with transaction.atomic():
            info = models.MaintenanceInfo.objects.create(
                equipment=validated_data.get('equipment'),
                maintenance_date=validated_data.get('maintenance_date'),
                notes=validated_data.get('notes'),
                genhours=validated_data.get('genhours')
                )
            for img in image_data:
                models.MaintenanceInfoImage.objects.create(
                    maintenance_info=info,
                    image=img
                )
            return info

            
class EquipmentMaintenanceSummarySerializer(serializers.Serializer):
    equipment = serializers.CharField()
    maintenance_mode = serializers.CharField()
    latest_maintenance_genhours = serializers.IntegerField()
    next_maintenance_date = serializers.DateField()
    next_maintenance_genhours = serializers.IntegerField()
