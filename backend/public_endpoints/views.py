from django.db import connection

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from drf_spectacular.utils import extend_schema

from backend import models
import datetime
from datetime import datetime as dt
from .serializers import TankSerializer, GetDeliveriesByTanksSerializer, GetTankInventoryResponseSerializer, GetTankProductResponseSerializer, GetDailyConsumptionReportSerializer, GetDailyConsumptionResponseSerializer, GenerateAPITokenResponseSerializer
from . import helpers 
from .. import utils
from ..reports.custom_reports import delivery_report_generator, consumption_report_generator


class GetTankInventory(APIView):
	permission_classes = ()
	authentication_classes = ()

	@extend_schema(responses=GetTankInventoryResponseSerializer)
	def get(self, request):
		token_status, station_id = helpers.request_middleware(request)
		if token_status:
			return utils.CustomResponse.Failure('Invalid API token')
		if station_id != None:
			
			with connection.cursor() as c:
				query = """
				        SELECT 
				            l.pv AS tankVolume,
				            l.sv AS tankHeight,
				            l.read_at AS last_updated_time,
				            bs.Name AS siteName,
				            bt.Name AS 'tankName',
				            bt.Capacity AS capacity,
				            bp.Name AS product
				        FROM
				            atg_primary_log l
				            JOIN backend_devices bd ON bd.Device_unique_address = l.device_address
				            JOIN backend_sites bs ON bs.Device_id = bd.Device_id
				            JOIN backend_tanks bt ON bt.Site_id = bs.Site_id and
				            bt.Tank_index = l.tank_index and bt.Controller_polling_address = l.multicont_polling_address
				            and bt.Tank_controller = l.Controller_type
				            JOIN backend_products bp ON bp.Product_id = bt.Product_id
				        WHERE
				            bs.Site_id = %s
				            ORDER BY l.read_at DESC
				            LIMIT 5000;

				    	"""
				c.execute(query, [station_id])
				data = self.filter_for_latest_records(helpers.dictfetchall(c))
			return utils.CustomResponse.Success(data)
		return utils.CustomResponse.Failure('API key missing')

	def filter_for_latest_records(self, records):

	    result = []
	    seen_tanks = {}

	    for record_dict in records:
	        # Parse records for the latest tank levels.
	        # Records are in reverse chronological order.
	        # This implies the first volume reading for a tank is its latest volume
	        tank_name = record_dict['tankName']

	        tank_ref = "{}".format(tank_name)

	        if tank_ref in seen_tanks:
	            continue
	        else:
	            seen_tanks[tank_ref] = True

	        volume = float(record_dict["tankVolume"])
	        tank_capacity = record_dict["capacity"]
	        record_dict["Fill %"] = round((volume * 100 / tank_capacity), 2)

	        record_dict["tankVolume"] = "{0:.3f}".format(float(record_dict["tankVolume"]))

	        record_dict["tankHeight"] = "{0:.3f}".format(float(record_dict["tankHeight"]))

	        result.append(record_dict)

	    return result


class GetTankProductList(APIView):
	permission_classes = ()
	authentication_classes = ()

	@extend_schema(responses=GetTankProductResponseSerializer)
	def get(self, request):
		token_status, station_id = helpers.request_middleware(request)
		if token_status:
			return utils.CustomResponse.Failure('Invalid API token')

		if station_id != None:
			queryset = models.Tanks.objects.filter(Site__Site_id=station_id)
			serializer = TankSerializer(queryset, many=True)
			return utils.CustomResponse.Success(serializer.data)
		return utils.CustomResponse.Failure('API key missing')


class GetDailyConsumptionReport(APIView):
	permission_classes = ()
	authentication_classes = ()
	serializer_class = GetDailyConsumptionReportSerializer

	@extend_schema(responses=GetDailyConsumptionResponseSerializer)
	def get(self, request):
		token_status, station_id = helpers.request_middleware(request)
		report_type = 'Daily'
		if token_status:
			return utils.CustomResponse.Failure('Invalid API token')

		serialized = self.serializer_class(data=request.data)
		if serialized.is_valid():
			serialized_data = serialized.validated_data
			if station_id != None:
				start_date = serialized_data['start']
				end_date = serialized_data['end']
				if start_date != None and end_date != None:
					tank_ids = helpers.get_tanks_in_a_site(station_id)
					data = consumption_report_generator(report_type, start_date, end_date, tank_ids)
					data = data[::-1]
					return utils.CustomResponse.Success(data)
				else:
					return utils.CustomResponse.Failure('Start and end dates not provided')
			return utils.CustomResponse.Failure('API key missing')
		else:
			return utils.CustomResponse.Failure('Invalid form-data', status=status.HTTP_400_BAD_REQUEST)


