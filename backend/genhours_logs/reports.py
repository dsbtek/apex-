import datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed

from backend import models

from ..reports.new_custom_reports import TimeRangeConsumptionReport, DailyConsumptionReport
from django.db.models import Avg

'''
Total Hours with Logs
Total Hours
Daily total hours
Total hours in range

- An equipment hour is valid if it worked for 10 mins & above
'''
GEN_THRESHOLD = 0.16


def extract_total_hours_from_FM_logs(logs, litres_mode=False):
    total_hours = 0
    total_litres = 0
    on_flag = False
    start_log = ""
    end_log = ""
    for (index, log) in enumerate(logs):
        if log.status == 1 and not on_flag:
            on_flag = True
            start_log = log

        elif log.status == 0 and on_flag:
            on_flag = False
            end_log = log
            start_time = start_log.timestamp
            end_time = end_log.timestamp
            hours = (end_log.hours - start_log.hours)/3600
            if hours < GEN_THRESHOLD:
                continue
            start_litres = start_log.litres
            end_litres = end_log.litres
            litres = end_litres - start_litres
            total_litres += litres
            total_hours += hours
        # compute when engine keeps running
        elif log.status == 1 and on_flag and index == logs.count()-1:
            on_flag = False
            end_log = log
            start_time = start_log.timestamp
            end_time = end_log.timestamp
            hours = (end_log.hours - start_log.hours)/3600
            if hours < GEN_THRESHOLD:
                continue
            start_litres = start_log.litres
            end_litres = end_log.litres
            litres = end_litres - start_litres
            total_litres += litres
            total_hours += hours

    # if full_mode:
    #     return total_hours, total_litres
    if litres_mode:
        return total_litres
    else:
        return total_hours


'''
**************************************************
TOTAL HOURS WITH LOGS
***************************************************
'''


def extract_total_hours_logs_from_DI_logs(logs, end):
    total_hours = 0
    payload = []
    last_log = None
    on_flag = False
    start_time = ""
    end_time = ""
    for (index, log) in enumerate(logs):
        if log.status == 1 and not on_flag:
            on_flag = True
            start_time = log.timestamp

        elif log.status == 0 and on_flag:
            on_flag = False
            end_time = log.timestamp
            hours_delta = end_time - start_time
            hours = hours_delta.seconds/3600
            if hours < GEN_THRESHOLD:
                continue
            payload.append({
                'start_time': start_time,
                'end_time': end_time,
                'hours': round(hours, 3)
            })
        last_log = log
    end = dt.datetime.strptime(end, "%Y-%m-%d %H:%M")
    if last_log and last_log.status == 1 and last_log.timestamp < end:
        hours_delta = end - last_log.timestamp
        hours = hours_delta.seconds/3600
        payload.append({
            'start_time': last_log.timestamp,
            'end_time': end.strftime("%Y-%m-%dT%H:%M:%S"),
            'hours': round(hours, 3)
        })
    return payload


def extract_total_hours_logs_from_FM_logs(logs, end, litres_mode=False):
    print('coming from test transaction', (logs.count()))
    total_hours = 0
    payload = []
    on_flag = False
    start_log = ""
    end_log = ""
    last_log = False
    for (index, log) in enumerate(logs):

        if log.status == 1 and not on_flag:
            print('starter', 'index', index)
            on_flag = True
            start_log = log
        elif log.status == 0 and on_flag:
            print('ender', 'index', index)
            on_flag = False
            end_log = log

            start_time = start_log.timestamp
            end_time = end_log.timestamp
            hours = (end_log.hours - start_log.hours)/3600
            # only log if running hours is > 10 minutes == 0.16hrs
            if hours < GEN_THRESHOLD:
                continue
            temp = {
                'start_time': start_time,
                'end_time': end_time,
                'hours': round(hours, 3)
            }
            if litres_mode:
                litres_consumed = end_log.litres - start_log.litres
                temp['consumption'] = round(litres_consumed, 3)
                try:
                    temp['consumption_rate'] = round(
                        temp['consumption']/temp['hours'], 3)
                except ZeroDivisionError:
                    temp['consumption_rate'] = None
            payload.append(temp)
        # this condition caters for when the equipment/gen is still on
        elif log.status == 1 and on_flag and index == logs.count()-1:
            on_flag = False
            end_log = log

            start_time = start_log.timestamp
            end_time = end_log.timestamp
            hours = (end_log.hours - start_log.hours)/3600
            # only log if running hours is > 10 minutes == 0.16hrs
            if hours < GEN_THRESHOLD:
                continue
            temp = {
                'start_time': start_time,
                'end_time': end_time,
                'hours': round(hours, 3)
            }
            if litres_mode:
                litres_consumed = end_log.litres - start_log.litres
                temp['consumption'] = round(litres_consumed, 3)
                try:
                    temp['consumption_rate'] = round(
                        temp['consumption']/temp['hours'], 3)
                except ZeroDivisionError:
                    temp['consumption_rate'] = None
            payload.append(temp)
    return payload


