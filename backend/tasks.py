from django.core.mail import EmailMessage
from io import StringIO
import csv
import json
import datetime
from typing import List
# changes
from django.db import connection
from django.core.mail import send_mail, EmailMessage
from django.template import loader

from celery import shared_task
from celery.utils.log import get_task_logger
from celery.task.schedules import crontab
from celery.decorators import periodic_task
from backend.smart_pump.utils import getSummaryReport
from backend import models
from . import celery_utils as cu
from . import smart_pump_celery_utils as smart_utils
from . import utils
from backend.smarteye_logs.utils import update_tankgroup_records
from django.db.models import Q
logger = get_task_logger(__name__)

'''
**************************************************************************
SMARTEYE TANK CELERY TASKS
***************************************************************************
'''


@shared_task(name='send_tank_alarms_email')
def tank_alarm_task(logs):
    #MTC&TLS has 13 items while Sensor(i.e. HYD-2) has 10 items
    #So their controller type index is different. -2 for tls&mtc;  -1 for sensor
    if len(logs[0]) == 13:
        controller_type_locator = -2
  
    elif len(logs[0]) == 10:
        controller_type_locator = -1
    elif len(logs[0]) == 15:
        controller_type_locator = -4
    else:
        controller_type_locator = -1

    for log in logs:
        # Get tank model for the log instance 
        device_address = log[5]
        controller_type = log[controller_type_locator]
        controller_address = log[6]
        tank_index = log[7]
        volume = float(log[2])
        read_at = log[1]
        log_valid = 0.1 <= volume <= 1000000
        #AND 0 + l.pv BETWEEN 0.1 AND 1000000
        if log_valid:
            try:
                #[*]I may have to exclude controller type while tracking a tank; site/device address,index,polling adrress shud be enough
                tank_reference = models.Tanks.objects.get(Site__Device__Device_unique_address=device_address,
                                                    Tank_controller=controller_type, Tank_index=tank_index, Controller_polling_address=controller_address)
                #get contollers that capture water and temperature
                if tank_reference.Tank_controller in ['TLS']:
                    water_level = log[9]
                    temperature_level = log[10]
                else:
                    water_level = 0
                    temperature_level = 0
                tank_content_conversion = update_tankgroup_records([{"Unit":tank_reference.UOM,"Display Unit":tank_reference.Display_unit,"Volume":volume,"Height":log[4],"Capacity":tank_reference.Capacity, "water":water_level, "temperature":temperature_level}]) 
                #device sends back date log sometimes, so there is need to compare date before updating obj
                x = models.LatestAtgLog.objects.filter(Q(last_updated_time__isnull = True)|Q(last_updated_time__lte = read_at), Tank_id = tank_reference.Tank_id )
                if x:
                    x.update(last_updated_time=read_at,Volume=tank_content_conversion[0]['Volume'],
                    temperature=tank_content_conversion[0]['temperature'],water=tank_content_conversion[0]['water'],
                    Height=tank_content_conversion[0]['Height'],Fill=tank_content_conversion[0]['Fill %']
                    )

                # obj, created = models.LatestAtgLog.objects.update_or_create(last_updated_time__lte = read_at,last_updated_time__isnull = True,Tank_id=tank_reference.Tank_id,
                #         defaults={'last_updated_time': read_at, 'Volume': tank_content_conversion[0]['Volume'],
                #         'temperature':tank_content_conversion[0]['temperature'],'water':tank_content_conversion[0]['water'],'Capacity':tank_reference.Capacity,'Unit':tank_reference.UOM,'DisplayUnit':tank_reference.Display_unit,
                #         'Product':tank_reference.Product.Name,'Height':tank_content_conversion[0]['Height'],'Fill':tank_content_conversion[0]['Fill %'],'Tank_name':tank_reference.Name,'siteName':tank_reference.Site.Name,
                #         "Tank_controller":tank_reference.Tank_controller,"Reorder":tank_reference.Reorder,"LL_Level":tank_reference.LL_Level,"HH_Level":tank_reference.HH_Level
                #         }
                #     )   
            except Exception as e:

                # if no tank mapping for a log instance, go to next log instance
                continue

            # Only send mail for recent log and time difference from now is with 30m
            current_timestamp = datetime.datetime.now()
            min_dif =  (current_timestamp-datetime.datetime.strptime(read_at, "%Y-%m-%d %H:%M:%S")).total_seconds()/60
            if (abs(min_dif) > 30):
                continue
            # Determine if site which tank belongs to is allowed to send email notifications
            if not tank_reference.Site.Email_Notification or volume < 0.0:
                continue

            # Use factory to get an Alarm notifier class based on the current volume.
            notifier = cu.AlarmFactory(
                tank_reference, volume, read_at, logger).create_alarm_notifier()
            # trigger notifier notify method
            if notifier is not None:
                notifier.notify()


def dictfetchall(cursor):
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


