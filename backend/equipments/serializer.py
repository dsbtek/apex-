from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from backend import models
from ..sites.serializer import SiteSerializerWithOnlyName
from ..flowmeters.serializer import FlowMeterSerializerWithName


class EquipmentSerializer(serializers.ModelSerializer):
    site = SiteSerializerWithOnlyName(read_only=True)
    site_id = serializers.PrimaryKeyRelatedField(
        queryset=models.Sites.objects.all(),
        write_only=True,
        source='site')

    flowmeter = FlowMeterSerializerWithName(read_only=True)
    flowmeter_id = serializers.PrimaryKeyRelatedField(
        queryset=models.Flowmeter.objects.all(),
        write_only=True,
        source='flowmeter',
        allow_null=True)
    tank_connection_status = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = models.Equipment
        fields = '__all__' 
        read_only_fields = ['totaliser_hours', 'last_genhours_calculated_time', 'totaliser_litres']
        validators = [
            UniqueTogetherValidator(
                queryset=model.objects.all(),
                fields=('site', 'address'),
                message='Equipment DI address already assigned for this site'
            )
        ]

    def validate(self, data):
        '''
        - if running hours source is FM, a FM must be selected
        - DI, address must be set
        - HYB, both fM and address must be set
        - if litres source is FM, FM must be selected
        '''
        hours_source = data.get('running_hours_source')
        litres_source = data.get('litres_consumed_source')
        flowmeter = data.get('flowmeter', None)
        address = data.get('address', None)
        if hours_source == 'FM' and not flowmeter:
            raise serializers.ValidationError('Running Hours Source is Flowmeter, but no meter was selected') 
        if hours_source == 'DI' and not address:
            raise serializers.ValidationError('Running Hours Source is Direct Integration, but no line address was chosen')
        if hours_source in ['HYB-FM', 'HYB-DI'] and not (flowmeter and address):
            raise serializers.ValidationError('Running Hours Source is HYB, please select FM and line address')
        if litres_source in ['FM', 'HYB-TL', 'HYB-FM'] and not flowmeter:
            raise serializers.ValidationError('Litres consumption Source is Flowmeter, but no meter was selected')
        return data


class EquipmentMapTanksSerializer(serializers.Serializer):
    Tank = serializers.ListField(
        child=serializers.IntegerField()
    )

class EquipmentResetTotaliserSerializer(serializers.Serializer):
    equipment = serializers.PrimaryKeyRelatedField(queryset=models.Equipment.objects.all())
    totaliser_litres = serializers.FloatField()
    totaliser_hours = serializers.FloatField()