def PHCN_total_hours_with_logs_report(site: models.Sites, start, end):
    mac_address = site.Device.Device_unique_address
    if site.Site_id == 1:
        mac_address = 'b8:27:eb:fb:00:9f'
    logs = models.GeneratorHours.objects.filter(
        mac_address=mac_address,
        lineID=0,
        timestamp__range=(start, end)
    ).order_by('timestamp')
    payload = extract_total_hours_logs_from_DI_logs(logs, end)
    for entry in payload:
        entry['site_name'] = site.Name
        entry['equipment'] = site.genhours_config.public_power_source_slug
    return payload


def DI_equipment_total_hours_with_logs_report(equipment: models.Equipment, start, end):
    mac_address = equipment.site.Device.Device_unique_address
    if equipment.site.Site_id == 1:
        mac_address = 'b8:27:eb:fb:00:9f'
    logs = models.GeneratorHours.objects.filter(
        mac_address=mac_address,
        lineID=equipment.address,
        timestamp__range=(start, end)
    ).order_by('timestamp')
    payload = extract_total_hours_logs_from_DI_logs(logs, end)
    for entry in payload:
        entry['site_name'] = equipment.site.Name
        entry['equipment'] = equipment.name
        entry['equipment_id'] = equipment.id
    return payload


def FM_equipment_total_hours_with_logs_report(equipment: models.Equipment, start, end):
    mac_address = equipment.site.Device.Device_unique_address
    if equipment.site.Site_id == 1:
        mac_address = 'b8:27:eb:fb:00:9f'
    logs = models.FlowmeterLogs.objects.filter(
        mac_address=mac_address,
        flowmeter_address=equipment.flowmeter.address,
        timestamp__range=(start, end)
    ).order_by('timestamp')
    payload = extract_total_hours_logs_from_FM_logs(logs, end)
    for entry in payload:
        entry['site_name'] = equipment.site.Name
        entry['equipment'] = equipment.name
        entry['equipment_id'] = equipment.id
    # print('fm hours with logs', payload)
    return payload


'''
************************************************
TOTAL HOURS AND LITRES
************************************************
'''


def extract_total_hours_from_logs(logs):
    start_time = ""
    end_time = ""
    on_flag = False
    last_log = None
    total_hours = 0
    for (index, log) in enumerate(logs):
        if log.status == 1 and not on_flag:
            on_flag = True
            start_time = log.timestamp

        elif log.status == 0 and on_flag:
            on_flag = False
            end_time = log.timestamp
            hours_delta = end_time - start_time
            hours = hours_delta.seconds/3600
            if hours < GEN_THRESHOLD:
                continue
            total_hours += hours
        last_log = log

    end = dt.datetime.now()
    if last_log and last_log.status == 1 and last_log.timestamp < end:
        hours_delta = end - last_log.timestamp
        hours = hours_delta.seconds/3600
        total_hours += hours
    return round(total_hours, 3)


def PHCN_total_hours_report(site: models.Sites):
    mac_address = site.Device.Device_unique_address
    if site.Site_id == 1:
        mac_address = 'b8:27:eb:fb:00:9f'
    logs = models.GeneratorHours.objects.filter(
        mac_address=mac_address,
        lineID=0
    ).order_by('timestamp')
    total_hours = extract_total_hours_from_logs(logs)
    return round(total_hours, 3)


def DI_totaliser_hours_report(equipment: models.Equipment):
    mac_address = equipment.site.Device.Device_unique_address
    if equipment.site.Site_id == 1:
        mac_address = 'b8:27:eb:fb:00:9f'
    line_id = equipment.address
    value = equipment.totaliser_hours
    logs = models.GeneratorHours.objects.filter(
        mac_address=mac_address,
        lineID=line_id
    ).order_by('timestamp')

    if logs.count() > 0:
        value += extract_total_hours_from_logs(logs)
    return round(value, 3)


