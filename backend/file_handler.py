import os
import csv
import json
import redis
import traceback
from typing import Dict, List
from .utils import convert_csv_to_json

from django.conf import settings
from decouple import config


def chart_processor_full(filepath):
    data = []
    with open(filepath, newline='') as chart:
    	csv_reader = csv.DictReader(chart)
    	headings = csv_reader.fieldnames

    	for row in csv_reader:
    		data.append({headings[0]: row[headings[0]], headings[1]: row[headings[1]]})

    	return data

def redis_handler(key, value):
	try: 
		red = redis.Redis(host=config('REDIS_HOST'), port=config('REDIS_PORT'), db=0)
		red.set(key,value)
	except:
		traceback.print_exc()

def read_file_from_redis(key):
	try: 
		red = redis.Redis(host=config('REDIS_HOST'), port=config('REDIS_PORT'), db=0, charset="utf-8", decode_responses=True)
		_file = red.get(key)
		return json.loads(_file)
	except:
		traceback.print_exc()

def lookup_chart(value, chart):
	'''
	Use interpolation search(binary search for range)
	'''
	n = len(chart)
	left = 0
	right = n-1
	HEIGHT_HEADER = 'Height(mm)'
	VOLUME_HEADER = 'Volume(ltrs)'

	#edge cases
	if value >= int(chart[n-1][HEIGHT_HEADER]):
		return chart[n-1]

	if value <= int(chart[0][HEIGHT_HEADER]):
		return chart[0]


	#perform binary search to get volume
	while left < right:
		mid = (left+right)//2
		if value < int(chart[mid][HEIGHT_HEADER]):
			right = mid
		elif value > int(chart[mid][HEIGHT_HEADER]):
			left = mid + 1
		else:
			return chart[mid]

	if value < int(chart[mid][HEIGHT_HEADER]):
		return value, chart[mid-1], chart[mid]
	else:
		return value, chart[mid], chart[mid+1]

def height_to_volume_interpolation_formula(**kwargs):
	HEIGHT_HEADER = 'Height(mm)'
	VOLUME_HEADER = 'Volume(ltrs)'
	#using equation of a line
	height = kwargs.get('height', None)
	prev_dict = kwargs.get('prev_chart_entry', None)
	next_dict = kwargs.get('next_chart_entry', None)
	chart = kwargs.get('chart', None)

	if height and prev_dict and next_dict:
		y2 = int(next_dict[VOLUME_HEADER])
		y1 = int(prev_dict[VOLUME_HEADER])
		x2 = int(next_dict[HEIGHT_HEADER])
		x1 = int(prev_dict[HEIGHT_HEADER])

		delta_y = y2-y1
		delta_x = x2-x1

		gradient = delta_y/delta_x

		#y = m(x-x1)+y1

		volume = gradient*(float(height)-x1) + y1
		return volume
	
	if chart:
		volume = int(chart[VOLUME_HEADER])
		return volume


def current_to_height_interpolation_formula(**kwargs):
	HEIGHT_HEADER = 'Height(mm)'
	CURRENT_HEADER = 'Current(mA)'
	#using equation of a line
	current = kwargs.get('current', None)
	prev_dict = kwargs.get('prev_chart_entry', None)
	next_dict = kwargs.get('next_chart_entry', None)
	chart = kwargs.get('chart', None)

	if current and prev_dict and next_dict:
		#edge cases
		if float(current) <= float(prev_dict[CURRENT_HEADER]):
			current = prev_dict[CURRENT_HEADER]
		if float(current) >= float(next_dict[CURRENT_HEADER]):
			current = next_dict[CURRENT_HEADER]

		y2 = float(next_dict[CURRENT_HEADER])
		y1 = float(prev_dict[CURRENT_HEADER])
		x2 = next_dict[HEIGHT_HEADER]
		x1 = prev_dict[HEIGHT_HEADER]

		delta_y = int(y2) - int(y1)
		delta_x = int(x2) - int(x1)

		gradient = delta_y/delta_x

		#y = m(x-x1)+y1
		#y = mx + c (y = current, x = height)
		#x = y - c / m
		height = (float(current)-y1)/gradient
		return height
	
	if chart:
		height = float(chart[HEIGHT_HEADER])
		return height


def last_entered_pv(tankid, new_pv):
	name = 'last_entered_pv'
	pv_flag = 1
	try: 
		red = redis.Redis(host=config('REDIS_HOST'), port=config('REDIS_PORT'), db=0)
		if red.hexists(name, tankid):
			last_pv = float(red.hget(name, tankid))
			if (last_pv-5 <= new_pv <= last_pv+10):
				pv_flag = 1
			elif (new_pv < last_pv-5):
				pv_flag = 2
			else:
				pv_flag = 3
			red.hset(name, tankid, new_pv)
		else:
			red.hset(name, tankid, new_pv)
			pv_flag = 1
		return pv_flag
	except:
		traceback.print_exc()
		return None

def get_tank_calibration_chart(tank):
	tank_pk = tank.pk
	key = 'Tank'+str(tank_pk)
	chart = tank.CalibrationChart
	red = redis.Redis(host=config('REDIS_HOST'), port=config('REDIS_PORT'), db=0, charset="utf-8", decode_responses=True)
	if not red.hexists('tanks_calibration_chart', key):
		try:
			chart_path = os.path.join(settings.MEDIA_ROOT, chart.name)
			json_chart = convert_csv_to_json(chart_path)
		except:
			raise Exception('Calibration chart not found on server')
		else:
			red.hset('tanks_calibration_chart', key, json.dumps(json_chart))
	calibration_chart = json.loads(red.hget('tanks_calibration_chart', key))
	return calibration_chart

if __name__ == '__main__':
	# x = read_file_from_redis('Tank200')
	# chart_results = lookup_chart('21', x)
	# print(chart_results)
	# if isinstance(chart_results, tuple):
	# 	height, prev_dict, next_dict = chart_results
	# 	vol = interpolation_formula(height=height, prev_chart_entry=prev_dict, next_chart_entry=next_dict)
	# else:
	# 	chart = chart_results
	# 	vol = interpolation_formula(chart=chart)

	# print(vol)
	# print(sensor_voltage_height_converter('4.1234'))

	x = chart_processor('/backend/temp_files/calibration.csv')
	y = json.loads(x)
	z = lookup_chart('1546.87', y)

	if isinstance(z, tuple):
		height, prev_dict, next_dict = z
		vol = interpolation_formula(height=height, prev_chart_entry=prev_dict, next_chart_entry=next_dict)
	else:
		chart = z
		vol = interpolation_formula(chart=chart)
