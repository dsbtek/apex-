import sys
from mysql.connector import MySQLConnection, Error
import re
import datetime
import redis
from decouple import config
redis = redis.Redis(host=config('REDIS_HOST'), port=config('REDIS_PORT'), db=0,
                    charset="utf-8", decode_responses=True)


def update_log_time(device_mac_address):
    print('mac addres', device_mac_address)
    try:
        conn = MySQLConnection(user=db_username, password=db_password,
                               host=db_host,
                               database=db_name)
        if conn.is_connected():
            cursor = conn.cursor(buffered=True)
            # query = """
            #         UPDATE
            #             `device_heartbeats` AS `destination`,
            #             (
            #                 SELECT
            #                     *
            #                 FROM
            #                     `atg_primary_log`
            #                 WHERE
            #                 device_address = %(str)s
            #                 ORDER BY read_at DESC LIMIT 1
            #             ) AS `source`
            #         SET
            #             `destination`.`last_log_time` = `source`.`read_at`
            #         WHERE
            #             `destination`.`device_mac_address` = %(str)s        
            #         """
            query = """ 
                     SELECT
                                *
                            FROM
                                `atg_primary_log`
                            WHERE
                            device_address = %(str)s
                            ORDER BY read_at DESC LIMIT 1
                    
                     """
            

            cursor.execute(query, {'str': 'b8:27:eb:76:dc:65'})
            print('mac', device_mac_address)
            print("updated")
            conn.commit()
            cursor.close()
            conn.close()

    except Error as e:
        print('Error:', e)
    except Exception as e:
        print('Exception:', e)


def main():
    update_log_time()


db_host = config('DB_HOST')
db_username = config('DB_USER')
db_password = config('DB_PASSWORD')
db_name = config('DB_NAME')

if __name__ == '__main__':
    main()
