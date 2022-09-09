from rest_framework import serializers
from backend import models

class ProbeSerializer(serializers.ModelSerializer):
	class Meta:
		model = models.Probes
		fields = "__all__"
		
class ProbeChartResponseSerializer(serializers.Serializer):
	data = serializers.JSONField()
