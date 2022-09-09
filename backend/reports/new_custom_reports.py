import datetime as dt

from . import queries as q
from ..smarteye_logs.utils import update_tank_records
from backend import models


'''
Single Tank Id is passed for reporting
'''

'''
*****************
FACTORIES
*****************
'''


class ConsumptionReportFactory:
    def get_consumption_report_type(self, report_type):
        if report_type == 'Daily':
            return DailyConsumptionReport
        elif report_type == 'Hourly':
            return HourlyConsumptionReport
        else:
            return TimeRangeConsumptionReport


class DeliveryReportFactory:
    def get_delivery_report_type(self, tank_controller):
        if tank_controller == 'TLS':
            return AutomaticDeliveryReport
        else:
            return ManualDeliveryReport


'''
The Consumption and Delivery algorithm are kind of tightly coupled (idk if this is good?)
However, it is so because the consumption formula is given as:
consumption = (opening_volume + delivery) - closing volume
Hence, a consumption report needs the delivery algorithm to compute the consumption.

Edit: I think it is wise to make the report a class with consumption and delivery algo 
as methods instead of having two separate classes for consumption and Delivery

Edit2: Let the report be a superclass which consumptionClass and deliveryClass can subclass
(Template method pattern)
'''

'''
****************
REPORT BASE SUPERCLASS
****************
'''


class Report:
    def __init__(self, tank_id, start, end):
        self.tank_id = tank_id
        self.start_date = start
        self.end_date = end
        self.tank = models.Tanks.objects.get(pk=tank_id)

    def get_logs(self):
        logs = q.extract_tank_logs(
            self.tank_id, self.start_date, self.end_date)
        updated_logs = update_tank_records(logs)
        return updated_logs


'''
************************************
ABSTRACT CONSUMPTION REPORT SUBCLASS
************************************
'''


class ConsumptionReport(Report):

    delivery_threshold = 10

    def categorise_logs(self):
        '''
        returns a generator of log_sets
        '''
        raise NotImplementedError("A subclass must implement this")

    def get_consumption_report(self):
        raise NotImplementedError("A subclass must implement this")


'''
************************************
CONCRETE CONSUMPTION REPORT CLASSES
************************************
'''


class DailyConsumptionReport(ConsumptionReport):

    delivery_threshold = 300

    def categorise_logs(self):
        all_logs = self.get_logs()
        if all_logs:
            start_date = all_logs[0]["log_time_date"]
            end_date = all_logs[-1]["log_time_date"]
            start_date_native = dt.datetime.strptime(start_date, "%Y-%m-%d")
            end_date_native = dt.datetime.strptime(end_date, "%Y-%m-%d")

            while start_date_native <= end_date_native:
                day_logs = [
                    log for log in all_logs if log["log_time_date"] == start_date]
                if day_logs:
                    yield day_logs

                start_date_native += dt.timedelta(days=1)
                start_date = start_date_native.strftime("%Y-%m-%d")
        else:
            yield []

    def get_consumption_report(self):
        logset_generator = self.categorise_logs()
        consumptions = []
        for logset in logset_generator:
            # get total delivery
            if len(logset) == 0:
                continue
            delivery_report = DeliveryReportFactory(
            ).get_delivery_report_type(self.tank.Tank_controller)
            delivery_start_time = logset[0]["log_time"]
            delivery_end_time = logset[-1]["log_time"]
            delivery = delivery_report(self.tank_id, delivery_start_time,
                                       delivery_end_time).extract_delivery_value_from_logs(logset)
            # delivery = 0 if delivery < self.delivery_threshold else delivery

            capacity = logset[0]['capacity']
            opening_volume = logset[0]['Volume']
            opening_percent = "{0:.3f}".format(
                (float(opening_volume) / float(capacity))*100)
            closing_volume = logset[-1]['Volume']
           
            closing_percent = "{0:.3f}".format(
                (float(closing_volume) / float(capacity))*100)
            consumption_val = (float(opening_volume) +
                               delivery)-float(closing_volume)
            consumption = 0 if consumption_val < 0 else consumption_val

            site_name = logset[0]['site_name']
            tank_name = logset[0]['tank_name']
            read_at_date = logset[0]['log_time_date']
            unit = logset[0]['Unit']
            product = logset[0]['product']

            log = {
                'Site_name': site_name, 'Tank_name': tank_name,
                'Date': read_at_date,
                'Opening_stock': opening_volume, 'OpeningPercentage': opening_percent, 'Closing_stock': closing_volume,
                'ClosingPercentage': closing_percent, 'Consumption': consumption, 'Delivery': delivery,
                'Unit': unit, 'Product': product
            }
            consumptions.append(log)
        return consumptions


