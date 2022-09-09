from ast import Pass
import json
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib import request
import requests
import MySQLdb as mdb
from decouple import config

from django.db import connection
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer
from django.http import HttpResponse, JsonResponse
from rest_framework.parsers import JSONParser

from backend import models
from backend.companies import serializer
from backend.custom_pagination import SQLHeaderLimitOffsetPagination
from backend.tasks import tank_alarm_task, analog_probe_logger
from ..tanks.serializer import TankSerializer
from .. import utils
from .. import sql_helpers
from .. import tank_calibration
from .serializer import LogSerializer, TankLogAnomalySerializer, TankMapSerializer, LatestTankLogSerializer
from . import utils as log_utils
from . import queries as q
from decouple import config

'''
VIEWS
- Regular data logger
- Sensor data logger
- Tank readings
- Tankgroup readings
- Latest tank reading
- Latest tankgroup reading
'''

class DataLogger(APIView):
    '''
    End point for tls and mtc
    Remote devices attempt to store multiple logs to the DB.
    Also, there is a need to do some other processing on the
    latest log for a particular tank asynchronously using celery.
    '''
    permission_classes = ()
    authentication_classes = ()

    def post(self, request, *args, **kwargs):
        log_data = request.data
        
        count_log_fail = 0
        error = "No errors"
        index = 0
        log_lenght = len(log_data)
        for each in log_data:
            if each[2] == None:
                each[2], each[4], message = log_utils.compute_pv(each[5], each[4], each[7])
                if message != "Done":
                    count_log_fail += 1
                    each.append(False)
                    error = message
                else:
                    each.append(True)
            else:
                each.append(True)

        # return utils.CustomResponse.Success(log_data)
        # logs are tuple of tuples; format direct from device sqlite cursor
        # create log instances for each log in request data
        # (local_id, read_at, pv, pv_flag, sv, device_address, multicon_polling_address,
        # tank_index, tc_volume, water, temperature, controller_type)
        # pv == tank_volume(l), sv == tank_height(mm), water == water_height(mm)
        
        try:
            logs = [models.AtgPrimaryLog(local_id=d[0], read_at=d[1],
            pv=d[2], pv_flag=d[3], sv=d[4], device_address=d[5], multicont_polling_address=d[6],
            tank_index=d[7], tc_volume=d[8], water=d[9], temperature=d[10],
            controller_type=d[11], status=d[12], probe_address=d[13], flag_log=d[14]) for d in log_data]
        except IndexError:
            logs = [models.AtgPrimaryLog(local_id=d[0], read_at=d[1],
            pv=d[2], pv_flag=d[3], sv=d[4], device_address=d[5], multicont_polling_address=d[6],
            tank_index=d[7], tc_volume=d[8], water=d[9], temperature=d[10],
            controller_type=d[11], flag_log=d[12]) for d in log_data]    
        #use bulk_create to create multiple new log objects

        '''
        Temporary fix for rerouting logs from
        Abinbev Sagamu and ENYO Pabod 
        to Station Manager
        '''
        route_mac_addresses = ['b8:27:eb:d9:ea:ea', 'b8:27:eb:2c:06:b4']
        log_mac_address = log_data[0][5]
        if log_mac_address in route_mac_addresses:
            try:
                conn = mdb.connect(
                    config("SM_DB_HOST"),
                    config("SM_DB_USER"),
                    config("SM_DB_PASSWORD"),
                    config("SM_DB_NAME")
                    )
                with conn:
                    cur = conn.cursor()
                    query = "INSERT INTO atg_primary_log (local_id, read_at, pv,pv_flag, sv, device_address, multicont_polling_address, tank_index, tc_volume, water, temperature, controller_type ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                    cur.executemany(query, log_data)
            except mdb.Error as e:
                pass
        else:
            models.AtgPrimaryLog.objects.bulk_create(logs)

        #dispatch logs asynchronously to celery task for processing
        #first process the logs to dispatch only the latest logs for each tank,
        #so as not to keep processing older logs when the newer ones have been processed
        filtered_logs = log_utils.filter_for_latest_logs(log_data)
        tank_alarm_task.delay(filtered_logs)
        return utils.CustomResponse.Success("{0} log(s) failed: {1}".format(count_log_fail, error))

