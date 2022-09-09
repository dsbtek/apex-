
from concurrent.futures import ThreadPoolExecutor, as_completed

import datetime as dt
from backend import models
from . import reports as r
from . import serializer
from . import queries


def date_range(*args):
    if len(args) != 3:
        raise SyntaxError("You must include start, stop and step as args")
    start, stop, step = args
    if start < stop:
        def cmp(a, b): return a < b
        def inc(a): return a + step
    else:
        def cmp(a, b): return a > b
        def inc(a): return a - step
    output = [start]
    while cmp(start, stop):
        start = inc(start)
        output.append(start)

    return output


# def convertDict(equipments):
#     title = ["id", "name", "product", "site", "flowmeter", "address", "active"]
#     result = {}
#     for each in len(equipments):
#         result[title[each]] = equipments[each]

'''
**************************************
POWERMETER REPORT AND CONSUMPTION PER CYCLE
**************************************
'''


def get_power(start, end, equipments_id):
    return queries.get_powermeterlogs(start, end, equipments_id)


def get_flow(start, end, mac_addresses, flowmeter_add):
    return serializer.FlowmeterLogsSerializer(models.FlowmeterLogs.objects.filter(timestamp__gt=start, timestamp__lt=end, mac_address__in=mac_addresses, flowmeter_address__in=flowmeter_add).order_by('-timestamp'), many=True).data


def get_power_consumption_logs(equipments_id, start, end):
    mac_addresses, flowmeter_add = [], []

    equipments = models.Equipment.objects.filter(id__in=equipments_id)

    for each_equipment in equipments:
        try:
            mac_addresses.append(
                each_equipment.site.Device.Device_unique_address)
            flowmeter_add.append(each_equipment.flowmeter.address)
        except Exception as e:
            continue
    with ThreadPoolExecutor() as executor:
        power = [executor.submit(get_power, start, end, equipments_id)]
        flow = [executor.submit(get_flow, start, end,
                                mac_addresses, flowmeter_add)]

        for each in as_completed(power):
            powermeter_logs = each.result()

        for each in as_completed(flow):
            flowmeter_logs = each.result()
        for each_power in powermeter_logs:
            for each_flow in flowmeter_logs:
                if each_power['uid'] == each_flow['uid'] and each_power['uid'] != 0 and each_power['uid'] != '0':
                    each_power['consumption_rate'] = each_flow['consumption_rate']
                    flowmeter_logs.remove(each_flow)
                    break
            if 'consumption_rate' not in each_power.keys():
                each_power['consumption_rate'] = "Not Available"
    return powermeter_logs


def get_on_off_report(equipments_id, powermeter_logs):

    logs = powermeter_logs[::-1]
    running = False
    sum_voltage, sum_current, sum_power, sum_consumption_rate = 0, 0, 0, 0
    counter = 0

    # result columns: Site_Name, Equipments_Name, start, end,
    # Average Voltage, Average Current, Average Power,
    # Consumption Rate, Equipment_id, duration
    result = []
    each_log = {}
    print('initial logs', len(powermeter_logs))
    print('modified logs', len(logs))
    print('equip id', equipments_id)

    for each_equipment_id in equipments_id:
        equipment_obj = models.Equipment.objects.filter(
            pk=each_equipment_id).values()[0]
        equipment_name = equipment_obj['name']
        site_name = models.Sites.objects.get(pk=equipment_obj['site_id']).Name

        for each in powermeter_logs:
            # compute running hours parameters if engine start running
            if each['status'] == 1 and running == False and each['equipment_id'] == each_equipment_id:
                print('currenly running...')

                each_log['site_name'] = site_name
                each_log['equipment_name'] = equipment_name
                each_log['equipment_id'] = each_equipment_id
                each_log['start'] = each['timestamp']
                sum_voltage += each['voltage_a']
                sum_current += each['current_a']
                sum_power += each['power_a']
                try:
                    sum_consumption_rate += each['consumption_rate']
                except:
                    sum_consumption_rate = each['consumption_rate']
                counter += 1
                running = True
                # print('current vol', sum_voltage)
                # print('current cur', sum_current)
                # print('current pow', sum_power)
                # print('------------')

            # compute running hours parameter if engine keeps running
            if each['status'] == 1 and running == True and each['equipment_id'] == each_equipment_id:
                print('coming from 2nd')
                sum_voltage += each['voltage_a']
                sum_current += each['current_a']
                sum_power += each['power_a']
                sum_consumption_rate += each['consumption_rate']
                counter += 1
                # print('------2nd------')
                # print('current vol', sum_voltage)
                # print('current cur', sum_current)
                # print('current pow', sum_power)
                # print('------------')

            # finish compute running hours when engine just stop running hours
            if each['status'] == 0 and running == True and each['equipment_id'] == each_equipment_id:
                print('it should be added')
                each_log['end'] = each['timestamp']
                each_log['average_voltage'] = sum_voltage/counter
                each_log['average_current'] = sum_current/counter
                each_log['average_power'] = sum_power/counter
                each_log['total_consumption'] = sum_consumption_rate
                each_log['duration'] = each_log['end'] - each_log['start']
                running = False
                counter = 0
                result.append(each_log)
                each_log = {}
    print(result)
    return result