def FM_totaliser_report(equipment: models.Equipment, litres_mode=False):
    mac_address = equipment.site.Device.Device_unique_address
    if equipment.site.Site_id == 1:
        mac_address = 'b8:27:eb:fb:00:9f'
    flowmeter_address = equipment.flowmeter.address
    if litres_mode:
        value = equipment.totaliser_litres
    else:
        value = equipment.totaliser_hours

    logs = models.FlowmeterLogs.objects.filter(
        mac_address=mac_address,
        flowmeter_address=flowmeter_address
    ).order_by('timestamp')
    if logs.count() > 0:
        value += extract_total_hours_from_FM_logs(
            logs, litres_mode=litres_mode)
    return round(value, 3)


'''
****************************************************
DAILY TOTAL HOURS
***************************************************
'''


def extract_daily_total_hours_from_DI_logs(logs):
    total_hours = 0
    last_log = None
    start_time = ""
    end_time = ""
    on_flag = False
    for (index, log) in enumerate(logs):
        if log.status == 1 and not on_flag:
            on_flag = True
            start_time = log.timestamp

        elif log.status == 0 and on_flag:
            on_flag = False
            end_time = log.timestamp
            hours_delta = end_time - start_time
            hours = hours_delta.seconds/3600
            if hours < GEN_THRESHOLD:
                continue
            total_hours += hours
        last_log = log
    if last_log and last_log.status == 1:
        tomorrow = last_log.timestamp + dt.timedelta(1)
        midnight = dt.datetime(year=tomorrow.year,
                               month=tomorrow.month,
                               day=tomorrow.day,
                               hour=0, minute=0, second=0)
        now = dt.datetime.now()
        latest_time = min(midnight, now)
        hours_delta = latest_time - last_log.timestamp
        hours = hours_delta.seconds/3600
        total_hours += hours
    return round(total_hours, 3)


def PHCN_daily_total_hours(site: models.Sites, dates):
    mac_address = site.Device.Device_unique_address
    if site.Site_id == 1:
        mac_address = 'b8:27:eb:fb:00:9f'
    total_hours = []
    for date in dates:
        logs = models.GeneratorHours.objects.filter(
            mac_address=mac_address,
            lineID=0,
            timestamp__date=date
        ).order_by('timestamp')
        hours = extract_daily_total_hours_from_DI_logs(logs)
        total_hours.append(hours)
    return total_hours


def DI_equipment_daily_total_hours(equipment: models.Equipment, dates):
    mac_address = equipment.site.Device.Device_unique_address
    if equipment.site.Site_id == 1:
        mac_address = 'b8:27:eb:fb:00:9f'
    total_hours = []
    for date in dates:
        logs = models.GeneratorHours.objects.filter(
            mac_address=mac_address,
            lineID=equipment.address,
            timestamp__date=date
        ).order_by('timestamp')
        hours = extract_daily_total_hours_from_DI_logs(logs)
        total_hours.append(hours)
    return total_hours


def FM_equipment_daily_total_hours(equipment: models.Equipment, dates):
    mac_address = equipment.site.Device.Device_unique_address
    if equipment.site.Site_id == 1:
        mac_address = 'b8:27:eb:fb:00:9f'
    total_hours = []
    for date in dates:
        logs = models.FlowmeterLogs.objects.filter(
            mac_address=mac_address,
            flowmeter_address=equipment.flowmeter.address,
            timestamp__date=date
        ).order_by('timestamp')
        hours = extract_total_hours_from_FM_logs(logs)
        total_hours.append(hours)
    return total_hours


'''
***************************************************
TOTAL HOURS IN TIME RANGE
**************************************************
'''


def extract_total_hours_in_range_from_DI_logs(logs, end):
    total_hours = 0
    last_log = None
    start_time = ""
    end_time = ""
    on_flag = False
    for (index, log) in enumerate(logs):
        if log.status == 1 and not on_flag:
            on_flag = True
            start_time = log.timestamp

        elif log.status == 0 and on_flag:
            on_flag = False
            end_time = log.timestamp
            hours_delta = end_time - start_time
            hours = hours_delta.seconds/3600
            if hours < GEN_THRESHOLD:
                continue
            total_hours += hours
        last_log = log
    end = dt.datetime.strptime(end, "%Y-%m-%d %H:%M")
    if last_log and last_log.status == 1 and last_log.timestamp.date() == end.date() and last_log.timestamp < end:
        hours_delta = end - last_log.timestamp
        hours = hours_delta.seconds/3600
        total_hours += hours
    return round(total_hours, 3)


