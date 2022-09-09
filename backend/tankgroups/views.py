from rest_framework import status
from rest_framework import generics
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema

from backend import models
from .. import utils 
from .serializer import TankGroupSerializer, TankGroupWithTankSerializer
from ..tanks.serializer import TankSerializer


class TankGroupList(generics.ListCreateAPIView):
    serializer_class = TankGroupSerializer
    queryset = models.TankGroups.objects.exclude(Company__Owned=True)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data, status.HTTP_201_CREATED)


class AllTankGroupList(generics.ListAPIView):
    serializer_class = TankGroupSerializer
    queryset = models.TankGroups.objects.all()

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data)


class TankGroupDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TankGroupSerializer
    queryset = models.TankGroups.objects.all()

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


class TankGroupByCompany(generics.ListAPIView):
    serializer_class = TankGroupSerializer
    def get_queryset(self):
        company_pk = self.kwargs.get('pk')
        queryset = models.TankGroups.objects.filter(Company__Company_id=company_pk)
        return queryset

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data)


class TankGroupByCompanies(APIView):
    serializer_class = TankGroupSerializer

    def get(self, request):
        company_ids = request.GET['company'].split(',')
        queryset = models.TankGroups.objects.filter(
            Company__Company_id__in=company_ids)
        
        serializer = TankGroupSerializer(queryset, many=True)
        return utils.CustomResponse.Success(serializer.data)


class EligibleTanks(generics.ListAPIView):
    '''
    Eligibke tanks for a tankgroup is defined as
    all tanks belonging to the tankgroup's company and
    containing the tankgroup's product
    '''
    serializer_class = TankSerializer
    def get_queryset(self):
        tankgroup_pk = self.kwargs.get('pk')
        tankgroup = get_object_or_404(models.TankGroups, pk=tankgroup_pk)
        #filter queryset by product
        queryset = models.Tanks.objects.filter(
            Site__Company__Company_id=tankgroup.Company.Company_id,
            Product__Product_id=tankgroup.Product.Product_id)
        return queryset

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data)


class TankGroupMapTanks(APIView):

    def get_object(self):
        tankgroup_pk = self.kwargs.get('pk')
        obj = get_object_or_404(models.TankGroups, pk=tankgroup_pk)
        return obj
    
    @extend_schema(responses=TankGroupWithTankSerializer)
    def put(self, request, *args, **kwargs):
        data = request.data
        tankgroup = self.get_object()
        #clear all tanks in tankgroup
        tankgroup.Tanks.clear()
        tank_ids = request.data.get('Tank', None)
        if tank_ids:
            tanks = models.Tanks.objects.filter(pk__in=tank_ids)
            tankgroup.Tanks.add(*tanks)
            tankgroup.save()
        serializer = TankGroupWithTankSerializer(tankgroup)
        return utils.CustomResponse.Success(serializer.data)


class TankGroupTanks(generics.RetrieveAPIView):
    serializer_class = TankGroupWithTankSerializer
    queryset = models.TankGroups.objects.all()
    
    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data, response.status_code)
