#!/usr/bin/python3

import concurrent.futures
#from mysql.connector import MySQLConnection, Error
import mysql.connector
import datetime
import smtplib

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from decouple import config

'''
This job detects missed log within preset  time(min) on a daily basis
for each active tank  on SmartEye

'''


def dictfetchall(cursor):
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def connect_to_database():
    """
        connect to smarteye database: return connection
    """
    conection = mysql.connector.connect(
        host=config("DB_HOST"),
        user=config("DB_USER"),
        password=config("DB_PASSWORD"),
        database=config("DB_NAME")
    )

    return conection


def get_sites(connection):
    """
        return list of all active sites on smarteye in dict format
    """
    query = """
            SELECT s.`Site_id` as site_id, s.`Name` as site_name,s.`Contact_person_name` as contact_name, s.`Critical_level_mail` as email, s.`Contact_person_phone` as mobile, d.`Device_unique_address` as mac_address , c.`Name` as Company_name, s.`Company_id`
            FROM `backend_sites` s
            JOIN `backend_devices` d
            ON d.`Device_id` = s.`Device_id`
            JOIN `backend_companies` c
            ON s.`Company_id` = c.`Company_id`
            WHERE s.`Active` = 1;
            """

    db_cursor = connection.cursor()
    db_cursor.execute(query)
    return dictfetchall(db_cursor)


def get_all_tanks(connection):
    """
        return the list of all active tanks on smarteye in dict format
    """
    query = """
            SELECT  bt.Tank_id as tank_id,  bt.Name as tank_name,  bt.Tank_index as tank_index,  bt.Site_id as site_id, `Anomaly_period`, `Anomaly_volume`, `UOM`, Controller_polling_address as "controller_address", bp.Name as Product_name
            FROM `backend_tanks` bt
            JOIN `backend_products` bp
            ON bt.`Product_id` = bp.`Product_id`
            WHERE `Status` = 1;
            """

    db_cursor = connection.cursor()
    db_cursor.execute(query)
    return dictfetchall(db_cursor)


def get_site_logs(site, connection, now):
    """
        return all atg_primary_logs of the current day for a single site 
    """
    start = datetime.datetime.strftime(now, "%Y-%m-%d") + " 00:00"
    stop = datetime.datetime.strftime(now, "%Y-%m-%d") + " 23:59"
    query = """
            SELECT `device_address` as macddress, `pv` as volume, `sv` as height, read_at, `water` as water_volume, tank_index, multicont_polling_address as "controller_address"
            FROM `atg_primary_log`
            WHERE `device_address` = "{}"
            AND read_at BETWEEN "{}" AND "{}"
            ORDER BY read_at ASC;
            """.format(site['mac_address'], start, stop)

    db_cursor = connection.cursor()
    db_cursor.execute(query)
    return dictfetchall(db_cursor)


def get_tanks_in_site(site, tanks):
    """
        add all the tanks in a site to the site dict
    """

    site['tanks'] = [tank for tank in tanks if tank['site_id'] == site['site_id']]


def send_mail(anomaly_list, unit):
    # optionally notify admin of the missed logs
    pass


def compute_missed_log(site, tank, logs, now):
    print('site:', site['site_name'], 'tank:', tank['tank_name'])
    """
        compute the missed logs
    """
    message = "No missing data"
    missed_anomaly_list = []
    log_threshold = 30  # in minutes
    counter = 1
    tank_logs = [log for log in logs if log['tank_index'] == tank['tank_index']
                 and log['controller_address'] == tank['controller_address']]

    log_length = len(tank_logs) 
    print('log lenght',log_length)    
    init_time = datetime.datetime.strftime(now, "%Y-%m-%d") + " 00:00:00"

    if log_length == 0:
        message = "Missing Data(Whole Day)"

    while counter <= log_length:
        try:
            if counter == 1:
                # start tracking logs from 12.am  else tracking start from the first log
                init_time = datetime.datetime.strftime(
                    now, "%Y-%m-%d") + " 00:00:00"
            else:
                init_time = tank_logs[counter]['read_at']

            next_time = datetime.datetime.strptime(
                init_time, "%Y-%m-%d %H:%M:%S") + datetime.timedelta(minutes=log_threshold)

            if counter == 1:
                next_log = tank_logs[counter]
            else:
                next_log = tank_logs[counter+1]
            # 00:30:00 00:00:40
            if next_time < datetime.datetime.strptime(next_log['read_at'], "%Y-%m-%d %H:%M:%S"):
                time_delta = (datetime.datetime.strptime(
                    next_log['read_at'], "%Y-%m-%d %H:%M:%S") - datetime.datetime.strptime(init_time, "%Y-%m-%d %H:%M:%S"))
                time_diff = time_delta.total_seconds()/60
                if (time_diff >= log_threshold):

                    missed_anomaly_list.append(
                        {"stat": init_time.format("%Y/%m/%d"), "end": next_log['read_at']})
                    message = "Missing Data"
                    counter += 1
                else:
                    counter += 1
            else:
                counter += 1
        except Exception as e:
            # when index is out of range check, compare the last log with the upper band of the dayi.e 12pm
            last_log_time = datetime.datetime.strptime(
                tank_logs[-1]['read_at'], "%Y-%m-%d %H:%M:%S")
            end_time_of_day = datetime.datetime.strftime(
                now, "%Y-%m-%d") + " 23:59:59"
            time_delta = (datetime.datetime.strptime(
                end_time_of_day, "%Y-%m-%d %H:%M:%S") - last_log_time)
            last_time_diff = time_delta.total_seconds()/60

            if (last_time_diff >= log_threshold):
                message = "Missing Data"
                missed_anomaly_list.append(
                    {"state": last_log_time, "ende": end_time_of_day})

            break

    missed_dates = ''.join(
        [each['stat'] + ' to ' + each['end'] + '\n' for each in missed_anomaly_list])

    query = """
            INSERT INTO backend_dailymissedlog (`Tank_id`,`Tank_name`,`Company_id`,`Company_name`,`Site_id`,`Site_name`,`Log_date`,`Status`,`Missed_interval`,`Db_fill_time`,`Product_name`) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """

    try:
        conn = mysql.connector.MySQLConnection(user=config("DB_USER"), password=config("DB_PASSWORD"),
                                               host=config("DB_HOST"),
                                               database=config("DB_NAME"))
        if conn.is_connected():
            cursor = conn.cursor(buffered=True)
        db_fill_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(query, (tank['tank_id'], tank['tank_name'], site['Company_id'], site['Company_name'], site['site_id'],
                       site['site_name'], datetime.datetime.strftime(now, "%Y-%m-%d"), message, missed_dates, db_fill_time, tank['Product_name']))
        conn.commit()
        cursor.close()
        conn.close()
    except mysql.connector.Error as e:
        print('Error:', e)
    except Exception as e:
        print('Exception:', e)


def process_missed_logs(sites, connection):
    """
        asyncronously process tanks in each site for missed logs
    """
    # there is need to pass now along for the fear of date conflict
    now = datetime.datetime.now() 
    #now = datetime.datetime(2019, 11, 6, 00, 00)
    tanks = get_all_tanks(connection)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        [executor.submit(get_tanks_in_site, site, tanks) for site in sites]

    for site in sites:
        logs = get_site_logs(site, connection, now)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            [executor.submit(compute_missed_log, site, tank, logs, now)
             for tank in site['tanks']]


def main():
    import time
    start = time.time()
    connection = connect_to_database()
    sites = get_sites(connection)
    process_missed_logs(sites, connection)
    print('Missed Log Execution took', time.time()-start, 'seconds.')


if __name__ == '__main__':
    main()
