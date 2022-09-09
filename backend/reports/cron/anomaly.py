#!/usr/bin/python3
import mysql.connector
import concurrent.futures

import datetime
import smtplib 

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from decouple import config


def coma_number(value):
    splited = str(value).split(".")
    decimal = splited[1]
    list_value = splited[0][::-1]
    result = []
    for each in list_value:
        if len(result)%4 == 0:
            result.append(",")
        result.append(each)
    return ''.join([str(elem) for elem in result])[::-1][:-1] + "." + str(decimal)


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
        return list of all sites on smarteye with email notification enabled in dict format
    """
    query = """
            SELECT s.`Site_id` as site_id, s.`Name` as site_name, s.`State` as state, s.`City` as city, s.`Address` as address, s.`Contact_person_name` as contact_name, s.`Critical_level_mail` as email, s.`Contact_person_phone` as mobile, d.`Device_unique_address` as mac_address
            FROM `backend_sites` s
            JOIN `backend_devices` d
            ON d.`Device_id` = s.`Device_id`
            WHERE `Email_Notification` = 1;
        """

    db_cursor = connection.cursor()
    db_cursor.execute(query)
    return dictfetchall(db_cursor)


def get_all_tanks(connection):
    """
        return the list of all tanks on smarteye in dict format
    """
    query = """
            SELECT Tank_id as tank_id, Name as tank_name, Tank_index as tank_index, Site_id as site_id, `Anomaly_period`, `Anomaly_volume`, `UOM`, Controller_polling_address as "controller_address"
            FROM `backend_tanks`;
        """

    db_cursor = connection.cursor()
    db_cursor.execute(query)
    return dictfetchall(db_cursor)


def get_site_logs(site, connection):
    """
        return all atg_primary_logs of the current day for a single site 
    """
    now = datetime.datetime.now()
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
    """
        send anomaly email alert to client
    """
    site_name = anomaly_list[0]['site']['site_name']
    site_address = anomaly_list[0]['site']['address'] + ", " + anomaly_list[0]['site']['city'] + ". " + anomaly_list[0]['site']['state'] + "."
    contact_email = anomaly_list[0]['site']['email']
    sender_email = "smartflowssbu@smartflowtech.com"
    contact_name = anomaly_list[0]['site']['contact_name']
    anomaly_per_tank = [(site_name, each_anomaly['tank']['tank_name'], each_anomaly['anomaly_log']) for each_anomaly in anomaly_list]

    # temp: for test send all mail to my email addresse
    contact_email = "ridwan.yusuf@smartflowtech.com"

    # write the HTML part
    each_list = ""
    for logs in  anomaly_per_tank:
        init_volume = round(float(logs[2][0]['volume']), 2)
        final_volume = round(float(logs[2][1]['volume']), 2)
        volume_drop = round(float(init_volume - final_volume), 2)

        init_volume = coma_number(init_volume)
        final_volume = coma_number(final_volume)
        volume_drop = coma_number(volume_drop)

        sub_html = """\
                <tr style="border: 1px solid #ddd; padding: 8px;">
                    <td style="border: 1px solid #ddd; padding: 8px;">{0}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{1}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{2}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{3}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{4}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{5}</td>
                </tr>
            """.format(logs[1], init_volume, logs[2][0]['read_at'], final_volume, logs[2][1]['read_at'], "volume drop by {}".format(volume_drop))
        each_list += sub_html


    footer = """\
                    <tr></tr>
                </tbody>
            </table>
            <p> Feel free to contact <a href="mailto:support@smartflowtech.com"><strong>Smartflowtech Support</strong></a> for more information.</p>
        </body>
        </html>
    """

    html = """\
        <html>
            <body>
                <p>Hi, {0}.</p>
                <p>Smarteye detect the following anomaly in {1} at {2}</p>
                <table style="border-collapse: collapse; width: 100%; font-family: Arial, Helvetica, sans-serif;">
                    <thead>
                        <tr>
                            <th style="padding-top: 12px; padding-bottom: 12px; text-align: left; background-color: red; color: white; border: 1px solid #ddd; padding: 8px;">Tank Name</th>
                            <th style="padding-top: 12px; padding-bottom: 12px; text-align: left; background-color: red; color: white; border: 1px solid #ddd; padding: 8px;">Start Volume ({3})</th>
                            <th style="padding-top: 12px; padding-bottom: 12px; text-align: left; background-color: red; color: white; border: 1px solid #ddd; padding: 8px;"> Start Time</th>
                            <th style="padding-top: 12px; padding-bottom: 12px; text-align: left; background-color: red; color: white; border: 1px solid #ddd; padding: 8px;"> End Volume ({3})</th>
                            <th style="padding-top: 12px; padding-bottom: 12px; text-align: left; background-color: red; color: white; border: 1px solid #ddd; padding: 8px;"> End Time</th>
                            <th style="padding-top: 12px; padding-bottom: 12px; text-align: left; background-color: red; color: white; border: 1px solid #ddd; padding: 8px;">Reason ({3})</th>
                        </tr>
                    </thead>
                <tbody>
    """.format(contact_name, site_name, site_address, unit)

    html = html+each_list+footer

    alert = MIMEMultipart("alternative")
    alert['Subject'] = 'Anomaly Alert!!! in {}'.format(site_name)
    alert['From'] = config("EMAIL_HOST_USER")
    alert['To'] = contact_email

    template = MIMEText(html, "html")
    alert.attach(template)

    # Send the message via SMTP server.
    try:
        server = smtplib.SMTP_SSL(config("EMAIL_HOST"),465)
        # server.ehlo()
        # server.starttls()
        # server.ehlo()
        server.login(config("EMAIL_HOST_USER"), config("EMAIL_HOST_PASSWORD"))
    except Exception as e:  
        print('err',e)
    server.sendmail(sender_email, 'ridwan.yusuf@smartflowtech.com', alert.as_string())
    server.quit()
    print("{0} | sent mail to {1} | SiteName: {2} ".format(datetime.datetime.now(), contact_email, site_name))


def compute_anomaly(site, tank, logs):
    """
        compute the anamaly algorithm using brute force algorithm
    """
    if tank['Anomaly_volume'] == None or tank['Anomaly_period'] == None:
        return None

    log_threshold = int(tank['Anomaly_period'])
    volume_threshold = int(tank['Anomaly_volume'])
    unit = tank['UOM']
    anomaly_list = []
    counter = 0
    tank_logs = [log for log in logs if log['tank_index'] == tank['tank_index'] and log['controller_address'] == tank['controller_address']]
    log_length = len(tank_logs)
    init_time = ""

    while counter <= log_length:
        try:
            init_time = tank_logs[counter]['read_at']
            next_time = datetime.datetime.strptime(init_time, "%Y-%m-%d %H:%M:%S") + datetime.timedelta(minutes=log_threshold)
            varry_log = [tank_logs[counter]]
            new_log = tank_logs[counter:]
            for each in range(len(new_log)):
                if next_time == datetime.datetime.strptime(new_log[each]['read_at'], "%Y-%m-%d %H:%M:%S"):
                    varry_log.append(new_log[each])
                    break
                if next_time < datetime.datetime.strptime(new_log[each]['read_at'], "%Y-%m-%d %H:%M:%S"):
                    varry_log.append(new_log[each-1])
                    break
            
            volume_diff = float(float(varry_log[0]['volume']) - float(varry_log[1]['volume']))
            

            if (volume_diff >= volume_threshold):
                anomaly_list.append({"site": site, "tank": tank, "anomaly_log": varry_log})
                counter += log_threshold
            else:
                counter += 1
        except IndexError:
            break
    if len(anomaly_list) > 0:
        send_mail(anomaly_list, unit)

    
def process_anomaly(sites, connection):
    """
        asyncronously process tanks in each site for anomaly checks
    """
    tanks = get_all_tanks(connection)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        [executor.submit(get_tanks_in_site, site, tanks) for site in sites]

    for site in sites:
        logs = get_site_logs(site, connection)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            [executor.submit(compute_anomaly, site, tank, logs) for tank in site['tanks']]


def main():
    connection = connect_to_database()
    sites = get_sites(connection)
    process_anomaly(sites, connection)


if __name__ == '__main__':
    main()