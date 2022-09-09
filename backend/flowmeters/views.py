from rest_framework import status
from rest_framework.views import APIView
from rest_framework import generics

from django.shortcuts import get_object_or_404

from drf_spectacular.utils import extend_schema

from backend import models
from .serializer import FlowMeterSerializer, FlowmeterActivationDetailSerializer
from .. import utils


class FlowmeterList(generics.ListCreateAPIView):
    serializer_class = FlowMeterSerializer
    queryset = models.Flowmeter.objects.all()

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data, response.status_code)

class FlowmeterCompanyList(generics.ListAPIView):
    serializer_class = FlowMeterSerializer
    def get_queryset(self):
        company_pk = self.kwargs['pk']
        queryset = models.Flowmeter.objects.filter(site__Company__Company_id=company_pk)
        return queryset

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data)
    

class FlowmeterCompanies(APIView):
    serializer_class = FlowMeterSerializer

    def get(self, request):
        company_ids = request.GET['company'].split(',')
        queryset = models.Flowmeter.objects.filter(
            site__Company__Company_id__in=company_ids)
        
        serializer = FlowMeterSerializer(queryset, many=True)
        return utils.CustomResponse.Success(serializer.data)


        
class FlowmeterDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = FlowMeterSerializer
    queryset = models.Flowmeter.objects.all()

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


class FlowmeterActivationDetail(APIView):
    serializer_class = FlowmeterActivationDetailSerializer

    @extend_schema(responses=FlowMeterSerializer)
    def post(self, request, **kwargs):
        serialized = self.serializer_class(data=request.data)
        if serialized.is_valid():
            serialized_data = serialized.validated_data

            flowmeter_pk = kwargs.pop('pk')
            site_id = kwargs.pop('id')

            flowmeter = get_object_or_404(models.Flowmeter, pk=flowmeter_pk)
            site = models.Sites.objects.get(pk=site_id)
            flowmeter.site = site

            if serialized_data['action'] == 'activate':
                flowmeter.active = True
            elif serialized_data['action'] == 'deactivate':
                flowmeter.active = False
            
            flowmeter.save()

            serializer = FlowMeterSerializer(flowmeter)
            return utils.CustomResponse.Success(serializer.data)
        else:
            return utils.CustomResponse.Failure("Invalid form-data", status=status.HTTP_400_BAD_REQUEST)


class FlowmeterBySiteList(generics.ListAPIView):
    serializer_class = FlowMeterSerializer

    def get_queryset(self):
        pk = self.kwargs['pk']
        queryset = models.Flowmeter.objects.filter(site__Site_id=pk, active=True)
        url_param = self.request.query_params.get('available', None)
        if url_param is not None:
            if url_param == '1':
                queryset = queryset.filter(equipment__isnull=True)
            elif url_param == '0':
                queryset = queryset.filter(equipment__isnull=False)
        return queryset

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data, response.status_code)