class DeliveryLogger(APIView):
    '''
    TLS devices attempt to store multiple deliveries to the DB.
    '''
    permission_classes = ()
    authentication_classes = ()

    def post(self, request, *args, **kwargs):
        log_data = request.data #logs are tuple of tuples; format direct from device sqlite cursor
        #create log instances for each log in request data
        #(local_id, read_at, device_address, polling_address, tank_index,
        # volume, tc_volume, system_start_time, system_end_time,start_height, 
        # end_height, start_volume, end_volume, controller_type)
        logs = [models.Deliveries(local_id=d[0], read_at=d[1],
        device_address=d[2], polling_address=d[3], tank_index=d[4], 
        volume=d[5], tc_volume=d[6], system_start_time=d[7], system_end_time=d[8],
        start_height=d[9], end_height=d[10],start_volume=d[11], end_volume=d[12],
        controller_type=d[13]) for d in log_data]
        
        #use bulk_create to create multiple new log objects
        models.Deliveries.objects.bulk_create(logs)
        return utils.CustomResponse.Success("Done")
        

class SmarthubLogsLogger(APIView):
    permission_classes = ()
    authentication_classes = ()

    def post(self, request, *args, **kwargs):
        log_data = request.data
        try:
            conn = mdb.connect(
                config("SM_DB_HOST"),
                config("SM_DB_USER"),
                config("SM_DB_PASSWORD"),
                config("SM_DB_NAME")
                )
            with conn:
                cur = conn.cursor()
                query = "INSERT INTO atg_primary_log (local_id, read_at, pv,pv_flag, sv, device_address, multicont_polling_address, tank_index, tc_volume, water, temperature, controller_type ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                cur.executemany(query, log_data)
            return utils.CustomResponse.Success("Insertion into db successful")    
        except mdb.Error:
            return utils.CustomResponse.Failure("Error inserting logs to db")
        
    
class SmarthubDeliveriesLogger(APIView):
    permission_classes = ()
    authentication_classes = ()

    def post(self, request, *args, **kwargs):
        log_data = request.data
        try:
            conn = mdb.connect(
                config("SM_DB_HOST"),
                config("SM_DB_USER"),
                config("SM_DB_PASSWORD"),
                config("SM_DB_NAME")
                )
            with conn:
                cur = conn.cursor()
                query = "INSERT INTO deliveries (local_id, read_at, device_address, polling_address, tank_index, volume, tc_volume, system_start_time, system_end_time, start_height, end_height, start_volume, end_volume, controller_type) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                cur.executemany(query, log_data)
            return utils.CustomResponse.Success("Insertion into db successful")    
        except mdb.Error:
            return utils.CustomResponse.Failure("Error inserting logs to db")


class SensorDataLogger(APIView):
    '''
    sensor_data is in the format
    (local_id,controller_address,tank_index,current,voltage,device_address,controller_type,read_at)
    '''
    permission_classes = ()
    authentication_classes = ()
    def post(self, request, *args, **kwargs):
        data = request.data
        analog_probe_logger(data)
        return utils.CustomResponse.Success('Done')


class SpecificTankReading(APIView):
    def get(self, request, *args, **kwargs):
        tank_id = self.kwargs['pk']
        data = q.get_specific_tank_reading(tank_id)
        data = log_utils.update_tank_records(data)
        return utils.CustomResponse.Success(data)
                


