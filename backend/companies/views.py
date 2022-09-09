from rest_framework import status
from rest_framework.views import APIView
from rest_framework import generics

from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from drf_spectacular.utils import extend_schema

from backend import models
from .. import utils 
from .serializer import CompanySerializer, CompanyGroupSerializer

class CompanyList(generics.ListCreateAPIView):
    '''
    This view GETS all companies except those owned by E360.
    Ideal way is to use query params to filter a single url.
    But, sticking with this due to backwards compatibility with the frontend
    Will change this once I am ready to refactor frontend
    '''
    serializer_class = CompanySerializer
    queryset = models.Companies.objects.exclude(Owned=True)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data, response.status_code)

        
class AllCompanyList(generics.ListAPIView):
    '''
    This view handles POST & GET requests for companies
    '''
    serializer_class = CompanySerializer
    queryset = models.Companies.objects.all()

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data, response.status_code)


class MultipleCompanyList(APIView):
    '''
    This view handles GET requests, for multliple companies
    '''
    serializer_class = CompanySerializer
    
    def get(self, request):
        company_ids = request.GET['company'].split(',')   
        query = models.Companies.objects.filter(Company_id__in=company_ids)
        serializer = CompanySerializer(query, many=True)
        return utils.CustomResponse.Success(serializer.data)



class CompanyDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a Company instance.
    """
    serializer_class = CompanySerializer
    queryset = models.Companies.objects.all()

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



class CompanyActivationDetail(APIView):
    '''
    The chain of command goes like this:
    Company -> User -> Sites -> Devices -> Tanks
    Deactivation of company means:
    - All users are deactivated
    '''

    @extend_schema(responses=CompanySerializer)
    def post(self, request, *args, **kwargs):
        pk = kwargs.get("pk")
        company = get_object_or_404(models.Companies, pk=pk)
        if company.Active:
            company.Active = False
            company.save()
            #deactivate all users in the company
            company.users.update(is_active=False)
        else:
            company.Active = True
            company.save()
            #Activate all users in the company
            company.users.update(is_active=True)

        serializer = CompanySerializer(company)
        return utils.CustomResponse.Success(serializer.data)


class CompanyGroupList(generics.ListCreateAPIView):
    serializer_class = CompanyGroupSerializer
    queryset = models.CompanyGroups.objects.all()

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data, status.HTTP_201_CREATED)


class CompanyGroupDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a company group instance.
    """
    serializer_class = CompanyGroupSerializer
    queryset = models.CompanyGroups.objects.all()

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


class CompanyGroupActivationDetail(APIView):

    @extend_schema(responses=CompanyGroupSerializer)
    def post(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk')
        company_group = get_object_or_404(models.CompanyGroups, pk=pk)
        if company_group.Status:
            company_group.Status = False
            company_group.save()
        else:
            company_group.Status = True
            company_group.save()

        serializer = CompanyGroupSerializer(company_group)
        return utils.CustomResponse.Success(serializer.data)