class HourlyConsumptionReport(ConsumptionReport):
    delivery_threshold = 100

    def categorise_logs(self):
        all_logs = self.get_logs()
        if all_logs:
            start_hour = all_logs[0]["log_time_hour"]
            end_hour = all_logs[-1]["log_time_hour"]
            start_hour_native = dt.datetime.strptime(start_hour, "%Y-%m-%d %H")
            end_hour_native = dt.datetime.strptime(end_hour, "%Y-%m-%d %H")

            while start_hour_native <= end_hour_native:
                hour_logs = [
                    log for log in all_logs if log["log_time_hour"] == start_hour]
                if hour_logs:
                    yield hour_logs

                start_hour_native += dt.timedelta(hours=1)
                start_hour = start_hour_native.strftime("%Y-%m-%d %H")
        else:
            yield []

    def get_consumption_report(self):
        logset_generator = self.categorise_logs()
        consumptions = []
        for logset in logset_generator:
            if len(logset) == 0:
                continue
            # get total delivery
            delivery_report = DeliveryReportFactory(
            ).get_delivery_report_type(self.tank.Tank_controller)
            delivery_start_time = logset[0]["log_time"]
            delivery_end_time = logset[-1]["log_time"]
            delivery = delivery_report(self.tank_id, delivery_start_time,
                                       delivery_end_time).extract_delivery_value_from_logs(logset)
            # delivery = 0 if delivery < self.delivery_threshold else delivery

            capacity = logset[0]['capacity']
            opening_volume = logset[0]['Volume']
            opening_percent = "{0:.3f}".format(
                (float(opening_volume) / float(capacity))*100)
            closing_volume = logset[-1]['Volume']
            closing_percent = "{0:.3f}".format(
                (float(closing_volume) / float(capacity))*100)
            consumption_val = (float(opening_volume) +
                               delivery)-float(closing_volume)
            consumption = 0 if consumption_val < 0 else consumption_val

            site_name = logset[0]['site_name']
            tank_name = logset[0]['tank_name']
            read_at_hour = logset[0]['log_time_hour']
            unit = logset[0]['Unit']
            product = logset[0]['product']

            log = {
                'Site_name': site_name, 'Tank_name': tank_name,
                'Date': read_at_hour,
                'Opening_stock': opening_volume, 'OpeningPercentage': opening_percent, 'Closing_stock': closing_volume,
                'ClosingPercentage': closing_percent, 'Consumption': consumption, 'Delivery': delivery,
                'Unit': unit, 'Product': product
            }
            consumptions.append(log)
        return consumptions