class TankReadings(generics.CreateAPIView, log_utils.SqlLogsPaginationCacheMixin):
    pagination_class = SQLHeaderLimitOffsetPagination
    def post(self, request, *args, **kwargs):
        if ( None not in request.data['site']):
            self.ids = request.data['site'] 
        else:
            self.ids = []
            values = models.Sites.objects.filter(Company__in=request.data['Company_ids']).values_list(flat=True)
            for each in values:
                self.ids.append(each)
        self.tank_ids = [each['Tank_id'] for each in request.data.get('tanks', None)]
        if len(self.tank_ids) == 0:
            return utils.CustomResponse.Failure('No tank is passed')
        self.start_date = request.data.get('start')
        self.end_date = request.data.get('end')
        kwargs['count_query'] = q.get_tanklogs_count
        kwargs['data_query'] = q.get_tanklogs
        return self.paginate_and_cache(request, *args, **kwargs)

class AnomalyTankReadingReport(TankReadings):
    pagination_class = SQLHeaderLimitOffsetPagination
    serializer = TankLogAnomalySerializer()
    def get(self,request):
        """
        List all tank logs, or save an anomaly log.
        """

        return HttpResponse()
        
        # req_param ={
        #     "Company_ids":	[1],
        #     "end":	"2022-08-11 09:36",
        #     "site":	[137],
        #     "start":	"2022-07-18 09:36",
        #     "tanks":	[
        #     {
        #         "Name":	"PMS TANK 1",
        #     "Tank_id":	336   
        # }
        # ]
        # }
        # self.ids = req_param['Company_ids']
        # self.tank_ids = req_param['tanks']
        # self.start_date = req_param['start']
        # self.end_date = req_param['end']
        # kwargs['count_query'] = q.get_tanklogs_count
        # kwargs['data_query'] = q.get_tanklogs
        # time_logs = self.paginate_and_cache(request, *args, **kwargs)
        # for time_stamp in range(len(time_logs)):            
        #         prev_time = time_logs[time_stamp - 1]
        #         current_time = time_logs[time_stamp]
        #         t1 = datetime.datetime.strptime(prev_time, "%Y-%m-%d %H:%M:%S").minute
        #         t2 = datetime.datetime.strptime(current_time, "%Y-%m-%d %H:%M:%S").minute
        #         td = datetime.datetime.strptime('2022-06-22 09:46:04', "%Y-%m-%d %H:%M:%S")
        #         time_delta = (t2) - (t1)
        #         if abs(time_delta) > 10:
        #             print(f"anomaly occured by {abs(time_delta)} minutes")
                # print(f"{t1} - {t2}")
                # print(abs(time_delta))


        # atg_log = models.AtgPrimaryLog.objects.all()[:100]
        # log = LogSerializer(atg_log, many=True).data
        # dict = list(log)
        # time_logs = []
        
            # current_time_log = i['read_at']
            # if current_time_log is not None:
            #     prev_time_log = current_time_log
                # print(current_time_log, "curr")
                


        # return JsonResponse(status=200)
        #     return JsonResponse(serializer.errors, status=400)


class RevampedTankReadings(generics.CreateAPIView, log_utils.RevampedSqlLogsPaginationCacheMixin):
    # pagination_class = SQLHeaderLimitOffsetPagination

    def post(self, request, *args, **kwargs):
        self.tank_ids = [each['Tank_id'] for each in request.data.get('tanks', None)]
        self.start_date = request.data.get('start')
        self.end_date = request.data.get('end')
        kwargs['data_query'] = q.revamped_get_tanklogs
        return self.paginate_and_cache(request, *args, **kwargs)
        


class TankReadingsForTankGroups(generics.CreateAPIView, log_utils.SqlLogsPaginationCacheMixin):
    # pagination_class = SQLHeaderLimitOffsetPagination

    def post(self, request, *args, **kwargs):
        self.ids = request.data.get('tankgroup', None)
        self.start_date = request.data.get('start')
        self.end_date = request.data.get('end')
        kwargs['count_query'] = q.get_tankgrouplogs_count
        kwargs['data_query'] = q.get_tankgroup_logs
        return self.paginate_and_cache(request, *args, **kwargs)