def getSitesAndEquipments(site_ids):
    result = queries.get_equipments_in_site(site_ids)
    for each_site in result:
        for count in range(len(each_site['equipments'])):
            data = queries.getStatusOfequipment(
                each_site['equipments'][count][0], each_site['site_name'])
            try:
                time_lag = dt.timedelta(seconds=300)
                diff_lasttime_now = dt.datetime.now() - data[0]['timestamp']

                if diff_lasttime_now >= time_lag:
                    each_site['equipments'][count].append(0)
                else:
                    each_site['equipments'][count].append(data[0]['status'])
            except IndexError:
                each_site['equipments'][count].append(0)
    return result


'''
**************************************
DASHBOARD DETAILS
**************************************
'''


def get_equipment_dashboard_details(equipment: models.Equipment):
    # get dashboard factory
    dashboard = EquipmentDashboardFactory(equipment)
    dashboard_payload = {}
    hour_dashboard = dashboard.create_hour_dashboard()
    litre_dashboard = dashboard.create_litres_dashboard()
    maintenance_dashboard = dashboard.create_maintenance_dashboard()
    if hour_dashboard:
        dashboard_payload.update(hour_dashboard.aggregate())
    if maintenance_dashboard:
        dashboard_payload.update(maintenance_dashboard.aggregate())
    if litre_dashboard:
        dashboard_payload.update(litre_dashboard.aggregate())
    return [dashboard_payload]


def get_phcn_dashboard_details(site: models.Sites):
    dashboard = PHCNDashboardHoursDetail(site)
    return [dashboard.aggregate()]


'''
******************************************
HOURS REPORTS AND ANALYTICS
*****************************************
'''


def get_equipment_total_hours_log_report(equipment: models.Equipment, start, end):
    if equipment.running_hours_source in ['FM', 'HYB-FM']:
        return r.FM_equipment_total_hours_with_logs_report(equipment, start, end)
    else:
        return r.DI_equipment_total_hours_with_logs_report(equipment, start, end)


def get_phcn_total_hours_log_report(site: models.Sites, start, end):
    return r.PHCN_total_hours_with_logs_report(site, start, end)


def get_equipment_daily_total_hours(equipment: models.Equipment, dates):
    if equipment.running_hours_source in ['FM', 'HYB-FM']:
        hours = r.FM_equipment_daily_total_hours(equipment, dates)
    else:
        hours = r.DI_equipment_daily_total_hours(equipment, dates)
    return {"name": equipment.name, "hours": hours}


def get_phcn_daily_total_hours(site: models.Sites, dates):
    hours = r.PHCN_daily_total_hours(site, dates)
    return {"name": site.genhours_config.public_power_source_slug, "hours": hours}


def get_equipment_total_hours_in_range(equipment: models.Equipment, start, end):
    if equipment.running_hours_source in ['FM', 'HYB-FM']:
        hours = r.FM_equipment_total_hours_in_range(equipment, start, end)
    else:
        hours = r.DI_equipment_total_hours_in_range(equipment, start, end)
    return {equipment.name: hours}


def get_phcn_total_hours_in_range(site: models.Sites, start, end):
    hours = r.PHCN_total_hours_in_range(site, start, end)
    return {site.genhours_config.public_power_source_slug: hours}