class TimeRangeConsumptionReport(ConsumptionReport):
    delivery_threshold = 100

    def categorise_logs(self):
        all_logs = self.get_logs()
        yield all_logs

    def get_consumption_report(self):
        logset_generator = self.categorise_logs()
        consumptions = []
        for logset in logset_generator:
            if len(logset) == 0:
                continue
            # get total delivery
            delivery_report = DeliveryReportFactory(
            ).get_delivery_report_type(self.tank.Tank_controller)
            delivery_start_time = logset[0]["log_time"]
            delivery_end_time = logset[-1]["log_time"]
            delivery = delivery_report(self.tank_id, delivery_start_time,
                                       delivery_end_time).extract_delivery_value_from_logs(logset)
            # delivery = 0 if delivery < self.delivery_threshold else delivery

            capacity = logset[0]['capacity']
            opening_volume = logset[0]['Volume']
            opening_percent = "{0:.3f}".format(
                (float(opening_volume) / float(capacity))*100)
            closing_volume = logset[-1]['Volume']
            closing_percent = "{0:.3f}".format(
                (float(closing_volume) / float(capacity))*100)
            consumption_val = (float(opening_volume) +
                               delivery)-float(closing_volume)
            consumption = 0 if consumption_val < 0 else consumption_val

            site_name = logset[0]['site_name']
            tank_name = logset[0]['tank_name']
            read_at_hour = logset[0]['log_time_hour']
            unit = logset[0]['Unit']
            product = logset[0]['product']

            log = {
                'Site_name': site_name, 'Tank_name': tank_name,
                'Start_time': self.start_date, 'End_time': self.end_date,
                'Opening_stock': opening_volume, 'OpeningPercentage': opening_percent, 'Closing_stock': closing_volume,
                'ClosingPercentage': closing_percent, 'Consumption': consumption, 'Delivery': delivery,
                'Unit': unit, 'Product': product
            }
            consumptions.append(log)
        return consumptions


'''
************************************
ABSTRACT DELIVERY REPORT SUBCLASS
************************************
'''


class DeliveryReport(Report):
    def extract_delivery_value_from_logs(self, logs):
        raise NotImplementedError("Subclass should implement this method")

    def extract_delivery_logs_from_logs(self, logs):
        raise NotImplementedError("Subclass should implement this method")

    def get_delivery_report(self):
        raise NotImplementedError("Subclass should implement this method")


'''
************************************
CONCRETE DELIVERY REPORT CLASSES
************************************
'''


class AutomaticDeliveryReport(DeliveryReport):
    def get_logs(self):
        delivery_logs = q.extract_tls_delivery_logs(
            self.tank_id, self.start_date, self.end_date)
        return delivery_logs

    def extract_delivery_value_from_logs(self, logs):
        logs = self.get_logs()
        return sum(float(log['Delivery']) for log in logs)

    def extract_delivery_logs_from_logs(self, logs):
        logs = self.get_logs()
        return logs

    def get_delivery_report(self):
        deliveries = self.extract_delivery_logs_from_logs(True)
        return deliveries


class ManualDeliveryReport(DeliveryReport):
    def delivery_extractor_factory(self):
        if self.tank.UOM == 'm3':
            return self.big_tanks_delivery_extractor
        else:
            return self.normal_tanks_delivery_extractor

    def extract_delivery_value_from_logs(self, logs):
        delivery_extractor = self.delivery_extractor_factory()
        return delivery_extractor(logs)

    def extract_delivery_logs_from_logs(self, logs):
        delivery_extractor = self.delivery_extractor_factory()
        return delivery_extractor(logs, report_mode=True)

    def big_tanks_delivery_extractor(self, logs, report_mode=False):
        '''
        For big tanks, we use the volume gradient to discern a delivery 
        '''
        return BigTanksLogsWindowDeliveryAlgorithm(logs).calculate_delivery(report_mode)

    def normal_tanks_delivery_extractor(self, logs, report_mode=False):
        '''
        For normal tanks, we use the volume flags to discern a delivery
        '''
        return NormalTanksLogsWindowDeliveryAlgorithm(logs).calculate_delivery(report_mode)

    def get_delivery_report(self):
        logs = self.get_logs()
        deliveries = self.extract_delivery_logs_from_logs(logs)
        return deliveries


'''
********************************
ABSTRACT DELIVERY STRATEGY CLASS
********************************
'''


class DeliveryAlgorithm:
    def __init__(self, logs):
        self.logs = logs

    def calculate_delivery(self, report_mode):
        raise NotImplementedError('Subclass must implement this')