class TankLogAnomalyView(generics.CreateAPIView, log_utils.SqlLogsPaginationCacheMixin):
    Pass
class ModifiedCurrentTankDetails(APIView):
    def post(self, request, *args, **kwargs):
        site_id = request.data.get('site', None)
        if site_id:
            #get tank_details from the sites required
            site_device = models.Sites.objects.get(Site_id=site_id)
            
            try:
                mac_address = site_device.Device.Device_unique_address
            except :
                return utils.CustomResponse.Success([])
            
            tank_details = list(models.Tanks.objects.filter(Site=site_id, Status=True).values('Name','Product','Tank_index','Controller_polling_address','Tank_controller','Capacity','Display_unit','UOM'))
            
            data = []
            #use threading to get the logs for each tank
            with ThreadPoolExecutor() as executor:
                tank_details_futures = [executor.submit(
                    q.modified_get_tank_latest_log,
                    tank['Tank_controller'],
                    tank['Tank_index'],tank['Controller_polling_address'], mac_address,tank['Display_unit'],tank['UOM'],tank['Capacity'],tank['Name'],str(site_device),tank['Product']) for tank in tank_details]
                for future in as_completed(tank_details_futures):
                    data.extend(future.result())
            return utils.CustomResponse.Success(data)
        else:
            return utils.CustomResponse.Failure('No site passed')


class RevampedCurrentTankDetails(APIView):
    serializer = LatestTankLogSerializer
    def post(self, request, *args, **kwargs):
        site_ids = request.data.get('site', None)
        if site_ids:
            #tank_ids = list(models.Sites.objects.prefetch_related('tanks').filter(pk__in=site_ids).values_list('tanks', flat=True))  
            returned =  LatestTankLogSerializer(models.LatestAtgLog.objects.filter(Site_id__in=site_ids), many=True)
            return utils.CustomResponse.Success(returned.data, status=status.HTTP_200_OK)
        else:
            return utils.CustomResponse.Failure('No site passed')

class PreviousCurrentTankDetails(APIView):
    def post(self, request, *args, **kwargs):
        site_ids = request.data.get('site', None)
        if site_ids:
            #get tank_ids from the sites required
            tank_ids = list(models.Sites.objects.prefetch_related('tanks').filter(pk__in=site_ids).values_list('tanks', flat=True))
            data = []
            #use threading to get the logs for each tank
            with ThreadPoolExecutor() as executor:
                tank_details_futures = [executor.submit(
                    q.get_tank_latest_log,
                    tank_id) for tank_id in tank_ids]
                for future in as_completed(tank_details_futures):
                    data.extend(future.result())
            #update data
            data = log_utils.update_tankgroup_records(data)
            return utils.CustomResponse.Success(data)
        else:
            return utils.CustomResponse.Failure('No site passed')


class CurrentTankDetails(APIView):
    serializer = LatestTankLogSerializer
    def post(self, request, *args, **kwargs):
        site_ids = request.data.get('site', None)
        if site_ids:
            #tank_ids = list(models.Sites.objects.prefetch_related('tanks').filter(pk__in=site_ids).values_list('tanks', flat=True))  
            returned =  LatestTankLogSerializer(models.LatestAtgLog.objects.filter(Site_id__in=site_ids), many=True)
            return utils.CustomResponse.Success(returned.data, status=status.HTTP_200_OK)
        else:
            return utils.CustomResponse.Failure('No site passed')


