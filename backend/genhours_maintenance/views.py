import datetime as dt

from django.shortcuts import get_object_or_404
from django.db import transaction

from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.parsers import MultiPartParser

from drf_spectacular.utils import extend_schema

from backend import models
from .. import utils
from .serializer import (MaintenanceConfigSerializer, MaintenanceInfoSerializer,
                        MaintenanceInfoImageSerializer, EquipmentMaintenanceSummarySerializer)
from ..genhours_logs.utils import EquipmentDashboardFactory


class NewMaintenanceConfig(generics.ListCreateAPIView):
    serializer_class = MaintenanceConfigSerializer
    queryset = models.MaintenanceConfig.objects.all()

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data, status=201)

class MaintenanceConfigDetail(generics.RetrieveUpdateAPIView):
    serializer_class = MaintenanceConfigSerializer
    queryset = models.MaintenanceConfig.objects.all()

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data)

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        response = super().update(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data, response.status_code)


class NewMaintenanceInfo(APIView):
    serializer_class = MaintenanceInfoSerializer

    @extend_schema(responses=MaintenanceInfoSerializer)
    def post(self, request, *args, **kwargs):
        data = request.data
        serialized = self.serializer_class(data=data, context={'request': request})
        if serialized.is_valid(raise_exception=True):
            serialized.save()
        return utils.CustomResponse.Success(serialized.data, status=201)


class MaintenanceInfoRecords(APIView):
    
    @extend_schema(responses=MaintenanceInfoSerializer)
    def get(self, request, *args, **kwargs):
        equipment_pk = self.kwargs.get('pk')
        queryset = models.MaintenanceInfo.objects.filter(equipment__id=equipment_pk)
        serializer = MaintenanceInfoSerializer(queryset, many=True)
        return utils.CustomResponse.Success(serializer.data)


class EquipmentMaintenanceSummary(APIView):

    @extend_schema(responses=EquipmentMaintenanceSummarySerializer)
    def get(self, request, *args, **kwargs):
        equipment_pk = kwargs.get('pk')
        equipment = get_object_or_404(models.Equipment, pk=equipment_pk)
        
        payload = EquipmentDashboardFactory(equipment).create_maintenance_dashboard().aggregate()
        return utils.CustomResponse.Success(payload)