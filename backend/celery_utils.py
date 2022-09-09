import datetime
import os
import json
import redis
from typing import Optional, Tuple

from django.conf import settings
from django.core.mail import send_mail
from django.template import loader

from backend import models
from . import file_handler as fh

class AlarmNotifier:
    alarm_type = ''
    email_template_name = ''
    email_subject = ''
    mail_list = ''
    delay = 96 #4 days value hrs 

    def __init__(self, tank, volume, log_time, logger):
        self.tank = tank
        self.volume = volume
        self.logger = logger
        self.context = {
            'tank_name': self.tank.Name,
            'site': self.tank.Site.Name,
            'product': self.tank.Product.Name,
            'volume': '{0:.2f}'.format(self.volume),
            'low_alarm': self.tank.LL_Level,
            'high_alarm': self.tank.HH_Level,
            'reorder': self.tank.Reorder,
            'log_time': log_time,
            'capacity':self.tank.Capacity
        }

    def extract_mail_list(self):
        raise NotImplementedError('Subclass must override this')

    # get last time mail was sent
    def get_last_mail_timestamp(self):
        try:
            alarm_object = models.TankAlarmDispatcher.objects.get(
                tank_id=self.tank.Tank_id, alarm_type=self.alarm_type)
            last_mail_timestamp = alarm_object.last_time_mail_sent
        except models.TankAlarmDispatcher.DoesNotExist:
            last_mail_timestamp = None
        finally:
            return last_mail_timestamp

    # send alarm notification
    def send_alarm_notification(self):
        email = loader.render_to_string(self.email_template_name, self.context)
        mail_recipients = self.extract_mail_list()
        if len(mail_recipients) > 0:
            mail = send_mail(subject=self.email_subject,
                    message=email,
                    from_email='support@smartflowtech.com',
                    #recipient_list=mail_recipients,
                    recipient_list=['ridwan.yusuf@smartflowtech.com','jamiu.adeyemi@smartflowtech.com','idowu.sekoni@smartflowtech.com'], #test mail
                    fail_silently=True
                    )
            if mail > 0:
                self.logger.info("Mail has been sent for tank {}".format(self.tank.pk))
                return True

    def update_mail_timestamp(self, new_timestamp):
        # update_or_create
        models.TankAlarmDispatcher.objects.update_or_create(tank_id=self.tank.Tank_id,
        alarm_type=self.alarm_type, defaults={'last_time_mail_sent': new_timestamp, 'volume': self.volume})
        
    def notify(self):
        # get last mail sent timestamp
        last_mail_timestamp = self.get_last_mail_timestamp()
        # send alarm only if timestamp is None or it has exceeded the preset delay
        current_timestamp = datetime.datetime.now()
        if not last_mail_timestamp or (current_timestamp - last_mail_timestamp > datetime.timedelta(hours=self.delay)):
            success_status = self.send_alarm_notification()
            # update timestamp mail was sent
            if success_status:
                self.update_mail_timestamp(current_timestamp)


class CriticalLowNotifier(AlarmNotifier):
    alarm_type = 'LL'
    email_template_name = 'alarm_notifications/critical_low_level.html'
    email_subject ='Tank Critical low level notification'
    
    def extract_mail_list(self):
        try:
            parsed_mail_list = list(map(lambda mail: mail.strip(), self.tank.Site.Critical_level_mail.split(','))) #strip white spaces away
        except AttributeError:
            parsed_mail_list = []
        finally:
            return parsed_mail_list


class CriticalHighNotifier(AlarmNotifier):
    alarm_type = 'HH'
    email_template_name = 'alarm_notifications/critical_high_level.html'
    email_subject ='Tank Critical High level notification'
    
    def extract_mail_list(self):
        try:
            parsed_mail_list = list(map(lambda mail: mail.strip(), self.tank.Site.Critical_level_mail.split(','))) #strip white spaces away
        except AttributeError:
            parsed_mail_list = []
        finally:
            return parsed_mail_list

class AbnormalCriticalHighNotifier(AlarmNotifier):
    alarm_type = 'AHH'
    email_template_name = 'alarm_notifications/abnormal_critical_high_level.html'
    email_subject ='Abnormal Critical High level notification'
    
    def extract_mail_list(self):
        try:
             #only send abnormaly tank level to me or smartflow support;Abnormal is when current tank volume level is beyond tank capacity
            parsed_mail_list = ['ridwan.yusuf@smartflowtech.com', 'idowu.sekoni@smartflowtech.com','idowu.sekoni@smartflowtech.coms']
            
        except AttributeError:
            parsed_mail_list = []
        finally:
            return parsed_mail_list


