import time
import datetime
import pika
import json
from ..atg_web.settings.base import *



def send_heartbeat_msg():
    try:
        # mq_url = "amqps://smarteye_staging_user:smarteye_staging_pass@b-d223dcc5-3d88-4ea9-aa44-2ba2659a9f5f.mq.us-east-2.amazonaws.com:5671"
        mq_url = RABBIQ_MQ_URL
        connection = pika.BlockingConnection(pika.URLParameters(mq_url))
        channel = connection.channel()
        MAC = "b2:dd:se:da:12"
        channel.exchange_declare(
            exchange='pumponline_logs', exchange_type='topic', durable=True)
        routing_key = 'pumpheartbeat.' + MAC
        last_time_online = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message = json.dumps(
            {'last_time_online': last_time_online, 'local_id': MAC})
        channel.basic_publish(
            exchange='pumponline_logs',
            routing_key=routing_key,
            body=message
        )
        print("[*] Sent %r:%r" % (routing_key, message))
        connection.close()
        print("Heartbeat sent to db")

    except Exception as e:
        print('Heartbeat message is not sent', e)


send_heartbeat_msg()
