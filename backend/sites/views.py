from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from drf_spectacular.utils import extend_schema

from backend import models
from .. import utils
from .serializer import SiteSerializer, SiteSerializerUpdate


class SiteList(generics.ListCreateAPIView):
    serializer_class = SiteSerializer

    def get_queryset(self):
        queryset = models.Sites.objects.exclude(Company__Owned=True)
        return queryset

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data, response.status_code)


class E360SiteList(generics.ListAPIView):
    serializer_class = SiteSerializer

    def get_queryset(self):
        queryset = models.Sites.objects.all()
        return queryset

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data)


class SiteDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a site instance.
    """

    def get_serializer_class(self):
        if self.request.method == 'PUT':
            return SiteSerializerUpdate
        return SiteSerializer

    queryset = models.Sites.objects.all()

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


class SiteByCompanyList(generics.ListAPIView):
    serializer_class = SiteSerializer

    def get_queryset(self):
        company_pk = self.kwargs.get('pk')
        queryset = models.Sites.objects.filter(
            Company__Company_id=company_pk, Active=True)
        return queryset

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data)


class SiteByCompanies(APIView):
    serializer_class = SiteSerializer

    def get(self,request):
        company_ids = request.GET['company'].split(',')
        queryset = models.Sites.objects.filter(
            Company__Company_id__in=company_ids, Active=True)
        
        serializer = SiteSerializer(queryset, many=True)
        return utils.CustomResponse.Success(serializer.data)



class SiteActivationDetail(APIView):
    '''
    Upon site deactivation,
    deactivate all users for that site
    '''

    @extend_schema(responses=SiteSerializer)
    def post(self, request, *args, **kwargs):
        pk = kwargs.get('pk', None)
        site = get_object_or_404(models.Sites, pk=pk)
        if site.Active:
            site.Active = False
            site.save()
            # deactivate all users in the site
            site.users.update(is_active=False)
        else:
            site.Active = True
            site.save()
            # Activate all users in the company
            site.users.update(is_active=True)

        serializer = SiteSerializer(site)
        return utils.CustomResponse.Success(serializer.data)


class SiteLocationActivationToggle(APIView):

    @extend_schema(responses=SiteSerializer)
    def post(self, request, pk, format=None):
        site = get_object_or_404(models.Sites, pk=pk)
        if site.Location_status:
            site.Location_status = False
            site.save()
        else:
            site.Location_status = True
            site.save()
        serializer = SiteSerializer(site)
        return utils.CustomResponse.Success(serializer.data)