class ReorderNotifier(AlarmNotifier):
    alarm_type = 'reorder'
    email_template_name = 'alarm_notifications/reorder_level.html'
    email_subject = 'Tank Reorder notification'
    
    def extract_mail_list(self):
        try:
            parsed_mail_list = list(map(lambda mail: mail.strip(), self.tank.Site.Reorder_mail.split(','))) #strip white spaces away
        except AttributeError:
            parsed_mail_list = ['','']
        finally:
            return parsed_mail_list

class AnomalyFactory:
    def __init__(self, tank, volume, log_time, logger):
        self.tank = tank
        self.volume = volume
        self.log_time = log_time
        self.logger = logger

    def create_anomaly_report(self):
        if self.tank.LL_Level and self.volume < self.tank.LL_Level:
            return CriticalLowNotifier(self.tank, self.volume, self.log_time, self.logger)
        elif self.tank.Reorder and self.volume < self.tank.Reorder:
            return ReorderNotifier(self.tank, self.volume, self.log_time, self.logger)
        elif self.tank.HH_Level and self.tank.HH_Level > 0 and self.volume > self.tank.HH_Level and self.volume > self.tank.Capacity :
            #abnormal critical high level when tank volume is greater than capacity probably due to a spark
            #Send mail to only me or Smartflow 
            return AbnormalCriticalHighNotifier(self.tank, self.volume, self.log_time, self.logger)
        elif self.tank.HH_Level and self.tank.HH_Level > 0 and self.volume > self.tank.HH_Level:
            return CriticalHighNotifier(self.tank, self.volume, self.log_time, self.logger)

class AlarmFactory:
    def __init__(self, tank, volume, log_time, logger):
        self.tank = tank
        self.volume = volume
        self.log_time = log_time
        self.logger = logger

    def create_alarm_notifier(self):
        # there are three alarm levels
        # 1. Critically low
        # 2. Reorder
        # 3. Critically high
        if self.tank.LL_Level and self.volume < self.tank.LL_Level:
            return CriticalLowNotifier(self.tank, self.volume, self.log_time, self.logger)
        elif self.tank.Reorder and self.volume < self.tank.Reorder:
            return ReorderNotifier(self.tank, self.volume, self.log_time, self.logger)
        elif self.tank.HH_Level and self.tank.HH_Level > 0 and self.volume > self.tank.HH_Level and self.volume > self.tank.Capacity :
            #abnormal critical high level when tank volume is greater than capacity probably due to a spark
            #Send mail to only me or Smartflow 
            return AbnormalCriticalHighNotifier(self.tank, self.volume, self.log_time, self.logger)
        elif self.tank.HH_Level and self.tank.HH_Level > 0 and self.volume > self.tank.HH_Level:
            return CriticalHighNotifier(self.tank, self.volume, self.log_time, self.logger)


def convert_current_to_height(tank: models.Tanks, current: float) -> Optional[float]:

    tank_id = tank.Tank_id
    tank_controller = tank.Tank_controller
    #GET ANALOG CHART
    #get tank probe
    try:
        tank_probe = models.Probes.objects.get(slug=tank_controller)
    except models.Probes.DoesNotExist:
        tank_probe = None
    if tank_probe is None:
        return None
    #get probe chart link
    analog_chart_path = tank_probe.probe_chart.path
    #Get chart in dict
    chart = fh.chart_processor_full(analog_chart_path)
    #Convert current to height
    height = fh.current_to_height_interpolation_formula(current=current,prev_chart_entry=chart[0], next_chart_entry=chart[1])
    #Add offset if it exists
    # Get offset
    offset = tank.Offset
    if offset:
        height = height*offset
    return height

def convert_height_to_volume(tank: models.Tanks, height: float) -> Tuple[Optional[int], Optional[float]]:
    key = 'Tank'+str(tank.pk)
    print(tank, 'yes oo')
    calibration_chart = fh.get_tank_calibration_chart(tank)
    #Convert height to volume
    temp = fh.lookup_chart(height, calibration_chart)
    if isinstance(temp, tuple):
        _height, prev_dict, next_dict = temp
        volume = fh.height_to_volume_interpolation_formula(height=_height, prev_chart_entry=prev_dict, next_chart_entry=next_dict)
    else:
        chart = temp
        volume = fh.height_to_volume_interpolation_formula(chart=chart)

    flag = fh.last_entered_pv(key, volume)
    return (flag, volume)