import csv
from concurrent.futures import ThreadPoolExecutor, as_completed

from rest_framework.views import APIView
from django.http import StreamingHttpResponse, HttpResponse
from .. import utils
from django.db import connection
from backend import models

from . import serializer
from drf_spectacular.utils import extend_schema

from .custom_reports import consumption_report_generator, delivery_report_generator
from . import utils as report_utils


class DownloadStockReport(APIView):
	def post(self, request, *args, **kwargs):
		report_data = request.data.get("data", None)
		if report_data:
			response = HttpResponse(content_type='text/csv')
			response['Content-Disposition'] = 'attachment; filename=stockreport.csv'

			fieldnames = ['Site Name', 'Tank Name', 'Tank Capacity',
							'Tank Volume', 'Tank Height', 'Read Time']

			writer = csv.DictWriter(response, fieldnames=fieldnames)
			writer.writeheader()
			for data in report_data:
				writer.writerow({
				fieldnames[0]: data['Site Name'],
				fieldnames[1]: data['Tank Name'],
				fieldnames[2]: data['Tank Capacity'],
				fieldnames[3]: data['Volume'],
				fieldnames[4]: data['Height'],
				fieldnames[5]: data['Log Time']
				})
			return response
    			
def dictfetchall(cursor):
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def time_format_check(time):
	if len(time.split(" ")) > 1: #If time is full format i.e yyyy-mm-dd hh:mm
		return True
	else:
		return False


class ConsumptionReport(APIView):
	serializer_class = serializer.ConsumptionReportSerializer

	@extend_schema(responses=serializer.ConsumptionResponseSerializer)
	def post(self, request, *args, **kwargs):
		serialized = self.serializer_class(data=request.data)
		if serialized.is_valid():
			serialized_data = serialized.validated_data
			tank_ids = serialized_data['tanks']
			start_date = serialized_data['start'] #Date only
			end_date = serialized_data['end'] #Date only
			report_type = serialized_data['report_type']
			if report_type == 'Daily':
				start_date += ' 00:00'
				end_date += ' 23:59'
			
			data = []

			if tank_ids:
				with ThreadPoolExecutor(max_workers=len(tank_ids) or 1) as executor:
					futures = [executor.submit(
						report_utils.get_consumption_report,
						tank_id, start_date, end_date, report_type) for tank_id in tank_ids]
					for future in as_completed(futures):
						data.extend(future.result())
				return utils.CustomResponse.Success(data)
			else:
				return utils.CustomResponse.Failure('No tank passed')
		else:
			return utils.CustomResponse.Failure('Invalid form-data')


class DeliveryReport(APIView):
	def post(self, request, *args, **kwargs):
		tank_ids = request.data.get('tanks', None)
		start_time = request.data.get('start') + ' 00:00' #Date only
		end_time = request.data.get('end') + ' 23:59'#Date only
		
		data = []

		if tank_ids:
			with ThreadPoolExecutor(max_workers=len(tank_ids) or 1) as executor:
				futures = [executor.submit(
					report_utils.get_delivery_report,
					tank, start_time, end_time) for tank in models.Tanks.objects.filter(pk__in=tank_ids)]
				for future in as_completed(futures):
					data.extend(future.result())

			return utils.CustomResponse.Success(data)
		else:
			return utils.CustomResponse.Failure('No tank passed')
