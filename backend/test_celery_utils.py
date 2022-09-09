import logging
import csv
import json
from unittest import mock
import os
import shutil
import fakeredis
from tempfile import NamedTemporaryFile, gettempdir

from django.core.files import File
from django.test import override_settings
from django.conf import settings
from django.test import TestCase
from django.core import mail

from . import celery_utils as cu
from . import models

logger = logging.getLogger(__name__)

class AlarmUtilTests(TestCase):
    def setUp(self):
        company_data_1 = {
            'Name': 'Test Company',
            'Country': 'Nigeria',
            'State':'Lagos',
            'City': 'Ikeja',
            'Address':'Plot E, Ikosi Road',
            'Company_type': 'Large',
            'Contact_person_name': 'Rahman Solanke',
            'Contact_person_designation': 'Tech Lead',
            'Contact_person_mail': 'rahman.s@e360africa.com',
            'Contact_person_phone': '08146646207'
        }
        models.Companies.objects.create(**company_data_1)
        device_data_1 = {
            'Name': 'Test Device 1',
            'Device_unique_address': 'b8:27:eb:97:8c:12',
            'Company_id': 1,
            'Active': True
        }
        models.Devices.objects.create(**device_data_1)
        data_1 = {
            'Name': 'Test Site 1',
            'Company_id': 1,
            'Device_id': 1,
            'Number_of_tanks': 3,
            'Country': 'Nigeria',
            'State':'Lagos',
            'City': 'Ikeja',
            'Address':'Plot E, Ikosi Road',
            'Site_type': 'Mining',
            'Critical_level_mail': 'solankerahman@gmail.com',
            'Reorder_mail': 'solankerahman@gmail.com, rahman.s@gmail.com',
        }
        models.Sites.objects.create(**data_1)
        product_data = {
            'Name': 'Petrol',
            'Code': 'PMS'
        }
        models.Products.objects.create(**product_data)
        tank_1 = {
            'Name': 'Test Tank 1',
            'Controller_polling_address': 1,
            'Tank_index': 1,
            'Capacity': 10000,
            'LL_Level': 1000,
            'HH_Level': 9800,
            'Reorder': 5000,
            'Site_id': 1,
        }
        tank_2 = {
            'Name': 'Test Tank 2',
            'Controller_polling_address': 1,
            'Tank_index': 2,
            'Capacity': 15000,
            'Site_id': 1,
            'LL_Level':1500,
            'HH_Level':14800,
            'Reorder':7000
        }
        tank_3 = {
            'Name': 'Test Tank 3',
            'Controller_polling_address': 1,
            'Tank_index': 3,
            'Capacity': 8000,
            'Site_id': 1,
            'LL_Level':500,
            'HH_Level':7900,
            'Reorder':3500
        }
        models.Tanks.objects.create(**tank_1)
        models.Tanks.objects.create(**tank_2)
        models.Tanks.objects.create(**tank_3)

    def test_alarm_notifier_factory(self):
        tank = models.Tanks.objects.get(pk=1)
        volume = 4800
        log_time = '2020-10-01 12:44'

        alarm_notifier = cu.AlarmFactory(tank, volume, log_time, logger).create_alarm_notifier()
        self.assertEqual(type(alarm_notifier), cu.ReorderNotifier)

    def test_alarm_notifier_send_mail(self):
        tank = models.Tanks.objects.get(pk=1)
        volume = 4800
        log_time = '2020-10-01 12:44'

        cu.ReorderNotifier(tank, volume, log_time, logger).notify()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Tank Reorder notification')
        
    @mock.patch.object(cu.AlarmNotifier, 'send_alarm_notification', return_value=1)
    def test_alarm_notifier_update_alarm_dispatcher(self, mock_send):
        tank = models.Tanks.objects.get(pk=1)
        volume = 4800
        log_time = '2020-10-01 12:44'

        cu.ReorderNotifier(tank, volume, log_time, logger).notify()
        mock_send.assert_called_once()
        tank_alarm_in_db = models.TankAlarmDispatcher.objects.get(tank_id=1, alarm_type='reorder')
        self.assertEqual(models.TankAlarmDispatcher.objects.filter(tank_id=1, alarm_type='reorder').count(), 1)


