import sys
import json
import redis
from .pump_online import save_pumponline_heartbeat_log
from decouple import config


redis = redis.StrictRedis(host=config('REDIS_HOST'), port=config('REDIS_PORT'),
                          db=0, charset="utf-8", decode_responses=True)

def main():
    # #This job updates the pump device_heartbeat time
    for key in redis.scan_iter("pump_online_*"):
        mac_address = key.replace('pump_online_', '')
        print('mac', mac_address)
        save_pumponline_heartbeat_log(mac_address)
