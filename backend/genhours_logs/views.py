from concurrent.futures import ThreadPoolExecutor, as_completed
import time

import datetime as dt

from datetime import date, timedelta, datetime

from django.shortcuts import get_object_or_404

from rest_framework import status, generics
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema, extend_schema_serializer
from drf_spectacular.types import OpenApiTypes

from backend import models
from .. import utils
from . import utils as log_utils
from . import serializer
from . import queries

import time


class GeneratorHoursLogger(APIView):
    permission_classes = ()
    authentication_classes = ()

    serializer_class = serializer.GenLoggerSerializer

    @extend_schema(responses=OpenApiTypes.STR)
    def post(self, request, *args, **kwargs):
        data = request.data  # incoming data is a tuple of tuples for genhours logs
        #(local_id, mac_address,lineID,status,uploaded,timestamp)
        genhours_logs = [models.GeneratorHours(mac_address=d[1], lineID=d[2],
                                               status=d[3], timestamp=d[5]) for d in data]

        models.GeneratorHours.objects.bulk_create(genhours_logs)
        return utils.CustomResponse.Success("Successful")


class FlowmeterLogger(APIView):
    permission_classes = ()
    authentication_classes = ()

    serializer_class = serializer.GenLoggerSerializer

    @extend_schema(responses=OpenApiTypes.STR)
    def post(self, request, *args, **kwargs):
        data = request.data
        fm_logs = [models.FlowmeterLogs(mac_address=d[1], flowmeter_address=d[2],
                                        litres=d[3], hours=d[4], forward_litres=d[5], backward_litres=d[6],
                                        forward_fuel_rate=d[7], backward_fuel_rate=d[8],
                                        consumption_rate=d[10], temperature=d[11], status=d[12],
                                        mode=d[13], timestamp=d[15], uid=d[18] if len(d) > 18 else 0) for d in data]

        models.FlowmeterLogs.objects.bulk_create(fm_logs)
        return utils.CustomResponse.Success("Successful")


class PowermeterLogger(APIView):
    """
        Write new powermeter logs to the db from firmware
    """
    permission_classes = ()
    authentication_classes = ()

    serializer_class = serializer.GenPowerLoggerSerializer
    # data in this  format
    # id,mac_address,pm_address,equipment_id,Time_stamp,uuid,voltage_a,voltage_b,voltage_c,current_a,
    # current_b,current_c,power_a,power_b,power_c,power_total,frequency,power_factor,active_energy,engine_running

    @extend_schema(responses=OpenApiTypes.STR)
    def post(self, request, *args, **kwargs):
        data = request.data
        pm_logs = [models.PowermeterLogs(mac_address=each[1], powermeter_address=each[2], uid=each[5], voltage_a=each[6], voltage_b=each[7], voltage_c=each[8], current_a=each[9], current_b=each[10], current_c=each[11], power_a=each[12],
                                         power_b=each[13], power_c=each[14], power_total=each[
                                             15], frequency=each[16], power_factor=each[17], active_energy=each[18],
                                         timestamp=each[4], engine_running=each[19], equipment=models.Equipment.objects.get(pk=int(each[3]))) for each in data]
        models.PowermeterLogs.objects.bulk_create(pm_logs)
        return utils.CustomResponse.Success("Successful")


class PowerMeterTransactionLogs(generics.ListAPIView):
    """
        List all registered powermeter
    """
    permission_classes = ()
    authentication_classes = ()
    queryset = models.PowermeterLogs.objects.all()
    serializer_class = serializer.GenPowerLoggerSerializer


class PowerMeterTransaction(generics.CreateAPIView):
    """
        Create A new Powermeter
    """
    permission_classes = ()
    authentication_classes = ()
    queryset = models.PowerMeter.objects.all()
    serializer_class = serializer.PowerMeterSerializer


class PowerMeterUpdate(APIView):
    permission_classes = ()
    authentication_classes = ()

    @extend_schema(responses=OpenApiTypes.STR)
    def post(self, request):
        data = request.data
        try:
            site = models.Sites.objects.get(pk=data['site'])
            equipment = models.Equipment.objects.get(pk=data['equipment'])
            models.PowerMeter.objects.filter(pk=data['id']).update(
                serial_number=data['serial_number'], site=site, meter_type=data['meter_type'], address=data['address'], equipment=equipment)
        except Exception as e:
            return utils.CustomResponse.Failure(error="{0}".format(e))
        return utils.CustomResponse.Success(data="Powermeter Updated Successfully")