# @periodic_task(
#     run_every=(crontab(minute=0, hour='*/8')),
#     name=("log_alerts"),
#     ignore_result=True
# )
def log_alerts():
    with connection.cursor() as c:
        query = """
				SELECT
					d.Name AS 'Device_serial_number',
					d.Device_unique_address AS 'Device_MAC_Address',
					la.*
				FROM
				(SELECT 
				    d.Site, MAX(l.db_fill_time) AS 'Last_log_time'
				FROM
				    atg_integration_db.backend_devices d
				        JOIN
				    atg_primary_log l ON d.Device_unique_address = l.device_address
				GROUP BY d.Site) la
				JOIN backend_devices d ON la.Site = d.Site;
		"""
        c.execute(query)
        data = dictfetchall(c)

    downtime_sites = []

    mail_recipients = [
        'ridwan.yusuf@smartflowtech.com'
        #'rahman.s@e360africa.com',
        # 'jamiu.adeyemi@smartflowtech.com',
        # 'abimbola.ayodele@smartflowtech.com',
        # 'ayobami.adeyemo@smartflowtech.com',
        # 'moshood.adeleye@smartflowtech.com',
        # 'adewale.adejumo@smartflowtech.com'
    ]
    current_time = datetime.datetime.now()
    for log in data:
        site = log["Site"]
        last_log_time = log["Last_log_time"]
        # last_log_time = datetime.datetime.strptime(last_log_time, '%Y-%m-%d %H:%M:%S') #python datetime
        context = {
            'site': site,
            'time': last_log_time.strftime("%Y-%m-%d %H:%M:%S")
        }

        time_bool = (current_time -
                     last_log_time) >= datetime.timedelta(hours=12)

        if time_bool:
            downtime_sites.append(context)

            # send mail
    email_template_name = 'alerts/log_downtime_alert.html'
    email = loader.render_to_string(
        email_template_name, {'down_sites': downtime_sites})
    test = send_mail(
        subject='SMARTEYE downtime notification',
        message=email,
        from_email='support@e360.com',
        recipient_list=mail_recipients
    )

    if test > 0:  # mail sent successfully
        logger.info('Downtime notification sent for {}'.format(site))
    else:
        logger.info(
            'Unable to send downtime notification sent for {}'.format(site))

@shared_task(name='analog_probe_data_logger')
def analog_probe_logger(data):
    if type(data)== dict:
        data = [i for i in list(data.values())]
        final_tuple = []
        local_id = data[0]
        tank_index = data[2]
        controller_id = data[1]
        mac_address = data[4]
        control_mode = data[5]
        current = data[3]
        read_time = data[6]

        tank = models.Tanks.objects.get(
            Tank_id=local_id, Tank_index=tank_index, Controller_polling_address=controller_id, Control_mode=control_mode)

        '''
            - Conversions:  current -> Height; and  Height -> Volume
            - Get tank flag
            - Send to alarm task asynchronously
            - Save into DB
        '''

        if tank.Density != None:
            density = float(tank.Density)
        else:
            density = 1.0

        height = None
        flag = None
        volume = None
        tank_controller = tank.Tank_controller
        height = cu.convert_current_to_height(tank, current) * density
        if height:
                flag, volume = cu.convert_height_to_volume(tank, height)
        else:
            pass
        # New: Save current(mA) in dB
        # (local_id, read_at, pv, pv_flag, sv, device_address, multicon_polling_address,
        # tank_index, tc_volume, water, temperature, controller_type)
        final_tuple.append((local_id, read_time, str(volume), flag, height,
                            mac_address, controller_id, tank_index, current, tank_controller))

    # asynchronously send to alarm task
        from .smarteye_logs.utils import filter_for_latest_logs
        filtered_logs = filter_for_latest_logs(final_tuple)
        tank_alarm_task.delay(filtered_logs)

        # insert to DB
        logs = [models.AtgPrimaryLog(local_id=d[0], read_at=d[1],
                                    pv=d[2], pv_flag=d[3], sv=d[4], device_address=d[5], multicont_polling_address=d[6],
                                    tank_index=d[7], temperature=d[8],
                                    controller_type=d[9]) for d in final_tuple]

        models.AtgPrimaryLog.objects.bulk_create(logs)
        logger.info("Inserted sensor logs into DB")


'''
**************************************************************************
SMARTEYE GEN CELERY TASKS
***************************************************************************
'''


'''
**************************************************************************
SMART PUMP REPORT CELERY TASKS
***************************************************************************
'''


@shared_task
def send_sales_summary_report(*args):
    email_receiver, mail_receiver_name, dateRange, Site_id, passed_products = args
    generated_summary_report = getSummaryReport(
        Site_id, passed_products, dateRange)
    all_date_summary_data = generated_summary_report.get('SummaryReport')

    summary_headers = all_date_summary_data[0].keys()
    # replace none value with 0.00
    formated_date_summary_data = utils.replace_none_with_zero(
        all_date_summary_data)
    csvfile = StringIO()
    writer = csv.DictWriter(csvfile, fieldnames=summary_headers)
    sales_totalizer = utils.generateSalesSummaryProductTotalizer(
        formated_date_summary_data)
    writer.writeheader()
    writer.writerows(formated_date_summary_data + sales_totalizer)
    # insert blank row
    # writer.writerows([{'date': ''}])

    site_name = models.Sites.objects.get(Site_id=Site_id)
    email_template_name = 'sales_report_email_template.html'
    template_context = {
        "full_username": mail_receiver_name,
        "site_name": f'{site_name}',
        "start_date": dateRange[0],
        "end_date": dateRange[-1],
        "current_time": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    emailmsg = loader.render_to_string(email_template_name, template_context)
    # update this mail to email_receiver i.e f'{email_receiver}' test email is working
    email = EmailMessage('Sales Report', emailmsg,
                         'noreply@smartflowtech.com', [f'{email_receiver}'],)
    email.content_subtype = "html"  # Main content is now text/html
    email.attach('sales-report.csv', csvfile.getvalue(), 'text/csv')
    email.send()


'''
**************************************************************************
SMART PUMP PRICE CHANGE CELERY TASKS
***************************************************************************
'''


@shared_task(name='send_price_change_notification_alarm')
def send_price_change_notification_task(price_change_request, designation, is_initial_price):
    # Use factory to get a Price Alarm notifier class based on the Approval Status,designation(site/company) and if 1st price
    notifier = smart_utils.PriceAlarmFactory(
        price_change_request, designation, is_initial_price).create_alarm_notifier()
    # trigger notifier notify method
    if notifier is not None:
        notifier.notify()
