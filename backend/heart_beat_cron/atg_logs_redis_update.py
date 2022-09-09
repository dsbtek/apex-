import sys
import json
import redis
from .log_time_update import update_log_time
from decouple import config

redis = redis.StrictRedis(host=config('REDIS_HOST'), port=config('REDIS_PORT'),
                          db=0, charset="utf-8", decode_responses=True)


def main():
   #This job updates the device_heartbeat last log time
   for key in redis.scan_iter("b8:*"):
      update_log_time(key)
