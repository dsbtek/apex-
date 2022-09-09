import os
import csv
import json

from django.db import connection
from django.shortcuts import get_object_or_404
from django.conf import settings

from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.decorators import api_view

from drf_spectacular.utils import extend_schema

from backend import models
from .serializer import ProbeSerializer, ProbeChartResponseSerializer
from .. import utils
 

class ProbeList(generics.ListCreateAPIView):
    serializer_class = ProbeSerializer
    queryset = models.Probes.objects.all()

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data, response.status_code)


class ProbeDetails(generics.RetrieveUpdateDestroyAPIView):

    serializer_class = ProbeSerializer
    queryset = models.Probes.objects.all()

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


class ProbeChart(APIView):

    @extend_schema(responses=ProbeChartResponseSerializer)
    def get(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        chart = get_object_or_404(models.Probes, pk=pk).probe_chart
        if chart:
            chart_path = os.path.join(settings.MEDIA_ROOT, chart.name)
            #transform csv to json
            json_chart = utils.convert_csv_to_json(chart_path)
            return utils.CustomResponse.Success(json_chart)
        else:
            return utils.CustomResponse.Failure('No chart uploaded', status=status.HTTP_400_BAD_REQUEST)