import pika
import sys
import json
#sys.path.append('/var/www/PYTHON/rabbits/services')
#import mysql_service
import redis
redis = redis.Redis(host='localhost', port=6379, db=0)

#credentials = pika.PlainCredentials('prod_user', 'prod_password')
#parameters = pika.ConnectionParameters('172.31.34.169', 5672, '/', credentials)
connection = pika.BlockingConnection(pika.URLParameters("amqps://prod_user:prod_password@b-f44d9c58-da38-4253-86f8-60f12212dad8.mq.eu-west-1.amazonaws.com:5671"))

channel = connection.channel()

channel.exchange_declare(exchange='heartbeat_logs',
                         exchange_type='topic')

channel.queue_declare('heartbeat_queue', durable=True)
#queue_name = result.method.queue
binding_key = 'heartbeat.*'

channel.queue_bind(exchange='heartbeat_logs',
                       queue='heartbeat_queue',
                       routing_key=binding_key)

print(' [*] Waiting for logs. To exit press CTRL+C')

def callback(ch, method, properties, body):
    #print(" [x] " % (method.routing_key, body))
    print(" [x] Received %r" % json.loads(body))
    payload = json.loads(body)
    #store in mysql db
    #mysql_service.save_heartbeat_log(payload)
    #store in redis cache
    redis.set(payload.get('device_mac_address'), payload.get('last_time_online'))
    #print(redis.get(payload.get('device_mac_address')).decode("utf-8"))
    ch.basic_ack(delivery_tag = method.delivery_tag)

channel.basic_qos(prefetch_count=1)
channel.basic_consume(callback,queue='heartbeat_queue')

channel.start_consuming()