
from rest_framework.views import APIView
from django.db import connection
from .. import utils
import json
from rest_framework import status

from datetime import datetime

from . import utils as u
from . import queries as q


class TrendReadings(APIView):

    def post(self, request, *args, **kwargs):
        # default_date = datetime.datetime.now().strftime('%Y-%m-%d')
        tank_ids = request.data.get('tanks', None)
        start_date = request.data.get('start')
        end_date = request.data.get('end')

        if len(tank_ids) == 0:
            return utils.CustomResponse.Failure("empty tank list", status=status.HTTP_400_BAD_REQUEST)
        if datetime.strptime(start_date, '%Y-%m-%d %H:%M') > datetime.strptime(end_date, '%Y-%m-%d %H:%M'):
            return utils.CustomResponse.Failure("Invalid date and time range", status=status.HTTP_400_BAD_REQUEST)

        if tank_ids:
            with connection.cursor() as c:
                query = q.get_trend_data
                c.execute(query, [tuple(tank_ids), start_date, end_date])
                data = u.dictfetchall(c)
            
            processed_data = u.processTrendData(data)
            return utils.CustomResponse.Success(processed_data)