def PHCN_total_hours_in_range(site: models.Sites, start, end):
    mac_address = site.Device.Device_unique_address
    if site.Site_id == 1:
        mac_address = 'b8:27:eb:fb:00:9f'
    logs = models.GeneratorHours.objects.filter(
        mac_address=mac_address,
        lineID=0,
        timestamp__range=(start, end)
    ).order_by('timestamp')
    hours = extract_total_hours_in_range_from_DI_logs(logs, end)
    return hours


def DI_equipment_total_hours_in_range(equipment: models.Equipment, start, end):
    mac_address = equipment.site.Device.Device_unique_address
    if equipment.site.Site_id == 1:
        mac_address = 'b8:27:eb:fb:00:9f'
    logs = models.GeneratorHours.objects.filter(
        mac_address=mac_address,
        lineID=equipment.address,
        timestamp__range=(start, end)
    ).order_by('timestamp')
    hours = extract_total_hours_in_range_from_DI_logs(logs, end)
    return hours


def FM_equipment_total_hours_in_range(equipment: models.Equipment, start, end):
    mac_address = equipment.site.Device.Device_unique_address
    if equipment.site.Site_id == 1:
        mac_address = 'b8:27:eb:fb:00:9f'
    logs = models.FlowmeterLogs.objects.filter(
        mac_address=mac_address,
        flowmeter_address=equipment.flowmeter.address,
        timestamp__range=(start, end)
    ).order_by('timestamp')
    hours = extract_total_hours_from_FM_logs(logs)
    return hours


'''
*****************************************************
CONSUMPTION WITH LOGS
*****************************************************
'''


def extract_tanks_consumption(tank_ids, payload):
    start = payload['start_time']
    end = payload['end_time']
    # small reparsing for consistency
    start = start.strftime("%Y-%m-%d %H:%M")
    end = " ".join(end.split('T')) if isinstance(
        end, str) else end.strftime("%Y-%m-%d %H:%M")
    consumption = 0
    for tank_id in tank_ids:
        report = TimeRangeConsumptionReport(
            tank_id, start, end).get_consumption_report()
        if report:
            new_consumption = report[0].get('Consumption', 0)
            if new_consumption >= 0:
                consumption += new_consumption
    payload['consumption'] = round(consumption, 3)
    try:
        payload['consumption_rate'] = round(
            payload['consumption']/payload['hours'], 3)
    except ZeroDivisionError:
        payload['consumption_rate'] = None
    return payload


def TL_equipment_litres_consumed_with_logs_report(equipment, hours_payload):
    '''
    FOr tank levels,
    - Extract payload of equipment running hours with timestamp
    - For each entry, get the corresponding consumption from the connected tank
    '''
    tanks = equipment.source_tanks.values_list('Tank_id', flat=True)
    source = "Tank logs"
    if not tanks:
        return hours_payload
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(
            extract_tanks_consumption,
            tanks, payload) for payload in hours_payload]
        for future in as_completed(futures):
            future.result()
    for entry in hours_payload:
        entry['source'] = source
    return hours_payload


def FM_equipment_litres_consumed_with_logs_report(equipment, start, end):
    mac_address = equipment.site.Device.Device_unique_address
    if equipment.site.Site_id == 1:
        mac_address = 'b8:27:eb:fb:00:9f'
    logs = models.FlowmeterLogs.objects.filter(
        mac_address=mac_address,
        flowmeter_address=equipment.flowmeter.address,
        timestamp__range=(start, end)
    ).order_by('timestamp')
    payload = extract_total_hours_logs_from_FM_logs(
        logs, end, litres_mode=True)
    source = "Flowmeter"
    for entry in payload:
        entry['site_name'] = equipment.site.Name
        entry['equipment'] = equipment.name
        entry['source'] = source
    return payload


'''
**************************************************
DAILY LITRES CONSUMPTION
**************************************************
'''