class ViewAllPowermeters(APIView):
    permission_classes = ()
    authentication_classes = ()

    @extend_schema(responses=serializer.PowerMeterListSerializer)
    def get(self, request):
        powermeters = serializer.PowerMeterListSerializer(
            models.PowerMeter.objects.all(), many=True)
        return utils.CustomResponse.Success(data=powermeters.data)


class ViewPowerMetersByCompany(APIView):
    permission_classes = ()
    authentication_classes = ()

    @extend_schema(responses=serializer.PowerMeterListSerializer)
    def get(self, request, *args, **kwargs):
        company = models.Companies.objects.get(pk=request.GET['id'])
        sites = models.Sites.objects.filter(Company=company)
        powermeters = serializer.PowerMeterListSerializer(
            models.PowerMeter.objects.filter(site__in=sites), many=True)
        return utils.CustomResponse.Success(data=powermeters.data)


class ViewPowerMetersByMultipleCompany(APIView):
    permission_classes = ()
    authentication_classes = ()

    @extend_schema(responses=serializer.PowerMeterListSerializer)
    def get(self, request, *args, **kwargs):
        company_ids = request.GET['company'].split(',')
        company = models.Companies.objects.filter(
            Company_id__in=company_ids)
        sites = models.Sites.objects.filter(Company__in=company)
        powermeters = serializer.PowerMeterListSerializer(
            models.PowerMeter.objects.filter(site__in=sites), many=True)
        return utils.CustomResponse.Success(data=powermeters.data)


class ActivateDeactivatePowermeter(APIView):

    permission_classes = ()
    authentication_classes = ()

    @extend_schema(responses=OpenApiTypes.STR)
    def post(self, request, *args, **kwargs):
        if kwargs.get('action').lower() == 'deactivate':
            action = False
        else:
            action = True

        powermeter = models.PowerMeter.objects.filter(
            pk=kwargs['powermeter_id']).update(active=action)
        return utils.CustomResponse.Success(data="Success")


class PowermeterLastLog(APIView):
    permission_classes = ()
    authentication_classes = ()

    def post(self, request):
        data = request.data

        try:
            equipments = models.Equipment.objects.filter(
                site__in=data['site_ids']).values()
        except Exception as e:
            pass
        try:
            results = []
            for equipment in equipments:
                equipment_id = equipment["id"]
                try:
                    equipment["log"] = models.PowermeterLogs.objects.filter(
                        equipment__id=equipment_id).order_by('-timestamp').values().first()
                    equipment["status"] = models.FlowmeterLogs.objects.filter(
                        mac_address=equipment["log"]["mac_address"]).order_by('-timestamp').values().first()
                    # print('log', equipment["log"])
                    # print('status', equipment["status"])
                except Exception as e:
                    continue

                equipment["site_id"] = models.Sites.objects.filter(
                    pk=equipment["site_id"]).values()[0]['Name']

                # if last log is more than 5mins ago then status if false
                # else status is true if status is already true
                time_lag = dt.timedelta(seconds=300)
                diff_lasttime_now = dt.datetime.now(
                ) - equipment['status']['timestamp']
                if (diff_lasttime_now >= time_lag) and (equipment['status']['status'] == 1):
                    equipment['status']['status'] = 0
                results.append(equipment)

        except Exception as e:
            pass
        return utils.CustomResponse.Success(data=results)


class PowermeterLogs(APIView):
    permission_classes = ()
    authentication_classes = ()

    def post(self, request):
        start, end = request.data['start'], request.data['end']
        equipments_id = request.data['equipments_id']
        logs = log_utils.get_power_consumption_logs(equipments_id, start, end)
        return utils.CustomResponse.Success(data=logs)


class ConsumptionLoad(APIView):
    permission_classes = ()
    authentication_classes = ()

    def post(self, request):
        equipments_id = request.data['equipments_id']
        start, end = request.data['start'], request.data['end']

        get_power_consumption_logs = log_utils.get_power_consumption_logs(
            equipments_id, start, end)
        get_on_off_report = log_utils.get_on_off_report(
            equipments_id, get_power_consumption_logs)
        # print('report', get_on_off_report)
        return utils.CustomResponse.Success(data=get_on_off_report)


