from pprint import pprint
from rest_framework import serializers
from backend import models
from .utils import is_valid_file_type
from django.db.models import Q


class CompanySerializerForGroupOnly(serializers.ModelSerializer):
    
    class Meta:
        model = models.Companies
        #fields = '__all__'
        fields = (
            'Company_id', 'Name', 'Country', 'State', 'City', 'Address',
            'number_of_sites', 'Company_type', 'Company_url', 'Company_image',
            'Notes', 'Contact_person_name', 'Contact_person_designation',
            'Contact_person_mail', 'Contact_person_phone', 'Created_at',
            'Updated_at', 'Deleted_at', 'Active', 'Owned', 'genhours_access',
            'smarttank_access', 'smartpump_access', 'group'
        )


class CompanyGroupWithNameSerializer(serializers.ModelSerializer):
    Companies = CompanySerializerForGroupOnly(read_only=True, many=True)
    class Meta:
        model = models.CompanyGroups
        fields = ('Name', 'Companies', 'Status')



class CompanySerializer(serializers.ModelSerializer):
    group = CompanyGroupWithNameSerializer(read_only=True, many=True)
    class Meta:
        model = models.Companies
        #fields = '__all__'
        fields = (
            'Company_id', 'Name', 'Country', 'State', 'City', 'Address',
            'number_of_sites', 'Company_type', 'Company_url', 'Company_image',
            'Notes', 'Contact_person_name', 'Contact_person_designation',
            'Contact_person_mail', 'Contact_person_phone', 'Created_at',
            'Updated_at', 'Deleted_at', 'Active', 'Owned', 'genhours_access', 
            'smarttank_access', 'smartpump_access','group'
        )

    def validate_Company_image(self, value):
        if not is_valid_file_type(value):
            raise serializers.ValidationError('Only png and jpg are allowed')
        return value


class CompanyGroupSerializer(serializers.ModelSerializer):

    Company_id = serializers.ListField(
        child=serializers.IntegerField(write_only=True),
        write_only=True,
        required=False)
    Companies = CompanySerializer(read_only=True, many=True)
    class Meta:
        model = models.CompanyGroups
        fields = ('Group_id', 'Name', 'Companies', 'Status',
                  'created_at', 'updated_at', 'Notes', 'Company_id')
    
    def create(self, validated_data):
        company_ids = validated_data.pop('Company_id', None)
        #check if companys is not already in another group
        if company_ids:
            if models.CompanyGroups.objects.filter(Companies__in=company_ids).exists():
                raise serializers.ValidationError(
                "Some companies already exist in a group")
        company_group = models.CompanyGroups.objects.create(**validated_data)
        if company_ids:
            companys = models.Companies.objects.filter(pk__in=company_ids)
            company_group.Companies.add(*companys)
            company_group.save()
        return company_group
    
    def update(self, instance, validated_data):
        company_ids = validated_data.pop('Company_id', None)
       
        if len(company_ids) == 0:
            new_instance = super().update(instance, validated_data)
            new_instance.Companies.clear()
            new_instance.save()
            return new_instance
        
        if company_ids:
            #check if companys is not already in another group except this
            if models.CompanyGroups.objects.filter(Companies__in=company_ids).exclude(Group_id=instance.Group_id).exists():
                raise serializers.ValidationError(
                    "Some companies already exist in a group")

            new_instance = super().update(instance, validated_data)
            new_instance.Companies.clear()
            companys = models.Companies.objects.filter(pk__in=company_ids)
            new_instance.Companies.add(*companys)
            new_instance.save()
        return new_instance

  