class SensorConverterUtilsTest(TestCase):
    
    @override_settings(MEDIA_ROOT=gettempdir())
    def setUp(self):
        #create company
        company_data = {
            'Name': 'Test Company',
            'Country': 'Nigeria',
            'State':'Lagos',
            'City': 'Ikeja',
            'Address':'Plot E, Ikosi Road',
            'Company_type': 'Large',
            'Contact_person_name': 'Rahman Solanke',
            'Contact_person_designation': 'Tech Lead',
            'Contact_person_mail': 'rahman.s@e360africa.com',
            'Contact_person_phone': '08146646207'
        }
        models.Companies.objects.create(**company_data)
        #create Device
        device_data = {
            'Name': 'Test Device 1',
            'Device_unique_address': 'b8:27:eb:97:8c:12',
            'Company_id': 1,
            'Active': True
        }
        models.Devices.objects.create(**device_data)
        #create Site
        site_data = {
            'Name': 'Test Site',
            'Company_id': 1,
            'Country': 'Nigeria',
            'State':'Lagos',
            'City': 'Ikeja',
            'Address':'Plot E, Ikosi Road',
            'Site_type': 'Mining',
            'Critical_level_mail': 'solankerahman@gmail.com',
            'Reorder_mail': 'solankerahman@gmail.com',
            'Device_id': 1,
            'Number_of_tanks': 3
        }
        models.Sites.objects.create(**site_data)
        #create Tanks
        models.Products.objects.create(Code='PMS', Name='Petroleum')
        
        f = NamedTemporaryFile()
        self.make_current_chart(f.name)
        chart = f.name
        
        data1 = {
            'name': 'Test Probe 1',
            'slug': 'PRB1'
        }
        probe1 = models.Probes.objects.create(**data1)
        probe1.probe_chart.save('chart1.csv', File(open(chart, 'rb')))

        f = NamedTemporaryFile()
        f.name += '.csv'
        self.make_volume_chart(f.name)
        chart = f.name
        
        tank_1 = {
            'Name': 'Tank 1',
            'Product_id': 1,
            'Site_id': 1,
            'Controller_polling_address': 1,
            'Tank_index': 1,
            'Capacity': 200,
            'UOM': 'L',
            'Shape': 'LC',
            'LL_Level': 50,
            'HH_Level': 200,
            'Reorder': 100,
            'Control_mode': 'SEN',
            'Tank_controller': 'PRB1'
        }
        tank_1 = models.Tanks.objects.create(**tank_1)
        tank_1.CalibrationChart.save('calib_chart_1.csv', File(open(chart, 'rb')))
    
    @classmethod
    @override_settings(MEDIA_ROOT=gettempdir())
    def tearDownClass(cls):
        try:
            shutil.rmtree(os.path.join(settings.MEDIA_ROOT, 'probe_charts'))
        except OSError as e:
            print(e)

    def make_current_chart(self, filename):
        with open(filename, 'w') as chart:
            writer = csv.writer(chart, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(['Current(mA)','Height(mm)'])
            writer.writerow(['4', '0'])
            writer.writerow(['20', '2000'])

    def make_volume_chart(self, filename):
        with open(filename, 'w') as chart:
            writer = csv.writer(chart, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(['Height(mm)', 'Volume(ltrs)'])
            writer.writerow(['0', '0'])
            writer.writerow(['500', '2500'])
            writer.writerow(['1000', '5000'])
            writer.writerow(['1500', '7500'])
            writer.writerow(['2000', '10000'])
    
    @override_settings(MEDIA_ROOT=gettempdir())
    def test_current_to_height_converter(self):
        tank = models.Tanks.objects.get(pk=1)
        current = 12
        height = cu.convert_current_to_height(tank, current)
        self.assertEqual(height, 1000)

    @override_settings(MEDIA_ROOT=gettempdir())
    @mock.patch('backend.celery_utils.fh.last_entered_pv')
    @mock.patch('backend.celery_utils.redis.Redis', fakeredis.FakeRedis)
    def test_height_to_volume_converter(self, mock_flag):
        tank = models.Tanks.objects.get(pk=1)
        height = 1000
        mock_flag.return_value = 1

        flag, volume = cu.convert_height_to_volume(tank, height)
        mock_flag.assert_called_once()

        self.assertEqual(flag, 1)
        self.assertEqual(volume, 5000)