class CurrentTankDetailsForTankgroup(APIView):
    def post(self, request, *args, **kwargs):
        tankgroup_ids = request.data.get('tankgroups', None)
        final_data = []
        for tgID in tankgroup_ids:
            try:
                tg = models.TankGroups.objects.get(pk=tgID)
            except models.TankGroups.DoesNotExist:
                continue

            tg_name = tg.Name
            tg_capacity = tg.current_capacity
            tg_product = tg.Product.Name
            tg_tank_count = tg.tank_count
            tg_volume = 0
            tg_last_update_time = ""
            tg_fill = 0

            tank_ids = list(tg.Tanks.values_list('Tank_id', flat=True))
            data = []
            #use threading to get the logs for each tank
            with ThreadPoolExecutor() as executor:
                tank_details_futures = [executor.submit(
                    q.get_tankgroup_tank_latest_log,
                    tank_id) for tank_id in tank_ids]
                for future in as_completed(tank_details_futures):
                    data.extend(future.result())
            #update data
            tank_data = log_utils.update_tankgroup_records(data)
            if tank_data:
                tg_volume = sum(float(tank['tankVolume']) for tank in tank_data)
                tg_fill = round((float(tg_volume) * 100 / tg_capacity), 2)
                tg_last_update_time = max(datetime.datetime.strptime(tank['last_updated_time'], '%Y-%m-%d %H:%M:%S') for tank in tank_data)
                tg_last_update_time = tg_last_update_time.strftime('%Y-%m-%d %H:%M:%S')

            tankgroup_data = {
                "Name":tg_name,
                "Capacity":tg_capacity,
                "Volume":tg_volume,
                "Product":tg_product,
                "Tank_count":tg_tank_count,
                "Fill(%)":tg_fill,
                "last_updated_time":tg_last_update_time
            }

            payload = {
                "accumulated": tankgroup_data,
                "tanks": tank_data
            }
            final_data.append(payload)
        return utils.CustomResponse.Success(final_data)

class RevampedCurrentTankDetailsForTankgroup(APIView):
    def post(self, request, *args, **kwargs):
        tankgroup_ids = request.data.get('tankgroups', None)
        final_data = []
        for tgID in tankgroup_ids:
            try:
                tg = models.TankGroups.objects.get(pk=tgID)
            except models.TankGroups.DoesNotExist:
                continue

            tg_name = tg.Name
            tg_capacity = tg.current_capacity
            tg_product = tg.Product.Name
            tg_tank_count = tg.tank_count
            tg_volume = 0
            tg_last_update_time = tg.Updated_at
            tg_fill = 0

            tank_ids = list(tg.Tanks.values_list('Tank_id', flat=True))
            data = []
            #use threading to get the logs for each tank
            with ThreadPoolExecutor() as executor:
                revampedtank_details_futures = [executor.submit(
                    q.revamped_get_tankgroup_tank_latest_log,tank_id) for tank_id in tank_ids]
                for future in as_completed(revampedtank_details_futures):
                    print(future.result())
                    data.extend(future.result())

            tank_data = data
            if tank_data:
                try:
                    tg_volume = sum(float(tank['Volume']) for tank in data)
                    tg_fill = round((float(tg_volume) * 100 / tg_capacity), 2)
                    tg_last_update_time = max(datetime.datetime.strptime(f"{tank['last_updated_time']}", '%Y-%m-%d %H:%M:%S') for tank in tank_data)
                    tg_last_update_time = tg_last_update_time.strftime('%Y-%m-%d %H:%M:%S')
                except :
                    pass
            tankgroup_data = {
                "Name":tg_name,
                "Capacity":tg_capacity,
                "Volume":tg_volume,
                "Product":tg_product,
                "Tank_count":tg_tank_count,
                "Fill(%)":tg_fill,
                "last_updated_time":tg_last_update_time
            }

            payload = {
                "accumulated": tankgroup_data,
                "tanks": tank_data
            }
            final_data.append(payload)
        return utils.CustomResponse.Success(final_data)



class TankMap(APIView):
    serializer_class = TankMapSerializer

    def post(self, request, *args, **kwargs):
        serialized = self.serializer_class(data=request.data)
        if serialized.is_valid():
            serialized_data = serialized.validated_data
            site_id = serialized_data['site_ids']

            if site_id:
                result = log_utils.getSitesAndTanks(site_id)
                return utils.CustomResponse.Success(result)
            else:
                return utils.CustomResponse.Failure('No site passed')
