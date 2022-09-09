import pika
import sys
import json
from ..atg_web.settings.base import *


import redis
redis = redis.Redis(
    host=REDIS_HOST, port=REDIS_PORT, db=0)

connection = pika.BlockingConnection(pika.URLParameters(
    RABBIQ_MQ_URL))

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
    redis.set('b2:dd:se:da:12', 'my redis value')
    print('redis get', redis.get('b2:dd:se:da:12'))
    # print(redis.get(payload.get('device_mac_address')).decode("utf-8"))
    ch.basic_ack(delivery_tag=method.delivery_tag)


channel.basic_qos(prefetch_count=1)
channel.basic_consume(callback, queue='heartbeat_queue')

channel.start_consuming()
