from ..companies.serializer import CompanySerializer
from ..roles.serializer import RoleSerializer
from ..sites.serializer import SiteSerializer
from django.contrib.auth import get_user_model
from rest_framework import serializers
from backend import models


class ModulesSerializer(serializers.ModelSerializer):

	class Meta:
		model = models.Modules
		fields = ('module_id', 'module_name')


class UserAccessPermissionsSerializer(serializers.ModelSerializer):

	class Meta:
		model = models.UserAccessPermissions
		fields = ('permission_name', 'read','create','update','delete','module')


class NewUserRoleSerializer(serializers.ModelSerializer):

	class Meta:
		model = models.NewUserRole
		fields = ('Role_id', 'Name','description','role_permission',)





class UserSerializer(serializers.ModelSerializer):
	
	Company = CompanySerializer(read_only=True)
	Role = RoleSerializer(read_only=True)
	Sites = SiteSerializer(read_only=True, many=True)

	Role_id = serializers.PrimaryKeyRelatedField(
		queryset=models.Role.objects.all(),
		source='Role',
		write_only=True)

	Company_id = serializers.PrimaryKeyRelatedField(
		queryset=models.Companies.objects.all(),
		source='Company',
		write_only=True)
		
	Site_id = serializers.ListField(
		child=serializers.IntegerField(write_only=True),
		write_only=True,
		required=False)

	class Meta:
		model = get_user_model()
		exclude = ('password',)

	def create(self, validated_data):
		site_ids = validated_data.pop('Site_id', None)
		user = get_user_model().objects.create_user(**validated_data)
		if site_ids:
			sites = models.Sites.objects.filter(pk__in=site_ids)
			user.Sites.add(*sites)
			user.save()
		return user

	def update(self, instance, validated_data):
		site_ids = validated_data.pop('Site_id', None)
		new_instance = super().update(instance, validated_data)
		if site_ids:
			new_instance.Sites.clear()
			sites = models.Sites.objects.filter(pk__in=site_ids)
			new_instance.Sites.add(*sites)
			new_instance.save()
		return new_instance
		
		