def get_flowmeter_test_transaction_report(equipment: models.Equipment, start, end):

    hours_report = get_equipment_total_hours_log_report(equipment, start, end)
    for trx in hours_report:
        # get comment if any
        end_time = trx["end_time"].strftime("%Y-%m-%dT%H:%M:%S")
        try:
            comment_object = models.FlowmeterTransactionComment.objects.get(
                equipment=equipment,
                trx_end_time=end_time
            )
            trx["comment_id"] = comment_object.id
            trx["comment"] = comment_object.comment
            trx["comment_author"] = comment_object.comment_edit_author if comment_object.comment_edit_author else comment_object.comment_create_author
            trx["comment_time"] = comment_object.comment_edit_time
        except models.FlowmeterTransactionComment.DoesNotExist:
            trx["comment_id"] = None
            trx["comment"] = ""
            trx["comment_author"] = None
            trx["comment_time"] = None

    return hours_report


'''
******************************************
CONSUMPTION REPORTS AND ANALYTICS
*****************************************
'''


def get_equipment_litres_consumption_log_report(equipment: models.Equipment, start, end):
    '''
    Dependent on the running hours report
    '''
    if equipment.litres_consumed_source in ['TL', 'HYB-TL']:
        equipment_hours_report_payload = get_equipment_total_hours_log_report(
            equipment, start, end)
        return r.TL_equipment_litres_consumed_with_logs_report(equipment, equipment_hours_report_payload)
    else:
        return r.FM_equipment_litres_consumed_with_logs_report(equipment, start, end)


def get_equipment_daily_litres_consumed(equipment: models.Equipment, dates):
    if equipment.litres_consumed_source in ['TL', 'HYB-TL']:
        litres = r.TL_equipment_daily_litres_consumed(equipment, dates)
    else:
        litres = r.FM_equipment_daily_litres_consumed(equipment, dates)
    return {"name": equipment.name, "litres": litres}


def get_equipment_daily_24hrs_interval_litres_consumption_log_report(equipment: models.Equipment, date, eachHour):

    if equipment.litres_consumed_source in ['TL', 'HYB-TL']:
        # todo implement
        litres = r.Daily_24hrs_Interval_range_FM_equipment_litres_consumed(
            equipment, date, eachHour)
    else:
        litres, forward_consumption, backward_consumption, consumption_rate, forward_consumption_rate, reverse_consumption_rate, average_temperature = r.Daily_24hrs_Interval_range_FM_equipment_litres_consumed(
            equipment, date, eachHour)
    return {"name": equipment.name, "litres": litres, "HourlyInterval": eachHour, "forward_consumption": forward_consumption, "backward_consumption": backward_consumption, "consumption_rate": consumption_rate, "forward_consumption_rate": forward_consumption_rate, "reverse_consumption_rate": reverse_consumption_rate, "average_temperature": average_temperature}


def get_equipment_daily_consumption_rates(equipment: models.Equipment, dates):
    hours = get_equipment_daily_total_hours(equipment, dates)["hours"]
    if equipment.litres_consumed_source in ['TL', 'HYB-TL']:
        litres = r.TL_equipment_daily_litres_consumed(equipment, dates)
    else:
        litres = r.FM_equipment_daily_litres_consumed(equipment, dates)

    consumption_rates = list(map(lambda entry: round(
        entry[0]/entry[1], 3) if entry[1] > 0 else None, zip(litres, hours)))
    return {"name": equipment.name, "rates": consumption_rates}


def get_equipment_litres_consumed_in_range(equipment: models.Equipment, start, end):
    if equipment.litres_consumed_source in ['TL', 'HYB-TL']:
        litres = r.TL_equipment_litres_consumed_in_range(equipment, start, end)
    else:
        litres = r.FM_equipment_litres_consumed_in_range(equipment, start, end)
    return {equipment.name: litres}


class EquipmentDashboardFactory:
    def __init__(self, equipment: models.Equipment):
        self.equipment = equipment
        self.hours_source = equipment.running_hours_source
        self.litres_source = equipment.litres_consumed_source

    def create_hour_dashboard(self):
        if self.hours_source in ['DI', 'HYB-DI']:
            return DIEquipmentDashboardHoursDetail(self.equipment)
        elif self.hours_source in ['FM', 'HYB-FM']:
            return FMEquipmentDashboardHoursDetail(self.equipment)

    def create_litres_dashboard(self):
        if self.litres_source in ['FM', 'HYB-FM']:
            return FMDashboardLitresDetail(self.equipment)

    def create_maintenance_dashboard(self):
        if hasattr(self.equipment, 'maintenance_config'):
            return MaintenanceDetail(self.equipment)