class PowerLogPerCycle(APIView):
    permission_classes = ()
    authentication_classes = ()

    def post(self, request):
        equipments_id = [request.data['equipment_id']]
        start, end = request.data['start'], request.data['end']
        get_power_consumption_logs = log_utils.get_power_consumption_logs(
            equipments_id, start, end)
        return utils.CustomResponse.Success(data=get_power_consumption_logs)


class DailyPowerTrend(APIView):
    permission_classes = ()
    authentication_classes = ()

    def post(self, request):
        start = request.data['start']
        end = request.data['end']
        site_ids = request.data['site_ids']

        dates = []
        sources = {}
        equip = models.Equipment.objects.filter(site__in=site_ids)
        equipments = [each[1] for each in equip.values_list()]

        for each in equipments:
            sources[each] = []
            full_logs = models.PowermeterLogs.objects.filter(
                timestamp__gt=start, timestamp__lt=end, equipment__name=each).values_list()
            for log in full_logs:
                dates.append(datetime.strftime(log[18], "%Y-%m-%d %H:%M:%S"))
                sources[each].append(log[5])

        data = [dates, equipments, sources]
        return utils.CustomResponse.Success(data=data)


class EquipmentList(APIView):
    permission_classes = ()
    authentication_classes = ()

    def get(self, request):
        site = models.Sites.objects.get(pk=request.GET['site_id'])
        equipments = serializer.EquipmentListSerializer(
            models.Equipment.objects.filter(site=site), many=True)
        return utils.CustomResponse.Success(data=equipments.data)


class EquipmentObj(APIView):
    permission_classes = ()
    authentication_classes = ()

    def get(self, request):
        site = models.Sites.objects.get(pk=request.GET['site_id'])
        name = request.GET.get('name')
        equipment = serializer.EquipmentListSerializer(
            models.Equipment.objects.get(site=site, name=name))
        return utils.CustomResponse.Success(data=equipment.data)


class EquipmentDashboardView(APIView):
    '''
    Get the following details:
    - Online status (Extract the last log of the equipment)
    - Totaliser hours 
    '''
    serializer_class = serializer.EquipmentDashboardViewSerializer

    @extend_schema(responses=serializer.EquipmentDashboardResponseSerializer)
    def post(self, request, *args, **kwargs):
        serialized = self.serializer_class(data=request.data)
        if serialized.is_valid():
            serialized_data = serialized.validated_data
            site_id = serialized_data['site_ids']

            if site_id:
                # get all equipments
                equipment_ids = models.Sites.objects.prefetch_related('equipments').filter(
                    pk__in=site_id).values_list('equipments', flat=True)
                data = []
                with ThreadPoolExecutor() as executor:
                    equipment_futures = [executor.submit(
                        log_utils.get_equipment_dashboard_details,
                        equipment) for equipment in models.Equipment.objects.filter(pk__in=equipment_ids)]

                    phcn_futures = []
                    for site in models.Sites.objects.filter(pk__in=site_id):
                        try:
                            site_config = site.genhours_config
                            public_power_monitoring = site_config.monitor_public_power
                        except models.SiteGenHoursConfiguration.DoesNotExist:
                            public_power_monitoring = False

                        if public_power_monitoring:
                            phcn_futures.append(executor.submit(
                                log_utils.get_phcn_dashboard_details, site))

                    futures = equipment_futures + phcn_futures
                    time_lag = dt.timedelta(seconds=300)

                    for future in as_completed(futures):
                        value = future.result()

                        # if last log is more than 5mins ago then status if false
                        # else status is true if status is already true
                        try:
                            for each_euip in value:
                                if each_euip['equipment_type']:
                                    diff_lasttime_now = dt.datetime.now(
                                    ) - each_euip['last_updated_time']
                                    if (diff_lasttime_now >= time_lag) and (each_euip['online_status'] == True):
                                        each_euip['online_status'] = False
                        except:
                            pass

                        data.extend(value)
                return utils.CustomResponse.Success(data)
            else:
                return utils.CustomResponse.Failure('No site passed')


