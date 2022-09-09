import sys
import json
import redis
from .device_online import  save_device_online_heartbeat_log
from decouple import config

redis = redis.StrictRedis(host=config('REDIS_HOST'), port=config('REDIS_PORT'),
                          db=0, charset="utf-8", decode_responses=True)
def main():
   for key in redis.scan_iter("b8:*"):
      save_device_online_heartbeat_log(key)