class EquipmentDashboardHoursDetail:
    '''
    - Online status
    - totaliser hours
    - Last updated time
    '''

    def __init__(self, equipment):
        self.equipment = equipment
        self.latest_log = self.get_latest_equipment_log()

    def get_latest_equipment_log(self):
        raise NotImplementedError('Should be implemented by subclass')

    def get_totaliser_hours(self):
        raise NotImplementedError('Should be implemented by subclass')

    def get_online_status(self):
        raise NotImplementedError('Should be implemented by subclass')

    def get_last_updated_time(self):
        raise NotImplementedError('Should be implemented by subclass')

    def get_hour_source(self):
        if self.equipment.running_hours_source in ['FM', 'HYB-FM']:
            return "Flowmeter"
        elif self.equipment.running_hours_source in ['DI', 'HYB-DI']:
            return "Digital Input"

    def aggregate(self):
        return {
            'equipment': self.equipment.name,
            'site_name': self.equipment.site.Name,
            'equipment_type': self.equipment.equipment_type,
            'online_status': self.get_online_status(),
            'totaliser_hours': self.get_totaliser_hours(),
            'last_updated_time': self.get_last_updated_time(),
            'hour_source': self.get_hour_source()
        }


class PHCNDashboardHoursDetail:
    def __init__(self, site):
        self.site = site
        self.latest_log = self.get_latest_equipment_log()

    def get_latest_equipment_log(self):
        mac_address = self.site.Device.Device_unique_address
        if self.site.Site_id == 1:
            mac_address = 'b8:27:eb:fb:00:9f'
        log = models.GeneratorHours.objects.filter(
            mac_address=mac_address, lineID=0).last()
        return log

    def get_online_status(self):
        if self.latest_log:
            return bool(self.latest_log.status)
        else:
            return False

    def get_last_updated_time(self):
        if self.latest_log:
            return self.latest_log.timestamp
        else:
            return None

    def get_totaliser_hours(self):
        '''
        Totaliser hours is gotten from equipment model
        1. Get latest updated totaliser time from model
        2. Run a report query on all the logs between then and now
        '''
        return r.PHCN_total_hours_report(self.site)

    def aggregate(self):
        return {
            'equipment': self.site.genhours_config.public_power_source_slug,
            'site_name': self.site.Name,
            'online_status': self.get_online_status(),
            'totaliser_hours': self.get_totaliser_hours(),
            'last_updated_time': self.get_last_updated_time(),
        }


class FMEquipmentDashboardHoursDetail(EquipmentDashboardHoursDetail):

    def get_latest_equipment_log(self):
        mac_address = self.equipment.site.Device.Device_unique_address
        if self.equipment.site.Site_id == 1:
            mac_address = 'b8:27:eb:fb:00:9f'
        log = models.FlowmeterLogs.objects.filter(
            mac_address=mac_address, flowmeter_address=self.equipment.flowmeter.address).last()
        return log

    def get_online_status(self):
        if self.latest_log:
            return bool(self.latest_log.status)
        else:
            return False

    def get_last_updated_time(self):
        if self.latest_log:
            return self.latest_log.timestamp
        else:
            return None

    def get_totaliser_hours(self):
        # self.equipment.refresh_from_db()
        total_hours = r.FM_totaliser_report(self.equipment)
        # total_hours = self.equipment.totaliser_hours
        return round(total_hours, 3)


class DIEquipmentDashboardHoursDetail(EquipmentDashboardHoursDetail):
    def get_latest_equipment_log(self):
        mac_address = self.equipment.site.Device.Device_unique_address
        if self.equipment.site.Site_id == 1:
            mac_address = 'b8:27:eb:fb:00:9f'

        log = models.GeneratorHours.objects.filter(
            mac_address=mac_address, lineID=self.equipment.address).last()
        return log

    def get_online_status(self):
        if self.latest_log:
            return bool(self.latest_log.status)
        else:
            return False

    def get_last_updated_time(self):
        if self.latest_log:
            return self.latest_log.timestamp
        else:
            return None

    def get_totaliser_hours(self):
        '''
        Totaliser hours is gotten from equipment model
        1. Get latest updated totaliser time from model
        2. Run a report query on all the logs between then and now
        '''
        return r.DI_totaliser_hours_report(self.equipment)


