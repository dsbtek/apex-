from rest_framework import status
from rest_framework.views import APIView
from rest_framework import generics

from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes

from django.db import connection
from .serializer import VersionSerializer, DeviceFirmwareUpdateSerializer, DeviceDataSerializer
from .. import utils
from . import sql_queries as q
from backend import models

'''
- Create new version
- List all versions
- Update device expected version
- All devices with their firmware version

Devices should get their expected version from device config
'''


class VersionList(generics.ListCreateAPIView):
    queryset = models.Version.objects.all()
    serializer_class = VersionSerializer

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data, response.status_code)

'''
The two classes below need to be refactored.
Most importantly, the device firmware needs to be managed by Django.
An API should be provided for the device to connect to log their versions
'''
class DeviceFirmwareUpdate(APIView):
    serializer_class = DeviceFirmwareUpdateSerializer

    @extend_schema(responses=OpenApiTypes.STR)
    def post(self, request, *args, **kwargs):
        serialized = self.serializer_class(data=request.data)
        if serialized.is_valid():
            serialized_data = serialized.validated_data
            devices = serialized_data['Device']
            version = serialized_data['Version']
            status = q.update_device_expected_firmware(devices, version)
            if status:
                return utils.CustomResponse.Success("devices updated")
            else:
                return utils.CustomResponse.Failure("Unable to update devices", status=status.HTTP_400_BAD_REQUEST)
        else:
            return utils.CustomResponse.Failure("Invalid Form-data", status=status.HTTP_400_BAD_REQUEST)


class DeviceFirmwareList(generics.ListAPIView):
    
    queryset = models.DeviceFirmwareVersion.objects.select_related('device').filter(device__isnull=False)
    serializer_class = DeviceDataSerializer

    # def get_queryset(self):
    #     valid_device_addresses = models.Devices.objects.all().values_list('Device_unique_address', flat=True)
    #     return models.DeviceFirmwareVersion.objects.filter(device_mac_address__in=valid_device_addresses)


    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data)
