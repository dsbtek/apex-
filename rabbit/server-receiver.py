import pika
import sys
import json
import os
# sys.path.append('/var/www/PYTHON/rabbits/services')
#import mysql_service
import redis
# from ..atg_web.settings.base import *

redis = redis.Redis(
    #host='smeye.lbzjml.ng.0001.use2.cache.amazonaws.com', port=6379, db=0)
# connection = pika.BlockingConnection(pika.URLParameters(
    # "amqps://smarteye_staging_user:smarteye_staging_pass@b-d223dcc5-3d88-4ea9-aa44-2ba2659a9f5f.mq.us-east-2.amazonaws.com:5671"))
    host= 'prodsmarti.lbzjml.ng.0001.use2.cache.amazonaws.com')
connection = pika.BlockingConnection(pika.URLParameters(
    'http://smarteye_prod_heartbeat_user:vt6Su59PBe8^@cupid.smartflowtech.com/api/vhosts'))
channel = connection.channel()
channel.exchange_declare(exchange='heartbeat_logs',
                         exchange_type='topic', durable=True)
channel.queue_declare('heartbeat_queue', durable=True)
#queue_name = result.method.queue
binding_key = 'heartbeat.*'
channel.queue_bind(exchange='heartbeat_logs',
                   queue='heartbeat_queue',
                   routing_key=binding_key)
print(' [*] Waiting for logs. To exit press CTRL+C')


def callback(ch, method, properties, body):
    #print(" [x] " % (method.routing_key, body))
    print(" [x] msg Received %r" % json.loads(body))
    payload = json.loads(body)
    print('comimg from payload', payload.get('last_time_online'))
    # store in mysql db
    # mysql_service.save_heartbeat_log(payload)
    # store in redis cache
    try:
        redis.set(payload.get('device_mac_address'),
                  payload.get('last_time_online'))
    except Exception as e:
        print('Exception', e)
        pass

    # print(redis.get(payload.get('device_mac_address')).decode("utf-8"))
    ch.basic_ack(delivery_tag=method.delivery_tag)


channel.basic_qos(prefetch_count=1)
channel.basic_consume(callback, queue='heartbeat_queue')
channel.start_consuming()