class EquipmentMap(APIView):
    serializer_class = serializer.EquipmentDashboardViewSerializer

    @extend_schema(responses=serializer.EquipmentDashboardResponseSerializer)
    def post(self, request, *args, **kwargs):
        serialized = self.serializer_class(data=request.data)
        if serialized.is_valid():
            serialized_data = serialized.validated_data
            site_id = serialized_data['site_ids']

            if site_id:
                result = log_utils.getSitesAndEquipments(site_id)
                return utils.CustomResponse.Success(result)
            else:
                return utils.CustomResponse.Failure('No site passed')


class TotalHoursReport(APIView):
    serializer_class = serializer.EquipmentRequestSerializer

    @extend_schema(responses=serializer.EquipmentDashboardResponseSerializer)
    def post(self, request, *args, **kwargs):
        serialized = self.serializer_class(data=request.data)
        if serialized.is_valid():
            serialized_data = serialized.validated_data
            site_ids = serialized_data['site_ids']
            start = serialized_data['start']
            end = serialized_data['end']
            equipment_ids = [each['id']
                             for each in request.data.get('equipments', None)]
            if site_ids:
                # equipment_ids = models.Sites.objects.prefetch_related('equipments').filter(pk__in=site_ids).values_list('equipments', flat=True)
                data = []
                with ThreadPoolExecutor(max_workers=len(equipment_ids) or 1) as executor:
                    equipment_futures = [executor.submit(
                        log_utils.get_equipment_total_hours_log_report,
                        equipment, start, end) for equipment in models.Equipment.objects.filter(pk__in=equipment_ids)]

                    phcn_futures = []
                    for site in models.Sites.objects.filter(pk__in=site_ids):
                        try:
                            site_config = site.genhours_config
                            public_power_monitoring = site_config.monitor_public_power
                        except models.SiteGenHoursConfiguration.DoesNotExist:
                            public_power_monitoring = False

                        if public_power_monitoring:
                            phcn_futures.append(executor.submit(
                                log_utils.get_phcn_total_hours_log_report, site, start, end))
                    futures = equipment_futures + phcn_futures
                    for future in as_completed(futures):
                        data.extend(future.result())
                return utils.CustomResponse.Success(data)


class Daily24HrsRangeConsumptionReport(APIView):
    serializer_class = serializer.HourlyRequestSerializer

    @extend_schema(responses=serializer.HourlyResponseSerializer)
    def post(self, request, *args, **kwargs):
        serialized = self.serializer_class(data=request.data)
        if serialized.is_valid():
            serialized_data = serialized.validated_data
            date = serialized_data['date']
            equipment_id = serialized_data['equipment_id']
            equipment = models.Equipment.objects.get(pk=equipment_id)
            daily_hours_interval = range(24)
            if equipment_id:
                data = []
                with ThreadPoolExecutor(max_workers=len(daily_hours_interval) or 1) as executor:
                    daily_hour_interval_futures = [executor.submit(
                        log_utils.get_equipment_daily_24hrs_interval_litres_consumption_log_report,
                        equipment, date, eachHour) for eachHour in daily_hours_interval]
                    for future in as_completed(daily_hour_interval_futures):
                        data.append(future.result())
                data.sort(
                    key=lambda x: (x['HourlyInterval']))
                return utils.CustomResponse.Success(data)


class EquipmentConsumptionReport(APIView):
    serializer_class = serializer.EquipmentRequestSerializer

    @extend_schema(responses=serializer.EquipmentDashboardResponseSerializer)
    def post(self, request, *args, **kwargs):
        serialized = self.serializer_class(data=request.data)
        if serialized.is_valid():
            serialized_data = serialized.validated_data
            site_ids = serialized_data['site_ids']
            start = serialized_data['start']
            end = serialized_data['end']
            equipment_ids = [each['id']
                             for each in request.data.get('equipments', None)]
            if site_ids:
                data = []
                with ThreadPoolExecutor(max_workers=len(equipment_ids) or 1) as executor:
                    equipment_futures = [executor.submit(
                        log_utils.get_equipment_litres_consumption_log_report,
                        equipment, start, end) for equipment in models.Equipment.objects.filter(pk__in=equipment_ids)]
                    for future in as_completed(equipment_futures):
                        data.extend(future.result())
                return utils.CustomResponse.Success(data)