def extract_daily_tanks_consumption(tank_ids, start, end):
    consumptions = []
    for tank_id in tank_ids:
        report = DailyConsumptionReport(
            tank_id, start, end).get_consumption_report()
        if report:
            tanks_consumptions = [entry['Consumption'] for entry in report]
            if consumptions:
                consumptions = list(map(lambda entry: sum(
                    entry), zip(consumptions, tanks_consumptions)))
            else:
                consumptions = tanks_consumptions
    return consumptions


def TL_equipment_daily_litres_consumed(equipment: models.Equipment, dates):
    # Get daily litres consumption for source tanks for each day
    tanks = equipment.source_tanks.values_list('Tank_id', flat=True)
    if not tanks:
        return []
    daily_consumptions = extract_daily_tanks_consumption(
        tanks, dates[0], dates[-1])
    return daily_consumptions


def FM_equipment_daily_litres_consumed(equipment: models.Equipment, dates):
    mac_address = equipment.site.Device.Device_unique_address
    if equipment.site.Site_id == 1:
        mac_address = 'b8:27:eb:fb:00:9f'
    total_litres = []
    for date in dates:
        logs = models.FlowmeterLogs.objects.filter(
            mac_address=mac_address,
            flowmeter_address=equipment.flowmeter.address,
            timestamp__date=date
        ).order_by('timestamp')
        litres = extract_total_hours_from_FM_logs(logs, litres_mode=True)
        total_litres.append(litres)
    return total_litres


def Daily_24hrs_Interval_range_FM_equipment_litres_consumed(equipment, date, eachHour):
    mac_address = equipment.site.Device.Device_unique_address
    if equipment.site.Site_id == 1:
        mac_address = 'b8:27:eb:fb:00:9f'
    logs = models.FlowmeterLogs.objects.filter(mac_address=mac_address, flowmeter_address=equipment.flowmeter.address,
                                               timestamp__date=date, timestamp__hour=eachHour).order_by('timestamp')
    litres = extract_total_hours_from_FM_logs(logs, litres_mode=True)
    try:
        start_forward_litre = logs.first().forward_litres
        start_backward_litre = logs.first().backward_litres
    except AttributeError:
        start_forward_litre = 0
        start_backward_litre = 0
    try:
        end_forward_litre = logs.last().forward_litres
        end_backward_litre = logs.last().backward_litres

    except AttributeError:
        end_forward_litre = 0
        end_backward_litre = 0

    forward_consumption = end_forward_litre - start_forward_litre
    backward_consumption = end_backward_litre - start_backward_litre
    consumption_rate = logs.aggregate(Avg('consumption_rate'))
    forward_consumption_rate = logs.aggregate(Avg('forward_fuel_rate'))
    reverse_consumption_rate = logs.aggregate(Avg('backward_fuel_rate'))
    average_temperature = logs.aggregate(Avg('temperature'))
    return litres, forward_consumption, backward_consumption, consumption_rate['consumption_rate__avg'], forward_consumption_rate['forward_fuel_rate__avg'], reverse_consumption_rate['backward_fuel_rate__avg'], average_temperature['temperature__avg']


'''
*************************************************
LITRES CONSUMED IN TIME RANGE
*************************************************
'''


def extract_tanks_consumption_in_date_range(tank_ids, start, end):
    consumption = 0
    for tank_id in tank_ids:
        report = TimeRangeConsumptionReport(
            tank_id, start, end).get_consumption_report()
        if report:
            new_consumption = report[0].get('Consumption', 0)
            if new_consumption > 0:
                consumption += new_consumption
    return consumption


def TL_equipment_litres_consumed_in_range(equipment, start, end):
    tanks = equipment.source_tanks.values_list('Tank_id', flat=True)
    if not tanks:
        return 0
    return extract_tanks_consumption_in_date_range(tanks, start, end)


def FM_equipment_litres_consumed_in_range(equipment, start, end):
    mac_address = equipment.site.Device.Device_unique_address
    if equipment.site.Site_id == 1:
        mac_address = 'b8:27:eb:fb:00:9f'
    logs = models.FlowmeterLogs.objects.filter(
        mac_address=mac_address,
        flowmeter_address=equipment.flowmeter.address,
        timestamp__range=(start, end)
    ).order_by('timestamp')
    litres = extract_total_hours_from_FM_logs(logs, litres_mode=True)
    return litres
