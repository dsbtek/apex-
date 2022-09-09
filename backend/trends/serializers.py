
from rest_framework import serializers
from backend import models

class TrendSerializers(serializers.ModelSerializer):
    class Meta:
        model = models.Tanks
        fields = "__all__"
