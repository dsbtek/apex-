from rest_framework import generics

from backend import models

from .serializer import GenHoursConfigSerializer
from .. import utils


class GenHoursConfig(generics.ListCreateAPIView):
    serializer_class = GenHoursConfigSerializer
    queryset = models.SiteGenHoursConfiguration.objects.all()

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data, status=201)


class GenHoursConfigDetail(generics.RetrieveUpdateAPIView):
    serializer_class = GenHoursConfigSerializer
    queryset = models.SiteGenHoursConfiguration.objects.all()

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data)

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        response = super().update(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data, response.status_code)