'''
**********************************
CONCRETE DELIVERY STRATEGY CLASSES
**********************************
'''


class NormalTanksSubsequentLogsDeliveryAlgorithm(DeliveryAlgorithm):
    def calculate_delivery(self, report_mode):
        total_delivery = 0
        delivery_flag = False
        volume_at_delivery_start = 0
        volume_at_delivery_end = 0
        num_of_logs = len(self.logs)
        delivery_start_time = ''
        delivery_end_time = ''
        deliveries = []

        for (index, log) in enumerate(self.logs):
            if index == 0:
                if log['flag'] == '3':  # delivery at start of log
                    delivery_flag = True
                    volume_at_delivery_start = log['Volume']
                    if report_mode:
                        delivery_start_time = log['log_time']

            elif(log['flag'] == '3' and not delivery_flag):
                # start of a delivery in logs
                volume_at_delivery_start = self.logs[index-1]['Volume']
                delivery_flag = True
                if report_mode:
                    delivery_start_time = self.logs[index-1]['log_time']

            elif((index == num_of_logs-1 or log['flag'] == '1' or log['flag'] == '2') and delivery_flag):
                # ongoing delivery ended or paused
                delivery_flag = False
                volume_at_delivery_end = log['Volume']
                delivery_end_time = log['log_time']
                delivery = float(volume_at_delivery_end) - \
                    float(volume_at_delivery_start)
                total_delivery += delivery
                if report_mode:

                    payload = {'Site_name': log['site_name'], 'Tank_name': log['tank_name'],
                               'start_pv': volume_at_delivery_start, 'stop_pv': volume_at_delivery_end,
                               'Delivery_start_time': delivery_start_time, 'Delivery_end_time': delivery_end_time,
                               'Unit': log['unit'], 'Product': log['product'], 'Delivery': delivery
                               }
                    deliveries.append(payload)

        if report_mode:
            return deliveries
        else:
            return total_delivery


class BigTanksSubsequentLogsDeliveryAlgorithm(DeliveryAlgorithm):
    def delivery_occured(self, curr_volume, prev_volume):
        threshold = 100
        if float(curr_volume) - float(prev_volume) >= threshold:
            return True
        else:
            return False

    def calculate_delivery(self, report_mode):
        total_delivery = 0
        delivery_flag = False
        volume_at_delivery_start = 0
        volume_at_delivery_end = 0
        num_of_logs = len(self.logs)
        delivery_start_time = ''
        delivery_end_time = ''
        deliveries = []

        for (index, log) in enumerate(self.logs):
            if index == 0:
                continue  # skip the first log

            elif(self.delivery_occured(log['Volume'], self.logs[index-1]['Volume']) and not delivery_flag):
                # start of a delivery in logs
                volume_at_delivery_start = self.logs[index-1]['Volume']
                delivery_flag = True
                if report_mode:
                    delivery_start_time = self.logs[index-1]['log_time']

            elif((index == num_of_logs-1 or not self.delivery_occured(log['Volume'], self.logs[index-1]['Volume'])) and delivery_flag):
                # ongoing delivery ended or paused
                delivery_flag = False
                volume_at_delivery_end = log['Volume']
                delivery_end_time = log['log_time']
                delivery = float(volume_at_delivery_end) - \
                    float(volume_at_delivery_start)
                total_delivery += delivery
                if report_mode:

                    payload = {'Site_name': log['site_name'], 'Tank_name': log['tank_name'],
                               'start_pv': volume_at_delivery_start, 'stop_pv': volume_at_delivery_end,
                               'Delivery_start_time': delivery_start_time, 'Delivery_end_time': delivery_end_time,
                               'Unit': log['unit'], 'Product': log['product'], 'Delivery': delivery
                               }
                    deliveries.append(payload)

        if report_mode:
            return deliveries
        else:
            return total_delivery