class HoursDailyTrend(APIView):
    serializer_class = serializer.EquipmentRequestSerializer

    @extend_schema(responses=serializer.EquipmentConsumptionResponseSerializer)
    def post(self, request, *args, **kwargs):
        serialized = self.serializer_class(data=request.data)
        if serialized.is_valid():
            serialized_data = serialized.validated_data
            site_ids = serialized_data['site_ids']
            start = serialized_data['start']
            end = serialized_data['end']
            if site_ids:
                site_id = site_ids[0]
                site = get_object_or_404(models.Sites, pk=site_id)
                equipments = site.equipments.all()
                equipment_ids = equipments.values_list('id', flat=True)
                equipment_names = list(
                    equipments.values_list('name', flat=True))
                data = {"equipments": equipment_names}
                try:
                    site_config = site.genhours_config
                    public_power_monitoring = site_config.monitor_public_power
                except models.SiteGenHoursConfiguration.DoesNotExist:
                    public_power_monitoring = False

                if public_power_monitoring:
                    data["equipments"] += [site_config.public_power_source_slug]

                # get date range
                start = dt.datetime.strptime(start, "%Y-%m-%d")
                end = dt.datetime.strptime(end, "%Y-%m-%d")
                step = dt.timedelta(days=1)

                date_range = log_utils.date_range(start, end, step)
                date_range = [date.strftime("%Y-%m-%d") for date in date_range]
                data["dates"] = date_range
                data["sources"] = {}
                with ThreadPoolExecutor(max_workers=len(equipment_ids) or 1) as executor:
                    equipment_futures = [executor.submit(
                        log_utils.get_equipment_daily_total_hours,
                        equipment, date_range) for equipment in models.Equipment.objects.filter(pk__in=equipment_ids)]

                    phcn_futures = []
                    if public_power_monitoring:
                        phcn_futures = [executor.submit(
                            log_utils.get_phcn_daily_total_hours,
                            site, date_range)]

                    futures = equipment_futures + phcn_futures
                    for future in as_completed(futures):
                        result = future.result()
                        data["sources"][result["name"]] = result["hours"]
                return utils.CustomResponse.Success(data)


class EquipmentConsumptionDailyTrend(APIView):
    serializer_class = serializer.EquipmentRequestSerializer

    @extend_schema(responses=serializer.EquipmentConsumptionResponseSerializer)
    def post(self, request, *args, **kwargs):
        serialized = self.serializer_class(data=request.data)
        if serialized.is_valid():
            serialized_data = serialized.validated_data
            site_ids = serialized_data['site_ids']
            start = serialized_data['start']
            end = serialized_data['end']
            if site_ids:
                site_id = site_ids[0]
                site = get_object_or_404(models.Sites, pk=site_id)
                equipments = site.equipments.all()
                equipment_ids = equipments.values_list('id', flat=True)
                equipment_names = list(
                    equipments.values_list('name', flat=True))
                data = {"equipments": equipment_names}
                # get date range
                start = dt.datetime.strptime(start, "%Y-%m-%d")
                end = dt.datetime.strptime(end, "%Y-%m-%d")
                step = dt.timedelta(days=1)

                date_range = log_utils.date_range(start, end, step)
                date_range = [date.strftime("%Y-%m-%d") for date in date_range]
                data["dates"] = date_range
                data["sources"] = {}
                with ThreadPoolExecutor(max_workers=len(equipment_ids) or 1) as executor:
                    futures = [executor.submit(
                        log_utils.get_equipment_daily_litres_consumed,
                        equipment, date_range) for equipment in models.Equipment.objects.filter(pk__in=equipment_ids)]
                    for future in as_completed(futures):
                        result = future.result()
                        data["sources"][result["name"]] = result["litres"]
                return utils.CustomResponse.Success(data)


