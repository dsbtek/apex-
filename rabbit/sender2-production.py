import time
import datetime
import pika
import json
import redis

# redis = redis.Redis(
#     host='prodsmarti.lbzjml.ng.0001.use2.cache.amazonaws.com', port=6379, db=0)

redis = redis.Redis(host='localhost', port=6379, db=0)


def send_heartbeat_msg():
    try:
        mq_url = "amqps://smarteyeproductionuser1:smarteyeproductionuser123@b-cf0720aa-72aa-4255-9906-930f501d7400.mq.us-east-2.amazonaws.com:5671"
        connection = pika.BlockingConnection(pika.URLParameters(mq_url))
        channel = connection.channel()
        MAC = "b2:dd:se:da:12"
        channel.exchange_declare(
            exchange='heartbeat_logs', exchange_type='topic', durable=True)
        routing_key = 'heartbeat.' + MAC
        last_time_online = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message = json.dumps(
            {'last_time_online': last_time_online, 'local_id': MAC})
        channel.basic_publish(
            exchange='heartbeat_logs',
            routing_key=routing_key,
            body=message
        )
        print("[*] Sent %r:%r" % (routing_key, message))
        redis.set(MAC, last_time_online)
        print('redis get', redis.get(MAC))
        connection.close()
        print("Heartbeat sent to db")

    except Exception as e:
        print('Heartbeat message is not sent', e)


send_heartbeat_msg()
