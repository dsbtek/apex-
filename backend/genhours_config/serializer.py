from rest_framework import serializers
from backend import models

from ..sites.serializer import SiteSerializerWithOnlyName

class GenHoursConfigSerializer(serializers.ModelSerializer):
	site = SiteSerializerWithOnlyName(read_only=True)
	site_id = serializers.PrimaryKeyRelatedField(
		queryset=models.Sites.objects.all(),
		source='site',
		write_only=True
	)
	class Meta:
		model = models.SiteGenHoursConfiguration
		fields = "__all__"