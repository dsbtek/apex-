from rest_framework import status
from rest_framework.views import APIView
from rest_framework import generics

from django.shortcuts import get_object_or_404

from drf_spectacular.utils import extend_schema, OpenApiParameter, extend_schema_serializer
from drf_spectacular.types import OpenApiTypes

from backend import models
from .. import utils 
from . import serializer
from .deviceConfig import RemoteConfig
# import redis


class GenerateDevice(generics.ListCreateAPIView):
    serializer_class = serializer.UniqueAddressTrackerSerializer
    queryset = models.UniqueAddressTracker.objects.all()

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data, response.status_code)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data, response.status_code)


class DeviceList(generics.ListCreateAPIView):
    serializer_class = serializer.DeviceSerializer
    queryset = models.Devices.objects.exclude(Company__Owned=True)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data, response.status_code)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data, response.status_code)

class AllDeviceList(generics.ListAPIView):
    serializer_class = serializer.DeviceSerializer
    queryset = models.Devices.objects.all()

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data, response.status_code)


class DeviceByCompanyList(generics.ListAPIView):
    serializer_class = serializer.DeviceSerializer

    def get_queryset(self):
        pk = self.kwargs['pk']
        queryset = models.Devices.objects.filter(Company__Company_id=pk, Active=True)
        url_param = self.request.query_params.get('available', None)
        if url_param is not None:
            if url_param == '1':
                queryset = queryset.filter(site__isnull=True)
                return queryset
            elif url_param == '0':
                queryset = queryset.filter(site__isnull=False)
                return queryset
        return queryset

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data, response.status_code)


class DeviceByCompanies(APIView):
    serializer_class = serializer.DeviceSerializer

    def get(self, request):
        company_ids = request.GET['company'].split(',')
        queryset = models.Devices.objects.filter(
            Company__Company_id__in=company_ids, Active=True)
        url_param = self.request.query_params.get('available', None)
        if url_param is not None:
            if url_param == '1':
                queryset = queryset.filter(site__isnull=True)
                
            elif url_param == '0':
                queryset = queryset.filter(site__isnull=False)
        serialized = serializer.DeviceSerializer(queryset, many=True)
        return utils.CustomResponse.Success(serialized.data)


class PumpDeviceByCompanyList(generics.ListAPIView):
    serializer_class = serializer.DeviceSerializer

    def get_queryset(self):
        pk = self.kwargs['pk']
        queryset = models.Devices.objects.filter(Company__Company_id=pk, Active=True, ForPump=True)
        url_param = self.request.query_params.get('available', None)
        if url_param is not None:
            if url_param == '1':
                queryset = queryset.filter(site__isnull=True)
                return queryset
            elif url_param == '0':
                queryset = queryset.filter(site__isnull=False)
                return queryset
        return queryset

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data, response.status_code)


class DeviceDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a Device instance.
    """
    serializer_class = serializer.DeviceSerializer
    queryset = models.Devices.objects.all()

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


class DeviceActivationDetail(APIView):
    serializer_class = serializer.DeviceActivationDetailSerializer

    @extend_schema(responses=serializer.DeviceSerializer)
    def post(self, request, **kwargs):
        serialized = self.serializer_class(data=request.data)
        if serialized.is_valid():
            data = serialized.validated_data

            device_pk = kwargs.pop('pk')
            company_id = kwargs.pop('id')

            device = get_object_or_404(models.Devices, pk=device_pk)
            company = models.Companies.objects.get(pk=company_id)
            device.Company = company

            if data['action'] == 'activate':
                device.Active = True
            elif data['action'] == 'deactivate':
                device.Active = False
            
            device.save()

            serialized = serializer.DeviceSerializer(device)
            return utils.CustomResponse.Success(serialized.data)
        else:
            return utils.CustomResponse.Failure("Invalid form-data")


class RegisteredDevicesOnlineStatusRedis(APIView):

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="all",
                required=True,
                type=str
            )
        ],
        responses=serializer.DeviceRedisOnlineSerializer
    )
    def get(self, request):
        mode = request.query_params.get('all', None)
        '''
        response in the form of
        {
            'Serial Number',
            'MAC Address',
            'SiteID',
            'Site Name',
            'Last Seen'
        }
        '''
        if mode is None: #Non-E360 Owned request
            devices = models.Devices.objects.filter(Company__Owned=False, site__isnull=False, Active=True)
        else:
            devices = models.Devices.objects.filter(site__isnull=False, Active=True)
        serialized = serializer.DeviceRedisOnlineSerializer(devices, many=True)
        return utils.CustomResponse.Success(serialized.data)


class ADC_Sensor_Configuration(APIView):
    serializer_class = serializer.ADCSensorSerializer

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def post(self, request, *args, **kwargs):
        serialized = self.serializer_class(data=request.data)
        if serialized.is_valid():
            data = serialized.validated_data
            mac_address = data.get('mac_address', None)
            if mac_address:
                device = get_object_or_404(models.Devices, Device_unique_address=mac_address)
                config = device.adc_sensor_count
                return utils.CustomResponse.Success(config)
            return utils.CustomResponse.Failure('No device MAC address specified')
        else:
            return utils.CustomResponse.Failure("Invalid form-data")


class Tank_Configuration_Details(APIView):
    serializer_class = serializer.ADCSensorSerializer

    @extend_schema(responses=serializer.TankDatailsSerializer(many=True))
    def post(self, request, *args, **kwargs):
        data =  request.data
        mac_address = data.get('mac_address', None)
        if mac_address:
            device = get_object_or_404(models.Devices, Device_unique_address=mac_address)
            config = device.tank_config_details
            return utils.CustomResponse.Success(config)
        return utils.CustomResponse.Failure('No device MAC address specified')


#WORK ON DEVICE REMOTE CONFIGURATION MODULE
class RemoteConfigView(APIView):
    permission_classes = ()
    authentication_classes = ()
    serializer_class = serializer.ADCSensorSerializer

    @extend_schema(responses=serializer.TankDatailsSerializer)
    def post(self, request, *args, **kwargs):
        serialized = self.serializer_class(data=request.data)
        if serialized.is_valid():
            data = serialized.validated_data
            mac_address = data.get('mac_address', None)
            if mac_address:
                #get device and confirm the device is connected to a site
                device = get_object_or_404(models.Devices, Device_unique_address=mac_address)
                if device.available:
                    return utils.CustomResponse.Failure('This device is not connected to a site')
                #only connected devices will fetch config
                config_object = RemoteConfig(device)
                data = config_object.get_configurations()
                return utils.CustomResponse.Success(data)
            return utils.CustomResponse.Failure('No device MAC address specified')
        else:
            return utils.CustomResponse.Failure('Invalid form-data')
