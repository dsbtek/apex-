from rest_framework import status
from rest_framework import generics
from rest_framework.views import APIView

from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from drf_spectacular.utils import extend_schema

from backend import models
from . import serializer
from .. import utils
from ..tanks.serializer import TankSerializer


class EquipmentList(generics.ListCreateAPIView):
    # List all Registered equipments and create new equipment returning all avaliable equipments

    serializer_class = serializer.EquipmentSerializer
    queryset = models.Equipment.objects.all()   

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data, response.status_code)


class EquipmentCompanyList(generics.ListAPIView):
    # List all equipment in a company
    
    serializer_class = serializer.EquipmentSerializer
    def get_queryset(self):
        company_pk = self.kwargs.get('pk')
        queryset = models.Equipment.objects.filter(site__Company__Company_id=company_pk)
        return queryset

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data)


class EquipmentCompanies(APIView):
    # List all equipment in multiple companies

    serializer_class = serializer.EquipmentSerializer

    def get(self, request):
        company_ids = request.GET['company'].split(',')
        queryset = models.Equipment.objects.filter(
            site__Company__Company_id__in=company_ids)

        serialized = serializer.EquipmentSerializer(queryset, many=True)
        return utils.CustomResponse.Success(serialized.data)



class EquipmentSiteList(generics.ListAPIView):
    """
        Return all equipments in a site
    """
    serializer_class = serializer.EquipmentSerializer
    def get_queryset(self):
        site_pk = self.kwargs['pk']
        queryset = models.Equipment.objects.filter(site__Site_id=site_pk)
        url_param = self.request.query_params.get('maintenance', None)
        if url_param is not None:
            if url_param == '1':
                queryset = queryset.filter(equipment_type='GEN')
        return queryset

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data)

class SitesEquipmentList(APIView):
    serializer_class = serializer.EquipmentSerializer

    def post(self, request):
        try:
            site_ids = request.data
            serializer = self.serializer_class(models.Equipment.objects.filter(site__Site_id__in=site_ids), many=True)
            return utils.CustomResponse.Success(serializer.data, status.HTTP_200_OK)
        except Exception as e:
            return utils.CustomResponse.Failure(e)



class EquipmentSitegroupList(generics.GenericAPIView):
    serializer_class = serializer.EquipmentSerializer

    def get_queryset(self):
        ids = self.kwargs.get('site_ids')
        queryset = models.Equipment.objects.filter(site__Site_id__in=ids)
        return queryset

    def post(self, request, *args, **kwargs):
        site_ids = request.data.get('site_ids', None)
        if site_ids:
            self.kwargs['site_ids'] = site_ids
            queryset = self.get_queryset()
            serializer_data = serializer.EquipmentSerializer(queryset, many=True)
            return utils.CustomResponse.Success(serializer_data.data)
        return utils.CustomResponse.Failure('No site_ids passed')


class EquipmentDetail(generics.RetrieveUpdateDestroyAPIView):
    """
        Retrieve Equipment Details
        Update an Equipment Details
        Delete an Equipment
    """
    serializer_class = serializer.EquipmentSerializer
    queryset = models.Equipment.objects.all()

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data, response.status_code)
    
    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        response = super().update(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data, response.status_code)

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data, response.status_code)


class EligibleTanks(generics.ListAPIView):
    '''
    Eligibke tanks for an equipment is defined as
    all tanks belonging to the equipment's site and
    containing the equipment's product
    '''
    serializer_class = TankSerializer
    def get_queryset(self):
        equipment_pk = self.kwargs.get('pk')
        equipment = get_object_or_404(models.Equipment, pk=equipment_pk)
        #filter queryset by product
        queryset = models.Tanks.objects.filter(
            Site__Site_id=equipment.site.Site_id,
            Product__Product_id=equipment.product.Product_id)
        return queryset

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data)


class EquipmentMapTanks(APIView):
    serializer_class = serializer.EquipmentMapTanksSerializer

    def get_object(self):
        equipment_pk = self.kwargs.get('pk')
        obj = get_object_or_404(models.Equipment, pk=equipment_pk)
        return obj
    
    @extend_schema(responses=serializer.EquipmentSerializer)
    def put(self, request, *args, **kwargs):
        serialized = self.serializer_class(data=request.data)
        if serialized.is_valid():
            serialized_data = serialized.validated_data
            equipment = self.get_object()
            #clear all tanks in tankgroup
            equipment.source_tanks.clear()
            tank_ids = serialized_data['Tank']
            if tank_ids:
                tanks = models.Tanks.objects.filter(pk__in=tank_ids)
                equipment.source_tanks.add(*tanks)
                equipment.save()
            response_serializer = serializer.EquipmentSerializer(equipment)
            return utils.CustomResponse.Success(response_serializer.data)
        else:
            return utils.CustomResponse.Failure("Invalid form-data")

class EquipmentTanks(generics.RetrieveAPIView):
    serializer_class = serializer.EquipmentSerializer
    queryset = models.Equipment.objects.all()
    
    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data, response.status_code)


class EquipmentResetTotalisers(APIView):
    serializer_class = serializer.EquipmentResetTotaliserSerializer

    @extend_schema(responses=serializer.EquipmentSerializer)
    def post(self, request, *args, **kwargs):
        serialized = self.serializer_class(data=request.data)
        if serialized.is_valid():
            data = serialized.validated_data
            eq = models.Equipment.objects.get(pk=data['equipment'].pk)
            eq.totaliser_hours = data['totaliser_hours']
            eq.totaliser_litres = data['totaliser_litres']
            eq.save()
            response_serializer = serializer.EquipmentSerializer(eq)
            return utils.CustomResponse.Success(response_serializer.data)
        else:
            return utils.CustomResponse.Failure(serialized.errors)
