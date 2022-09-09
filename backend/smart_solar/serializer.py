
from rest_framework import serializers
from backend import models


class SolarDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SmartSolarData
        fields = "__all__"