class NormalTanksLogsWindowDeliveryAlgorithm(DeliveryAlgorithm):
    def calculate_delivery(self, report_mode):
        log_window_size = 2  # 2 previous logs, 2 next logs

        log_size = len(self.logs)
        delivery_flag = False
        volume_at_delivery_start = 0
        volume_at_delivery_end = 0
        delivery_start_time = ''
        delivery_end_time = ''
        deliveries = []
        total_delivery = 0

        if log_size >= log_window_size:
            
            controller_type = self.logs[0]['controller_type']

            for index in range(log_size):

                # for each log, check if it is the start of a delivery
                '''
                set delivery flags for prev and next logs in window
                '''

                '''
                check for start of delievry
                '''
                if (self.logs[index]['flag'] == '3' and not delivery_flag):

                    # check if it is a real delivery i.e no delivery in prev 2 logs (no longer),
                    # and continous delivery in next 2 logs
                    '''
                    set delivery flags for prev and next logs in window
                    '''
                    prev_non_delivery_flag = True
                    next_delivery_flag = True
                    for i in range(1, log_window_size+1):
                        prev_index = index - i
                        next_index = index + i
                        if next_index >= log_size:
                            next_delivery_flag &= True
                        else:
                            #temporary fix for inconsistent log for HYD-2 where log is inconsistent
                            if controller_type == "HYD-2":
                                if self.logs[next_index]['flag'] in ["3"]:
                                    next_delivery_flag &= True
                                else:
                                    next_delivery_flag &= False
                            else:
                                
                                if self.logs[next_index]['flag'] in ["3"]:
                                    next_delivery_flag &= True
                                else:
                                    next_delivery_flag &= False




                    if next_delivery_flag:
                        delivery_flag = True
                        
                        volume_at_delivery_start = self.logs[index-1]['Volume']
                        if report_mode:
                            delivery_start_time = self.logs[index -
                                                            1]['log_time']
                        # print('delivery start time idx and time',
                        #       index-1, delivery_start_time)
                        continue

                # check if it is in the midst of a delivery to know when it ends
                elif (self.logs[index]['flag'] == '3' and delivery_flag):
                    # check if it is actual delivery end i.e delivery in any of prev 2 logs,
                    # and no delivery in next 2 logs
                    prev_delivery_flag = False
                    next_non_delivery_flag = True
                    for i in range(1, log_window_size+1):
                        prev_index = index - i
                        next_index = index + i
                        if prev_index < 0:
                            prev_delivery_flag |= True
                        else:
                            if self.logs[prev_index]['flag'] == '3':
                                prev_delivery_flag |= True
                            else:
                                prev_delivery_flag |= False

                        if next_index >= log_size:
                            next_non_delivery_flag &= True
                        else:
                            if self.logs[next_index]['flag'] in ['1', '2']:
                                next_non_delivery_flag &= True
                            else:
                                next_non_delivery_flag &= False

                    if prev_delivery_flag and next_non_delivery_flag:
                        delivery_flag = False
                        volume_at_delivery_end = self.logs[index]['Volume']
                        delivery = float(volume_at_delivery_end) - \
                            float(volume_at_delivery_start)
                        if delivery >=0:
                            total_delivery += delivery
                        if report_mode:
                            delivery_end_time = self.logs[index]['log_time']
                            payload = {
                                'Site_name': self.logs[index]['site_name'], 'Tank_name': self.logs[index]['tank_name'],
                                'start_pv': volume_at_delivery_start, 'stop_pv': volume_at_delivery_end,
                                'Delivery_start_time': delivery_start_time, 'Delivery_end_time': delivery_end_time,
                                'Unit': self.logs[index]['Unit'], 'Product': self.logs[index]['product'], 'Delivery': delivery
                            }
                            if delivery > 0 :
                                deliveries.append(payload)

        if report_mode:
            return deliveries
        else:
            return total_delivery


