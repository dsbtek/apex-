import redis
import pickle
import csv

from concurrent.futures import ThreadPoolExecutor
from typing import List
import datetime as dt

from backend import models

from .. import utils
from . import queries as q
from decouple import config
#test
'''
(local_id=d[0], read_at=d[1],
                                 pv=d[2], pv_flag=d[3], sv=d[4], device_address=d[5], multicont_polling_address=d[6],
                                 tank_index=d[7], temperature=d[8],
                                 controller_type=d[9]) 
'''


def filter_for_latest_logs(logs):
    #use a set to hold tank refs whose log have been seen
    seen_tanks = set()
    filtered_logs = []
    for log in logs:
        tank_ref = '{}-{}-{}-{}'.format(log[5],log[6],
        log[7], log[-1])

        if tank_ref in seen_tanks:
            continue
        else:
            seen_tanks.add(tank_ref)
        filtered_logs.append(log)
    return filtered_logs


def update_tank_records(logs):
    
    for log in logs:
        #get conversion strategy
        strategy = ConversionFactory().create_conversion_strategy(
            log['Unit'],
            log['Display Unit']
            )
        #convert using the strategy
        log = strategy().convert(log)
    return logs


def update_tankgroup_records(logs):
    #perform tank level conversion
    logs = update_tank_records(logs)
    for log in logs:
        log = TankgroupConversion().convert(log)
    return logs


def compute_pv(mac_address, tank_height, tank_index):
    # get tank_chart using tank_index
    try:
        tank_info= q.get_tank_info(mac_address, tank_index)[0]
        chart_path = tank_info['CalibrationChart']
        offset_height = tank_info['Offset']
        density = tank_info['Density'] if tank_info['Density'] != None else 1
        chart = []

        # get the tank_chart to chart memory
        with open(f'media/{chart_path}', mode='r', encoding='latin1') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for each_line in csv_reader:
                chart.append((each_line['Height(mm)'], each_line['Volume(ltrs)']))

    except Exception as e:
        return float(0.0), float(tank_height) + float(offset_height), e

    # compute tank volume from the tank_height(sv) using the tank calibration chart
    counter = 0
    for each in chart:
        if float(each[0]) == float(tank_height) + float(offset_height):
            pv = float(each[1])
            break
        if float(each[0]) >= float(tank_height):
            uH, uV, lH, lV, sv = float(chart[counter-1][0]), float(chart[counter-1][1]), float(each[0]), float(each[1]), float(tank_height) + float(offset_height)
            pv = (((abs(sv - uH) * abs(lV - uV)) / (abs(lH - uH))) + uV)
            break
        counter += 1

    try:
        return float(pv * density), float(sv), "Done"
    except Exception as e:
        return float(0.0), float(tank_height) + float(offset_height), e


class ConversionFactory:
    def create_conversion_strategy(self, unit, display):
        if unit != display:
            if unit == 'm3' and display == 'L':
                return MeterCubeToLitres
            if unit == 'L' and display == 'gal':
                return LitresToGallon

            if unit == 'T' and display == 'L':
                return TonnesToLitres
        else:
            return SameUnit


class ConversionStrategy:
    def convert(self, log):
        raise NotImplementedError('Needs to subclass this class')        

class TonnesToLitres(ConversionStrategy):
    #[*] waiting for an update from Site guys to know the right formular
    #to use in computing this
    def convert(self, log):
        log["Volume"] = "{0:.3f}".format(float(log["Volume"]))
        return log

class MeterCubeToLitres(ConversionStrategy):
    def convert(self, log):
        log["Volume"] = "{0:.3f}".format(float(log["Volume"])*1000)
        return log


class LitresToGallon(ConversionStrategy):
    def convert(self, log):
        log["Volume"] = "{0:.3f}".format(float(log["Volume"])/3.78541)
        log["Height"] = "{0:.3f}".format(float(log["Height"])/25.4)
        return log


class SameUnit(ConversionStrategy):
    def convert(self, log):
        log["Volume"] = "{0:.3f}".format(float(log["Volume"]))
        log["Height"] = "{0:.3f}".format(float(log["Height"]))
        return log


class TankgroupConversion(ConversionStrategy):
    def convert(self, log):
        volume = float(log["Volume"])
        capacity = log["Capacity"]

        log["Fill %"] = round((volume * 100 / capacity), 2)
        log["tankVolume"] = "{0:.3f}".format(float(log["Volume"]))
        log["tankHeight"] = "{0:.3f}".format(float(log["Height"]))
        if "temperature" in log:
            log["temperature"] = "{0:.3f}".format(float(log["temperature"]))
        if "water" in log:
            log["water"] = "{0:.3f}".format(float(log["water"]))
        return log


