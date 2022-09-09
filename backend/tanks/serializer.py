import redis
import json
import os

from django.conf import settings

from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from backend import models
from ..sites.serializer import SiteSerializer
from .utils import is_valid_file_type

from ..utils import convert_csv_to_json
from decouple import config




class TankSerializer(serializers.ModelSerializer):
    Site = SiteSerializer(read_only=True)
    Site_id = serializers.PrimaryKeyRelatedField(
        queryset=models.Sites.objects.all(), source='Site', write_only=True)

    class Meta:
        model = models.Tanks
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=model.objects.all(),
                fields=('Site', 'Tank_controller', 'Controller_polling_address', 'Tank_index'),
                message='Tank index already assigned'
            )
        ]
    '''
    Validate the following:
    1. Calibration_chart is valid file
    2. Site's number of tanks
    '''
    def validate_CalibrationChart(self, value):
        if not is_valid_file_type(value):
            raise serializers.ValidationError('Only csv files are allowed')
        return value

    def create(self, validated_data):
        #if tank's site has exceeded number of tanks, raise error
        site = validated_data.get('Site', None)
        if site and site.tank_count >= site.Number_of_tanks:
            raise serializers.ValidationError('Tank Site has reached limit for registered number of tanks')
        return models.Tanks.objects.create(**validated_data)

    def save(self, **kwargs):
        tank = super().save(**kwargs)
        if tank.CalibrationChart: #if tank CalibrationChart is set, update redis value
            # inside redis
            key = 'Tank'+str(tank.pk)
            red = redis.Redis(host=config('REDIS_HOST'), port=config('REDIS_PORT'), db=0, charset="utf-8", decode_responses=True)
            try:
                chart_path = os.path.join(settings.MEDIA_ROOT, tank.CalibrationChart.name)
                json_chart = convert_csv_to_json(chart_path)
            except Exception as err:
                print(err)
            else:
                # setting tank chart
                red.hset('tanks_calibration_chart', key, json.dumps(json_chart))
        return tank

class GetTankIDsSerializer(serializers.Serializer):
    site = serializers.IntegerField()
        

class GetTankResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Tanks
        fields = ['Tank_id', 'Name']