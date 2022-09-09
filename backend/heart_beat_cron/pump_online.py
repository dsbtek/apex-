import sys
from mysql.connector import MySQLConnection, Error
import re
import datetime
import redis
from decouple import config
redis = redis.Redis(host=config('REDIS_HOST'), port=config('REDIS_PORT'), db=0,
                    charset="utf-8", decode_responses=True)


def save_pumponline_heartbeat_log(device_mac_address):
    last_time_online = redis.get('pump_online_'+device_mac_address)
    print('pump_online_'+device_mac_address)

   
    print(last_time_online)
    try:
        conn = MySQLConnection(user=db_username, password=db_password,
                               host=db_host,
                               database=db_name)
        if conn.is_connected():
            cursor = conn.cursor(buffered=True)
            query = "SELECT COUNT(id) FROM pump_device_heartbeats WHERE device_mac_address = '" + \
                device_mac_address+"'"
            cursor.execute(query)
            #print(cursor.fetchone()[0])
            #print(len(cursor.fetchone()))
            if(cursor.fetchone()[0] == 0):
                query = "INSERT INTO pump_device_heartbeats (last_time_online,device_mac_address, source) VALUES(%s,%s,%s)"
                print("inserted")
                cursor = conn.cursor()
                cursor.execute(query, (last_time_online, device_mac_address, 'rabbitmq'))
            else:
                print('gets herexs')
                MAC = device_mac_address
                query = "UPDATE pump_device_heartbeats SET last_time_online = '" + \
                    last_time_online+"', source = 'rabbitmq', local_ip = '" + \
                    "' WHERE device_mac_address = '"+MAC + "'"

                cursor.execute(query)
                print("updated")

            conn.commit()
            cursor.close()
            conn.close()

    except Error as e:
        print('Error:', e)
    except Exception as e:
        print('Exception:', e)


def main():
    save_pumponline_heartbeat_log()


db_host = config('DB_HOST')
db_username = config('DB_USER')
db_password = config('DB_PASSWORD')
db_name = config('DB_NAME')

if __name__ == '__main__':
    main()
