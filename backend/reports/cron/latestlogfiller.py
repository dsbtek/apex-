#!/usr/bin/python3
import mysql.connector
from mysql.connector import MySQLConnection, Error
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed
import datetime
import smtplib 

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from decouple import config
'''
This job checks for all tanks on smarteye, get their last/latested log and
saves it to another table called backend_latestatglog/LatestAtgLog model

'''

def dictfetchall(cursor):
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def connect_to_database():
    """
        connect to smarteye database: return connection
    """
    conection = mysql.connector.connect(
        host = config("DB_HOST"), 
        user = config("DB_USER"), 
        password = config("DB_PASSWORD"), 
        database = config("DB_NAME")
    )

    return conection


def get_sites(connection):
    """
        return list of all sites on smarteye in dict format
    """
    query = """
            SELECT s.`Site_id` as site_id, s.`Name` as site_name, s.`State` as state, s.`City` as city, s.`Address` as address, s.`Contact_person_name` as contact_name, s.`Critical_level_mail` as email, s.`Contact_person_phone` as mobile, d.`Device_unique_address` as mac_address
            FROM `backend_sites` s
            JOIN `backend_devices` d
            ON d.`Device_id` = s.`Device_id`
        """

    db_cursor = connection.cursor()
    db_cursor.execute(query)
    return dictfetchall(db_cursor)


def get_all_tanks(connection):
    """
        return the list of all tanks on smarteye in dict format
    """
    query = """
            SELECT t.`Tank_id` as tank_id, t.`Name` as tank_name, t.`Tank_index` as tank_index, t.`Site_id` as site_id, t.`Anomaly_period`, t.`Anomaly_volume`, t.`UOM`, t.`Controller_polling_address` as "controller_address", t.`Tank_controller`,t.`Capacity`,t.`Display_unit`, p.`name` as "product_name",`HH_Level`,`LL_Level`,`Reorder`
            FROM `backend_tanks` t
            JOIN `backend_products` p
            ON t.`product_id` = p.`product_id`;          
             """

    db_cursor = connection.cursor()
    db_cursor.execute(query)
    return dictfetchall(db_cursor)


def get_tanks_in_site(site, tanks):
    """
        add all the tanks in a site to the site dict
    """

    site['tanks'] = [tank for tank in tanks if tank['site_id'] == site['site_id']]

def compute_tank_latest_log(site, tank):
    try:
        conn = MySQLConnection(user=config("DB_USER"), password= config("DB_PASSWORD"),
                                 host= config("DB_HOST"),
                                 database= config("DB_NAME"))
        if conn.is_connected():
            cursor = conn.cursor(buffered=True)

        
        query = """
                    SELECT
                                l.pv AS Volume,
                                l.sv AS Height,
                                    (CASE
                                        WHEN l.temperature IS NULL THEN '0.00'
                                        ELSE l.temperature
                                    END) AS temperature,
                                    (CASE
                                        WHEN l.water IS NULL THEN '0.00'
                                        ELSE l.water
                                    END) AS water,
                                    l.read_at AS last_updated_time
                                        
                                FROM
                                    atg_primary_log l
                                WHERE
                                    l.Controller_type = "{}"
                                        AND l.tank_index = {}
                                        AND l.multicont_polling_address = {}
                                        AND l.flag_log = 1
                                        AND l.device_address= "{}"
                                ORDER BY l.read_at DESC
                                LIMIT 1; 
                    """.format(tank['Tank_controller'], tank['tank_index'],tank['controller_address'],site['mac_address'])
        cursor.execute(query)
        data = dictfetchall(cursor)
        if len(data) == 1:
            latest_log_insert_query  = "INSERT INTO backend_latestatglog (`Tank_id`,`Tank_name`,`Volume`,`Height`,`temperature`,`water`,`last_updated_time`,`Site_id`,`siteName`,`Capacity`,`Unit`,`DisplayUnit`,`Product`,`Fill`,`db_updated_time`,`Tank_controller`,`HH_Level`,`LL_Level`,`Reorder`,`Tank_Status`) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            cursor = conn.cursor()
            cursor.execute(latest_log_insert_query, (tank['tank_id'],tank['tank_name'],"{0:.3f}".format(float(data[0]["Volume"])),"{0:.3f}".format(float(data[0]["Height"])),"{0:.3f}".format(float(data[0]["temperature"])),data[0]['water'],data[0]['last_updated_time'],site['site_id'],site['site_name'],tank['Capacity'],tank['UOM'],tank['Display_unit'],tank['product_name'],round((float(data[0]["Volume"])* 100 / tank['Capacity']), 2),None,tank['Tank_controller'],tank['HH_Level'],tank['LL_Level'],tank['Reorder'],1))
            print("log found")
        elif len(data) == 0:
            print('log not found but')
            lastest_log_insert_query_2 = "INSERT INTO backend_latestatglog (`Tank_id`,`Tank_name`,`Site_id`,`siteName`,`Capacity`,`Unit`,`DisplayUnit`,`Product`,`Tank_controller`,`HH_Level`,`LL_Level`,`Reorder`,`db_updated_time`,`Tank_Status`) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            cursor = conn.cursor()
            cursor.execute(lastest_log_insert_query_2, (tank['tank_id'],tank['tank_name'],site['site_id'],site['site_name'],tank['Capacity'],tank['UOM'],tank['Display_unit'],tank['product_name'],tank['Tank_controller'],tank['HH_Level'],tank['LL_Level'],tank['Reorder'],None,1))
            

        conn.commit()
        cursor.close()
        conn.close()

    

    except Error as e:
        print('Error:', e)
    except Exception as e:
        print ('Exception:', e)
    

def process_tank_log(sites, connection):
    """
        asyncronously process tanks in each site to fill up the latest_log_table
    """
    tanks = get_all_tanks(connection)
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        [executor.submit(get_tanks_in_site, site, tanks) for site in sites]


    for site in sites:
        site_device_mac_address = site['mac_address']
        with concurrent.futures.ThreadPoolExecutor() as executor:
           [executor.submit(compute_tank_latest_log,site, tank) for tank in site['tanks']] 


def main():
    connection = connect_to_database()
    sites = get_sites(connection)
    process_tank_log(sites, connection)
 


if __name__ == '__main__':
    main()