class EquipmentDailyConsumptionRatesTrend(APIView):
    """
        post: {'site_ids<LISTFormat>', 'start<DateFormat>', 'end<DateFormat>'}
    """
    serializer_class = serializer.EquipmentRequestSerializer

    @extend_schema(responses=serializer.EquipmentConsumptionResponseSerializer)
    def post(self, request, *args, **kwargs):
        serialized = self.serializer_class(data=request.data)
        if serialized.is_valid():
            serialized_data = serialized.validated_data
            site_ids = serialized_data['site_ids']
            start = serialized_data['start']
            end = serialized_data['end']
            if site_ids:
                site_id = site_ids[0]
                site = get_object_or_404(models.Sites, pk=site_id)
                equipments = site.equipments.all()
                equipment_ids = equipments.values_list('id', flat=True)
                equipment_names = list(
                    equipments.values_list('name', flat=True))
                data = {"equipments": equipment_names}
                # get date range
                start = dt.datetime.strptime(start, "%Y-%m-%d")
                end = dt.datetime.strptime(end, "%Y-%m-%d")
                step = dt.timedelta(days=1)

                date_range = log_utils.date_range(start, end, step)
                date_range = [date.strftime("%Y-%m-%d") for date in date_range]
                data["dates"] = date_range
                data["sources"] = {}
                with ThreadPoolExecutor(max_workers=len(equipment_ids) or 1) as executor:
                    futures = [executor.submit(
                        log_utils.get_equipment_daily_consumption_rates,
                        equipment, date_range) for equipment in models.Equipment.objects.filter(pk__in=equipment_ids)]
                    for future in as_completed(futures):
                        result = future.result()
                        data["sources"][result["name"]] = result["rates"]

                # remove dates where
                return utils.CustomResponse.Success(data)


class HoursDistribution(APIView):
    serializer_class = serializer.EquipmentRequestSerializer

    @extend_schema(responses=serializer.EquipmentConsumptionResponseSerializer)
    def post(self, request, *args, **kwargs):
        serialized = self.serializer_class(data=request.data)
        if serialized.is_valid():
            serialized_data = serialized.validated_data
            site_ids = serialized_data['site_ids']
            start = serialized_data['start']
            end = serialized_data['end']
            if site_ids:
                site_id = site_ids[0]
                site = get_object_or_404(models.Sites, pk=site_id)
                equipments = site.equipments.all()
                equipment_ids = equipments.values_list('id', flat=True)
                data = {}
                with ThreadPoolExecutor(max_workers=len(equipment_ids) or 1) as executor:
                    equipment_futures = [executor.submit(
                        log_utils.get_equipment_total_hours_in_range,
                        equipment, start, end) for equipment in models.Equipment.objects.filter(pk__in=equipment_ids)]

                    phcn_futures = []
                    for site in models.Sites.objects.filter(pk=site_id):
                        try:
                            site_config = site.genhours_config
                            public_power_monitoring = site_config.monitor_public_power
                        except models.SiteGenHoursConfiguration.DoesNotExist:
                            public_power_monitoring = False

                        if public_power_monitoring:
                            phcn_futures.append(executor.submit(
                                log_utils.get_phcn_total_hours_in_range, site, start, end))
                    futures = equipment_futures + phcn_futures
                    for future in as_completed(futures):
                        data.update(future.result())
                return utils.CustomResponse.Success(data)


class LitresConsumedDistribution(APIView):
    serializer_class = serializer.EquipmentRequestSerializer

    @extend_schema(responses=serializer.EquipmentConsumptionResponseSerializer)
    def post(self, request, *args, **kwargs):
        serialized = self.serializer_class(data=request.data)
        if serialized.is_valid():
            serialized_data = serialized.validated_data
            site_ids = serialized_data['site_ids']
            start = serialized_data['start']
            end = serialized_data['end']
            if site_ids:
                site_id = site_ids[0]
                site = get_object_or_404(models.Sites, pk=site_id)
                equipments = site.equipments.all()
                equipment_ids = equipments.values_list('id', flat=True)
                data = {}
                with ThreadPoolExecutor(max_workers=len(equipment_ids) or 1) as executor:
                    futures = [executor.submit(
                        log_utils.get_equipment_litres_consumed_in_range,
                        equipment, start, end) for equipment in models.Equipment.objects.filter(pk__in=equipment_ids)]
                    for future in as_completed(futures):
                        data.update(future.result())
                return utils.CustomResponse.Success(data)


