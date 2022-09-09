from rest_framework import generics
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated

from backend import models
from .. import utils 
from .serializer import RoleSerializer

class UserRoleList(generics.ListAPIView):
    #permission_classes = (IsAuthenticated,)
    serializer_class = RoleSerializer
    def get_queryset(self):
        admins = ['Super-admin', 'E360-Admin']
        queryset = models.Role.objects.exclude(Name__in=admins)
        return queryset

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data)


class AllRoleList(generics.ListAPIView):
    #permission_classes = (IsAuthenticated,)
    serializer_class = RoleSerializer
    queryset = models.Role.objects.all()

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data)