class GetDeliveries(APIView):
	permission_classes = ()
	authentication_classes = ()
	def get(self, request):
		token_status, station_id = helpers.request_middleware(request)
		if token_status:
			return utils.CustomResponse.Failure('Invalid API token')

		if station_id != None:
			start_time = request.query_params.get('start', None)
			end_time = request.query_params.get('end', None)

			if start_time != None and end_time != None:
				tank_ids = helpers.get_tanks_in_a_site(station_id)
				data = delivery_report_generator(start_time, end_time, tank_ids)
				data = data[::-1]
				return utils.CustomResponse.Success(data)
			else:
				return utils.CustomResponse.Failure('Start and end dates not provided')
		return utils.CustomResponse.Failure('API key missing')

class GetDeliveriesByTanks(APIView):
	permission_classes = ()
	authentication_classes = ()
	serializer_class = GetDeliveriesByTanksSerializer
	
	def get(self, request):
		serialized = self.serializer_class(data=request.data)
		if serialized.is_valid():
			serialized_data = serialized.validated_data

			token_status, station_id = helpers.request_middleware(request)
			if token_status:
				return utils.CustomResponse.Failure('Invalid API token')

			if station_id != None:
				tank_name = serialized_data['tank_name']
				start_time = serialized_data['start']
				end_time = serialized_data['end']

				if tank_name != None and start_time != None and end_time != None:
					tank_name = tank_name.replace('_', ' ')
					data = helpers.delivery_report_generator(start_time, end_time, station_id, tank_name)
					return utils.CustomResponse.Success(data)
				else:
					return utils.CustomResponse.Failure('Missing query parameter(s)')
			return utils.CustomResponse.Failure('API key missing')
		else:
			return utils.CustomResponse.Failure('Invalid form-data')

class GenerateAPIToken(APIView):
	permission_classes = ()
	authentication_classes = ()

	@extend_schema(responses=GenerateAPITokenResponseSerializer)
	def get(self, request, pk):
		keygenClass = helpers.APIKEYGenerator()
		key = keygenClass.key_generator()
		token = keygenClass.generate_encrypted_token(key, pk)
		return utils.CustomResponse.Success(token)


class GetOnlineDevices(APIView):
	permission_classes = ()
	authentication_classes = ()
	def get(self, request):
		# Get Serial number, Device address, Site name, Seen last, Last read time
		token_status, station_id = helpers.request_middleware(request)
		if token_status:
			return utils.CustomResponse.Failure('Invalid API token')
		if station_id and station_id == 1:
			with connection.cursor() as c:
				query = """
						SELECT DISTINCT
							d.Name AS 'Serial Number',
							d.Device_unique_address AS 'MAC Address',
							s.Site_id AS 'SiteID',
							d.Site AS 'Site Name',
							h.last_time_online AS 'Last Seen'
						FROM
							device_heartbeats h JOIN backend_devices d ON h.device_mac_address = d.Device_unique_address
							JOIN backend_sites s ON d.Site = s.Name JOIN backend_companies c on c.Company_id = s.Company_id
						WHERE c.Owned = 0  
						ORDER BY h.last_time_online DESC;
				"""
				c.execute(query)
				data = helpers.dictfetchall(c)
			return utils.CustomResponse.Success(self.format_records(data))
		return utils.CustomResponse.Failure('API key missing')
	
	def format_records(self, data):
		result = {
			"offline": [],
			"online": []
		}
		for entry in data:
			current_time = dt.now()
			last_seen = entry["Last Seen"]
			date_diff = current_time - last_seen
			duration_in_seconds = date_diff.total_seconds()
			days_diff_list = divmod(duration_in_seconds, 86400)
			days_diff = int(days_diff_list[0])
			hours_diff_list = divmod(days_diff_list[1], 3600)
			hours_diff = int(hours_diff_list[0])
			minutes_diff_list = divmod(hours_diff_list[1], 60)
			minutes_diff = int(minutes_diff_list[0])
			seconds_diff = int(minutes_diff_list[1])
			
			if date_diff < datetime.timedelta(hours=24):
				result["online"].append({
					"serial_number": entry["Serial Number"],
					"device_address": entry["MAC Address"],
					"site_name": entry["Site Name"],
					"last_time_online": entry["Last Seen"],
					"seen_last": "{} days, {} hours, {} minutes, {} seconds".format(days_diff, hours_diff, minutes_diff, seconds_diff)
				})
			else:
				result["offline"].append({
					"serial_number": entry["Serial Number"],
					"device_address": entry["MAC Address"],
					"site_name": entry["Site Name"],
					"last_time_online": entry["Last Seen"],
					"seen_last": "{} days, {} hours, {} minutes, {} seconds".format(days_diff, hours_diff, minutes_diff, seconds_diff)
				})
		result["number_of_sites_monitored"] = len(data)
		result["number_of_online_sites"] = len(result["online"])
		result["number_of_offline_sites"] = len(result["offline"])
		return result