class EquipmentFlowmeterTestTransactionReport(APIView):
    """
        post: {site_ids, start, end}
        response: {data, error, code, status}
    """

    serializer_class = serializer.EquipmentRequestSerializer

    def post(self, request, *args, **kwargs):
        serialized = self.serializer_class(data=request.data)
        if serialized.is_valid():
            serialized_data = serialized.validated_data
            site_ids = serialized_data['site_ids']
            start = serialized_data['start']
            end = serialized_data['end']
            if site_ids:
                equipment_ids = models.Sites.objects.prefetch_related('equipments').filter(
                    pk__in=site_ids).values_list('equipments', flat=True)
                data = []
                with ThreadPoolExecutor(max_workers=len(equipment_ids) or 1) as executor:
                    futures = [executor.submit(
                        log_utils.get_flowmeter_test_transaction_report,
                        equipment, start, end) for equipment in models.Equipment.objects.filter(pk__in=equipment_ids) if equipment.flowmeter]
                    for future in as_completed(futures):
                        data.extend(future.result())
                return utils.CustomResponse.Success(data)


class EquipmentFlowmeterTransactionLogs(APIView):
    """
        post: {equipment_id, start, end}
    """
    serializer_class = serializer.EquipmentLogsSerializer

    @extend_schema(responses=serializer.FlowmeterLogsSerializer)
    def post(self, request, *args, **kwargs):
        serialized = self.serializer_class(data=request.data)
        if serialized.is_valid():
            serialized_data = serialized.validated_data
            equipment_id = serialized_data['equipment_id']
            start = serialized_data['start']
            end = serialized_data['end']

            equipment = get_object_or_404(models.Equipment, pk=equipment_id)
            mac_address = equipment.site.Device.Device_unique_address
            # temporary condition for smartflow installation
            if equipment.site.Site_id == 1:
                mac_address = 'b8:27:eb:fb:00:9f'
            transaction_logs = models.FlowmeterLogs.objects.filter(
                mac_address=mac_address,
                flowmeter_address=equipment.flowmeter.address,
                timestamp__gte=start,
                timestamp__lte=end
            ).order_by('timestamp')
            serialized = serializer.FlowmeterLogsSerializer(
                transaction_logs, many=True)
            return utils.CustomResponse.Success(serialized.data)
        else:
            return utils.CustomResponse.Failure("Invalid form-data")


class EquipmentFlowmeterTransactionTrends(APIView):
    """
        post: {equipment_id, start, end}
    """
    serializer_class = serializer.EquipmentLogsSerializer

    @extend_schema(responses=serializer.EquipmentFlowmeterResponseSerializer)
    def post(self, request, *args, **kwargs):
        serialized = self.serializer_class(data=request.data)
        if serialized.is_valid():
            serialized_data = serialized.validated_data
            equipment_id = serialized_data['equipment_id']
            start = serialized_data['start']
            end = serialized_data['end']

            equipment = get_object_or_404(models.Equipment, pk=equipment_id)
            mac_address = equipment.site.Device.Device_unique_address
            # temporary condition for smartflow installation
            if equipment.site.Site_id == 1:
                mac_address = 'b8:27:eb:fb:00:9f'
            transaction_logs = models.FlowmeterLogs.objects.filter(
                mac_address=mac_address,
                flowmeter_address=equipment.flowmeter.address,
                timestamp__gte=start,
                timestamp__lte=end
            ).order_by('timestamp')
            serialized = serializer.FlowmeterLogsSerializer(
                transaction_logs, many=True)
            data = serialized.data

            timestamps = []
            forward_rates = []
            backward_rates = []
            consumption_rates = []
            for d in data:
                timestamps.append(d["timestamp"])
                consumption_rates.append(round(d["consumption_rate"], 3))
                forward_rates.append(round(d["forward_fuel_rate"], 3))
                backward_rates.append(round(d["backward_fuel_rate"], 3))

            return utils.CustomResponse.Success(
                {
                    "timestamps": timestamps,
                    "sources": {
                        "Consumption rates": consumption_rates,
                        "Forward rates": forward_rates,
                        "Reverse rates": backward_rates
                    }
                }
            )


class TransactionComment(generics.CreateAPIView):

    serializer_class = serializer.TransactionCommentSerializer

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data, status=201)


class TransactionCommentDetail(generics.UpdateAPIView):

    serializer_class = serializer.TransactionCommentSerializer
    queryset = models.FlowmeterTransactionComment.objects.all()

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        response = super().update(request, *args, **kwargs)
        return utils.CustomResponse.Success(response.data, response.status_code)
