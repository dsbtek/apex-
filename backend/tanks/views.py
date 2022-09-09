import os
import json
import csv
import redis

from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.conf import settings

from rest_framework import status
from rest_framework import generics
from rest_framework.views import APIView

from drf_spectacular.views import extend_schema
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter

from backend import models
from .serializer import TankSerializer, GetTankIDsSerializer, GetTankResponseSerializer
from .. import utils
from ..file_handler import get_tank_calibration_chart


class TankList(generics.ListCreateAPIView):
    serializer_class = TankSerializer
    queryset = models.Tanks.objects.exclude(Site__Company__Owned=True)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data)

    def create(self, request, *args, **kwargs):

        try:
            if request.data['Density'] == 'undefined':
                request.data['Density'] = None
        except Exception as e:
            pass

        response = super().create(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data, status.HTTP_201_CREATED)


class AllTankList(generics.ListAPIView):
    serializer_class = TankSerializer
    queryset = models.Tanks.objects.all()

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data)


class TankCompanyList(generics.ListAPIView):
    serializer_class = TankSerializer
    def get_queryset(self):
        company_pk = self.kwargs.get('pk')
        queryset = models.Tanks.objects.filter(Site__Company__Company_id=company_pk)
        return queryset

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data)


class TankCompanies(generics.ListAPIView):
    serializer_class = TankSerializer

    def get(self,request):
        company_ids = request.GET['company'].split(',')
        queryset = models.Tanks.objects.filter(
            Site__Company__Company_id__in=company_ids)
        
        serializer = TankSerializer(queryset, many=True)
        return utils.CustomResponse.Success(serializer.data)


class TankSiteList(generics.ListAPIView):
    serializer_class = TankSerializer
    def get_queryset(self):
        site_pk = self.kwargs.get('pk')
        queryset = models.Tanks.objects.filter(Site__Site_id=site_pk)
        return queryset

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data)


class TankSitegroupList(generics.GenericAPIView):
    serializer_class = TankSerializer
    def get_queryset(self):
        ids = self.kwargs.get('site_ids')
        queryset = models.Tanks.objects.filter(Site__Site_id__in=ids)
        return queryset

    def post(self, request, *args, **kwargs):
        site_ids = request.data.get('site_ids', None)
        if site_ids:
            self.kwargs['site_ids'] = site_ids
            queryset = self.get_queryset()
            serializer = TankSerializer(queryset, many=True)
            return utils.CustomResponse.Success(serializer.data)
        return utils.CustomResponse.Failure('No site_ids passed')



class GetTankList(APIView):
    permission_classes = ()
    authentication_classes = ()

    def get(self, request):
        data = request.GET['site_ids'].split(",")
        tanks = GetTankResponseSerializer(models.Tanks.objects.filter(Site__in=data), many=True)
        return utils.CustomResponse.Success(tanks.data)


class GetTankFromTankGroup(APIView):
    permission_classes = ()
    authentication_classes = ()

    def get(self, request):
        tankgroup_ids = request.GET['tankgroups'].split(",")
        response = list()
        tankgroups = models.TankGroups.objects.filter(Group_id__in=tankgroup_ids)
        for eachTank in tankgroups:
            tanksData = GetTankResponseSerializer(eachTank.Tanks.all(), many=True)
            for each in tanksData.data:
                response.append(each)
        return utils.CustomResponse.Success(response)

class TankActivationDetail(APIView):

    @extend_schema(responses=TankSerializer)
    def post(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk')
        tank = get_object_or_404(models.Tanks, pk=pk)
        if tank.Status :
            tank.Status = False
            tank.save()
        else:
            tank.Status = True
            tank.save()
        #change status of tank on LatestAtgLog table
        try:        
            tank_latest_log = models.LatestAtgLog.objects.get(Tank_id= pk)
            tank_latest_log.Tank_Status = tank.Status
            tank_latest_log.save()
        except models.LatestAtgLog.DoesNotExist:
            pass

        serializer = TankSerializer(tank)
        return utils.CustomResponse.Success(serializer.data)



class TankDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a Tank instance.
    """

    serializer_class = TankSerializer
    queryset = models.Tanks.objects.all()

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data, response.status_code)
    
    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        
        try:
            if request.data['Density'] == 'undefined':
                request.data['Density'] = None
        except Exception as e:
            pass

        response = super().update(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data, response.status_code)

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data, response.status_code)


class GetTankIDs(APIView):
    serializer_class = GetTankIDsSerializer

    @extend_schema(responses=GetTankResponseSerializer(many=True))
    def post(self, request, *args, **kwargs):
        serialized = self.serializer_class(data=request.data)
        if serialized.is_valid():
            site = serialized.validated_data['site']
            if site:
                data = models.Tanks.objects.filter(Site__pk=site).values('Tank_id', 'Name')
                return utils.CustomResponse.Success(data)
            return utils.CustomResponse.Failure('No site id passed')
        else:
            return utils.CustomResponse.Failure('Invalid form data')


class CalibrationChartTemplate(APIView):

    @extend_schema(responses=OpenApiTypes.NONE)
    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="chart_template.csv"'
        writer = csv.writer(response)
        writer.writerow(['height', 'volume'])
        return response


class GetCalibrationChart(APIView):
    '''
    Use caching with redis
    - Try to get chart from redis
    - If cache miss, retrieve chart from server and set in cache,
    - If cache hit, retrieve chart from cache
    '''
    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request, *args, **kwargs):
        tank_pk = self.kwargs.get('pk')
        # key = 'Tank'+str(tank_pk)
        tank = get_object_or_404(models.Tanks, pk=tank_pk) #check if tank has calibration chart uploaded
        try:
            calibration_chart = get_tank_calibration_chart(tank)
        except:
            return utils.CustomResponse.Failure('Could not get calibration chart', status=400)
        else:
            return utils.CustomResponse.Success(calibration_chart)
