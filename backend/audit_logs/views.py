from mmap import PAGESIZE
from rest_framework import status
from rest_framework import generics
from auditlog.models import LogEntry
from .. import utils
from . import serializer
from rest_framework.views import APIView
from ..custom_pagination import SmallDefaultPagination

class AllLogList(generics.ListAPIView):
    # I decided not to log password reset object/ because of the risk of the api
    # exposing user reset tokens;a walkaround may be to exclude the PasswordReset obj here in query;
    serializer_class = serializer.AuditLogSerializer
    queryset = LogEntry.objects.all()
    # pagination_class = SmallDefaultPagination
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data, response.status_code)

class AuditLogTimeStamp(APIView):
  
    def get(self, request):
        time_stamp = request.GET['period'].split(",")

        query = LogEntry.objects.filter(timestamp__range=time_stamp)
        print('query', query)
        returned = serializer.AuditLogSerializer(query, many=True)
        return utils.CustomResponse.Success(returned.data, status=status.HTTP_200_OK)