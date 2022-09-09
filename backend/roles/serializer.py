from rest_framework import serializers
from backend import models

class RoleSerializer(serializers.ModelSerializer):
	
	class Meta:
		model = models.Role
		fields = '__all__'