class SqlLogsPaginationCacheMixin:
    def paginate_and_cache(self, request, *args, **kwargs):
        '''
        Apply caching
        '''
        #check for key: requesturl+ids+start+end
        key = (request.get_full_path()+'_ids:{}'+'_tank_ids:{}'+'_start:{}'+'_end:{}').format(self.ids,self.tank_ids,self.start_date,self.end_date)
        redis_instance = redis.Redis(host=config('REDIS_HOST'), port=config('REDIS_PORT'), db=0)
        client_count = request.data.get('count', None)
        pickled_response = redis_instance.get(key)
        if pickled_response:
            try:
                response = pickle.loads(pickled_response)
                content = response['content']
                headers = response['headers']
            except:
                pass
            else:
                return utils.CustomResponse.Success(data=content, headers=headers)

        if hasattr(self, 'pagination_class') and self.pagination_class is not None:
            limit = self.pagination_class().default_limit
            offset = self.pagination_class().get_offset(request)
        else:
            limit = config('ATG_LOGS_QUERY_LIMIT', cast=int)
            offset = 0
        if self.ids:
            '''
            Use threading to get count, and data
            '''
            
            count_query_fn = kwargs.pop('count_query', None)
            data_query_fn = kwargs.pop('data_query', None)
            with ThreadPoolExecutor(max_workers=3) as executor:
                result = executor.submit(
                    data_query_fn,
                    self.ids,
                    self.tank_ids,
                    self.start_date,
                    self.end_date,
                    limit,
                    offset
                )
                if client_count is None:
                    result_count = executor.submit(
                    count_query_fn,
                    self.ids,
                    self.tank_ids,
                    self.start_date,
                    self.end_date,
                    limit,
                    offset
                    )
                else:
                    result_count = client_count
            try:
                result_count = result_count.result()
            except AttributeError:
                result_count = client_count

            result = result.result()
            #update records
            result = update_tank_records(result)
            if self.paginator:
                self.paginator.set_log_count(result_count)
            page = self.paginate_queryset(result)
            if page:
                data, headers = self.get_paginated_response(result)
            else:
                data = result
                headers = {}
            '''
            set response in cache
            '''
            cache_response_payload = {
                'content': data,
                'headers': headers
            }
            pickled_response = pickle.dumps(cache_response_payload)
            redis_instance.set(key, pickled_response, 5*60)
            return utils.CustomResponse.Success(data=data, headers=headers)


class RevampedSqlLogsPaginationCacheMixin:
    def paginate_and_cache(self, request, *args, **kwargs):
        '''
        Apply caching
        '''
        #check for key: requesturl+ids+start+end
        key = (request.get_full_path()+'_tank_ids:{}'+'_start:{}'+'_end:{}').format(self.tank_ids,self.start_date,self.end_date)
        redis_instance = redis.Redis(host=config('REDIS_HOST'), port=config('REDIS_PORT'), db=0)
        pickled_response = redis_instance.get(key)
        if pickled_response:
            try:
                response = pickle.loads(pickled_response)
                content = response['content']
                headers = response['headers']
            except:
                pass
            else:
                return utils.CustomResponse.Success(data=content, headers=headers)
        if hasattr(self, 'pagination_class') and self.pagination_class is not None:
            limit = self.pagination_class().default_limit
            offset = self.pagination_class().get_offset(request)
        else:
            
            #limit = 10000000
            limit = config('ATG_LOGS_QUERY_LIMIT', cast=int)
            offset = 0

        if self.tank_ids:
            '''
            Use threading to get data
            '''
            data_query_fn = kwargs.pop('data_query', None)
            with ThreadPoolExecutor(max_workers=2) as executor:
                
                result = executor.submit(
                    data_query_fn,
                    self.tank_ids,
                    self.start_date,
                    self.end_date,
                    limit,
                    offset
                )
            result = result.result()

            #update records
            result = update_tank_records(result)     
            data = result
            headers = {}
            '''
            set response in cache
            '''
            cache_response_payload = {
                'content': data,
                'headers': headers
            }
            pickled_response = pickle.dumps(cache_response_payload)
            redis_instance.set(key, pickled_response, 5*60)
            return utils.CustomResponse.Success(data=data, headers=headers)



def getSitesAndTanks(site_ids):
    result = q.get_tanks_in_site(site_ids)
    site_device_address = q.get_site_device_address(site_ids)
    for each_site in result:
        r = redis.Redis(host=config('REDIS_HOST'), port=config('REDIS_PORT'), db=0)
        try:
            last_read = r.get(str(site_device_address[each_site['site_name']])).decode('utf-8')
            time_diff = (dt.datetime.now() - dt.datetime.strptime(last_read, "%Y-%m-%d %H:%M:%S")).total_seconds()
            
            # status if last_read < 24 hours
            if float(time_diff) < 86400.0:
                each_site['status'] = True
            else:
                each_site['status'] = False
        except Exception as e:
            each_site['status'] = False
    return result