class BigTanksLogsWindowDeliveryAlgorithm(DeliveryAlgorithm):
    def delivery_occured(self, curr_volume, prev_volume):
        threshold = 100
        if float(curr_volume) - float(prev_volume) >= threshold:
            return True
        else:
            return False

    def calculate_delivery(self, report_mode):
        log_window_size = 3  # 3 previous logs, 3 next logs

        log_size = len(self.logs)

        delivery_flag = False
        volume_at_delivery_start = 0
        volume_at_delivery_end = 0
        delivery_start_time = ''
        delivery_end_time = ''
        deliveries = []
        total_delivery = 0

        if log_size >= log_window_size:
            for index in range(log_size):
                if index == 0:
                    continue
                # for each log, check if it is the start of a delivery
                if (self.delivery_occured(self.logs[index]['Volume'], self.logs[index-1]['Volume']) and not delivery_flag):
                    # check if it is a real delivery i.e no delivery in prev 2 logs,
                    # and continous delivery in next 2 logs
                    #prev_non_delivery_flag = True
                    next_delivery_flag = True
                    for i in range(1, log_window_size+1):
                        prev_index = index - i
                        next_index = index + i
                        # if prev_index < 1:
                        #     prev_non_delivery_flag &= True
                        # else:
                        #     if not self.delivery_occured(self.logs[prev_index]['Volume'], self.logs[prev_index - 1]['Volume']):
                        #          prev_non_delivery_flag &= True
                        #     else: prev_non_delivery_flag &= False

                        if next_index >= log_size-1:
                            next_delivery_flag &= True
                        else:
                            if self.delivery_occured(self.logs[next_index]['Volume'], self.logs[next_index - 1]['Volume']):
                                next_delivery_flag &= True
                            else:
                                next_delivery_flag &= False

                    if next_delivery_flag:
                        delivery_flag = True
                        volume_at_delivery_start = self.logs[index-1]['Volume']
                        delivery_start_time = self.logs[index-1]['log_time']

                # check if it is in the midst of a delivery to know when it ends
                elif (self.delivery_occured(self.logs[index]['Volume'], self.logs[index-1]['Volume']) and delivery_flag):
                    # check if it is actual delivery end i.e delivery in any of prev 2 logs,
                    # and no delivery in next 2 logs
                    prev_delivery_flag = False
                    next_non_delivery_flag = True
                    for i in range(1, log_window_size+1):
                        prev_index = index - i
                        next_index = index + i
                        if prev_index < 1:
                            prev_delivery_flag |= True
                        else:
                            if self.delivery_occured(self.logs[prev_index]['Volume'], self.logs[prev_index - 1]['Volume']):
                                prev_delivery_flag |= True
                            else:
                                prev_delivery_flag |= False

                        if next_index >= log_size - 1:
                            next_non_delivery_flag &= True
                        else:
                            if not self.delivery_occured(self.logs[next_index]['Volume'], self.logs[next_index - 1]['Volume']):
                                next_non_delivery_flag &= True
                            else:
                                next_non_delivery_flag &= False

                    if prev_delivery_flag and next_non_delivery_flag:
                        delivery_flag = False
                        volume_at_delivery_end = self.logs[index]['Volume']
                        delivery = float(volume_at_delivery_end) - \
                            float(volume_at_delivery_start)
                        total_delivery += delivery
                        if report_mode:
                            delivery_end_time = self.logs[index]['log_time']
                            payload = {
                                'Site_name': self.logs[index]['site_name'], 'Tank_name': self.logs[index]['tank_name'],
                                'start_pv': volume_at_delivery_start, 'stop_pv': volume_at_delivery_end,
                                'Delivery_start_time': delivery_start_time, 'Delivery_end_time': delivery_end_time,
                                'Unit': self.logs[index]['Unit'], 'Product': self.logs[index]['product'], 'Delivery': delivery
                            }
                            deliveries.append(payload)

        if report_mode:
            return deliveries
        else:
            return total_delivery