class FMDashboardLitresDetail:
    def __init__(self, equipment):
        self.equipment = equipment
        self.latest_log = self.get_latest_equipment_log()
    '''
    - totaliser litres
    - Current temperature
    - Average consumption rate
    '''

    def get_latest_equipment_log(self):
        mac_address = self.equipment.site.Device.Device_unique_address
        if self.equipment.site.Site_id == 1:
            mac_address = 'b8:27:eb:fb:00:9f'
        log = models.FlowmeterLogs.objects.filter(
            mac_address=mac_address,
            flowmeter_address=self.equipment.flowmeter.address
        ).order_by('timestamp').last()
        return log

    def get_litres_consumed(self):
        # self.equipment.refresh_from_db()
        total_litres = r.FM_totaliser_report(self.equipment, litres_mode=True)
        # total_litres = self.equipment.totaliser_litres
        return round(total_litres, 3)

        '''
        mac_address = self.equipment.site.Device.Device_unique_address
        if self.equipment.site.Site_id == 1:
            mac_address = 'b8:27:eb:fb:00:9f'
        logs = models.FlowmeterLogs.objects.filter(
            mac_address=mac_address,
            flowmeter_address=self.equipment.flowmeter.address
        ).order_by('timestamp')
        if logs:
            first_log_litre = logs.first().litres
            latest_log_litre = logs.last().litres
            total_litres_consumed = latest_log_litre - first_log_litre
            return round(total_litres_consumed, 3)
        else:
            return 0
        '''

    def get_current_temperature(self):
        if self.latest_log:
            return self.latest_log.temperature
        else:
            return None

    def get_consumption_rate(self):
        if self.latest_log:
            return round(self.latest_log.consumption_rate, 3)
        else:
            return None

    def get_forward_chamber_rate(self):
        if self.latest_log:
            return round(self.latest_log.forward_fuel_rate, 3)
        else:
            return None

    def get_reverse_chamber_rate(self):
        if self.latest_log:
            return round(self.latest_log.backward_fuel_rate, 3)
        else:
            return None

    def aggregate(self):
        payload = {
            'equipment': self.equipment.name,
            'total_litres_consumed': self.get_litres_consumed(),
            'current_temperature': self.get_current_temperature(),
            'consumption_rate': self.get_consumption_rate(),
            'forward_rate': self.get_forward_chamber_rate(),
            'reverse_rate': self.get_reverse_chamber_rate()
        }
        return payload


class MaintenanceDetail:
    def __init__(self, equipment):
        self.equipment = equipment
        self.maintenance_config = self.get_maintenance_config()

    def get_maintenance_config(self):
        try:
            config = models.MaintenanceConfig.objects.get(
                equipment__pk=self.equipment.pk)
        except models.MaintenanceConfig.DoesNotExist:
            config = None
        return config

    def last_maintenance_details(self):
        latest_maintenance_record = models.MaintenanceInfo.objects.filter(
            equipment__pk=self.equipment.pk).last()
        if latest_maintenance_record:
            return latest_maintenance_record.maintenance_date, latest_maintenance_record.genhours
        else:
            return None, None

    def next_maintenance_details(self):
        latest_date, latest_genhours = self.last_maintenance_details()
        if self.maintenance_config and latest_date and latest_genhours:
            config_mode = self.maintenance_config.mode
            if config_mode == 'HR/D':
                next_maintenance_day = latest_date + \
                    dt.timedelta(days=self.maintenance_config.days)
                next_maintenance_hours = latest_genhours + self.maintenance_config.hours
            elif config_mode == 'SCH':
                next_maintenance_day = latest_date + \
                    dt.timedelta(days=self.maintenance_config.scheduled_days)
                next_maintenance_hours = None
            return next_maintenance_day, next_maintenance_hours
        else:
            return None, None

    def aggregate(self):
        latest_date, latest_genhours = self.last_maintenance_details()
        next_date, next_genhours = self.next_maintenance_details()
        config_mode = self.maintenance_config.mode if self.maintenance_config else None
        payload = {
            'equipment': self.equipment.name,
            'maintenance_mode': config_mode,
            'latest_maintenance_date': latest_date,
            'latest_maintenance_genhours': latest_genhours,
            'next_maintenance_date': next_date,
            'next_maintenance_genhours': next_genhours
        }
        return payload


def main():
    dash = DIEquipmentDashboardHoursDetail('b8:27:eb:fb:00:9f', 1)


if __name__ == '__main__':
    main()
