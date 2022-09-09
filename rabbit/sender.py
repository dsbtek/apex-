import time
import datetime
import pika
import json
import redis
# from ..atg_web.settings.base import *


# redis = redis.Redis(
#     host='smeye.lbzjml.ng.0001.use2.cache.amazonaws.com', port=6379, db=0)
# redis = redis.Redis(host='localhost', port=6379, db=0)


def send_heartbeat_msg():
    try:
        mq_url = 'http://smarteye_prod_heartbeat_user:vt6Su59PBe8^@cupid.smartflowtech.com:15672/vhost'
        connection = pika.BlockingConnection(pika.URLParameters(mq_url))
        channel = connection.channel()
        MAC = "b8:27:eb:c6:38:97"
        channel.exchange_declare(
            exchange='heartbeat_logs', virtual_host="/",exchange_type='topic', durable=True)
        routing_key = 'heartbeat.' + MAC
        last_time_online = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message = json.dumps(
            {'last_time_online': last_time_online, 'local_ip': MAC, 'device_mac_address': MAC})
        channel.basic_publish(
            exchange='heartbeat_logs',
            routing_key=routing_key,
            body=message
        )
        print("[*] Sent %r:%r" % (routing_key, message))
        # redis.set(MAC, last_time_online)
        #print('redis get', redis.get(MAC))
        connection.close()
        print("Heartbeat sent to db")

    except Exception as e:
        print('Heartbeat message is not sent', e)


send_heartbeat_msg()
