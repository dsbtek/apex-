from rest_framework import status
from rest_framework.views import APIView
from rest_framework import generics

from drf_spectacular.utils import extend_schema

from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from .serializer import UserSerializer,ModulesSerializer
from .. import utils 
from backend import models


class ModulesList(generics.ListCreateAPIView):
    serializer_class = ModulesSerializer
    queryset = models.Modules.objects.all()

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data, status.HTTP_201_CREATED)


class UserList(generics.ListCreateAPIView):
    """
    List all Users, or create a new user
    """
    serializer_class = UserSerializer
    queryset = get_user_model().objects.exclude(Company__Owned=True)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data, response.status_code)


class AllUserList(generics.ListAPIView):
    serializer_class = UserSerializer
    queryset = get_user_model().objects.all()

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data)


class UserDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a user instance.
    """
    serializer_class = UserSerializer
    queryset = get_user_model().objects.all()

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


class UserByCompany(generics.ListAPIView):
    serializer_class = UserSerializer
    def get_queryset(self):
        company_pk = self.kwargs.get('pk')
        queryset =  get_user_model().objects.filter(Company__pk=company_pk)
        return queryset

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data)


class UserByCompanies(APIView):
    serializer_class = UserSerializer
    def get(self, request):
        company_ids = request.GET['company'].split(',')
        query = get_user_model().objects.filter(Company__in=company_ids)
    
        serializer = UserSerializer(query, many=True)
        return utils.CustomResponse.Success(serializer.data)

class UserActivationDetail(APIView):

    @extend_schema(responses=UserSerializer)
    def post(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk')
        user = get_object_or_404(get_user_model(), pk=pk)
        if user.is_active:
            user.is_active = False
            user.save()
        else:
            user.is_active = True
            user.save()

        serializer = UserSerializer(user)
        return utils.CustomResponse.Success(serializer.data)
