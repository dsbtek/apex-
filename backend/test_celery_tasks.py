from unittest import mock
import csv
import os
import shutil
from tempfile import NamedTemporaryFile, gettempdir

from django.core.files import File
from django.test import override_settings
from django.conf import settings
from django.test import TestCase
from django.core import mail

from . import models
from .tasks import tank_alarm_task, analog_probe_logger

class SmarteyeTankDataTaskTests(TestCase):
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
            'Reorder_mail': 'solankerahman@gmail.com',
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


    def test_tank_alarm_task(self):
        logs = [(54563, '2019-04-30 20:50:13', '16733.099609375', '1', '152.100006103516', 'b8:27:eb:97:8c:12', 1, 2, None, None, None, 'MTC'),
                (54561, '2019-04-30 20:50:08', '4500.0', '1', '5.19999980926514', 'b8:27:eb:97:8c:12', 1, 1, None, None, None, 'MTC'),
                (54562, '2019-04-30 20:50:40', '328.400024414063', '1', '278.5', 'b8:27:eb:97:8c:12', 1, 3, None, None, None, 'MTC'),
                ]
        tank_alarm_task(logs)
        #alarm less than 30 mins are not sent
        self.assertEqual(len(mail.outbox), 0)

    
    def test_no_alarm_on_site_without_email_notification(self):
        s = models.Sites.objects.get(pk=1)
        s.Email_Notification = False
        s.save()

        logs = [(54563, '2019-04-30 20:50:13', '16733.099609375', '1', '152.100006103516', 'b8:27:eb:97:8c:12', 1, 2, None, None, None, 'MTC'),
                (54561, '2019-04-30 20:50:08', '4500.0', '1', '5.19999980926514', 'b8:27:eb:97:8c:12', 1, 1, None, None, None, 'MTC'),
                (54562, '2019-04-30 20:50:08', '328.400024414063', '1', '278.5', 'b8:27:eb:97:8c:12', 1, 2, None, None, None, 'MTC'),
                ]
        tank_alarm_task(logs)
        self.assertEqual(len(mail.outbox), 0)

    def test_no_alarm_exception_on_invalid_tank(self):
        logs = [(54563, '2019-04-30 20:50:13', '16733.099609375', '1', '152.100006103516', 'b8:27:eb:97:8c:12', 2, 2, None, None, None, 'MTC'),
                (54561, '2019-04-30 20:50:08', '4500.0', '1', '5.19999980926514', 'b8:27:eb:97:8c:12', 2, 1, None, None, None, 'MTC'),
                (54562, '2019-04-30 20:50:08', '328.400024414063', '1', '278.5', 'b8:27:eb:97:8c:12', 3, 2, None, None, None, 'MTC'),
                ]
        tank_alarm_task(logs)
        # self.assertEqual(len(mail.outbox), 0)

    def test_no_alarm_on_valid_log(self):
        logs = [(54563, '2019-04-30 20:50:13', '12733.099609375', '1', '152.100006103516', 'b8:27:eb:97:8c:12', 1, 2, None, None, None, 'MTC')]
        tank_alarm_task(logs)
        self.assertEqual(len(mail.outbox), 0)


class SmarteyeSensorLoggerTask(TestCase):
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
        f.name += '.csv'
        self.make_current_chart(f.name)
        chart = f.name
        
        data1 = {
            'name': 'Test Probe 1',
            'slug': 'PRB1'
        }
        probe1 = models.Probes.objects.create(**data1)
        probe1.probe_chart.save('chart1.csv', File(open(chart, 'rb')))

        g = NamedTemporaryFile()
        g.name += '.csv'
        self.make_volume_chart(g.name)
        chart = g.name
        
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
        # super().tearDownClass()

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
    
    # @mock.patch('backend.tasks.cu')
    # @mock.patch('backend.tasks.tank_alarm_task')
    # def test_analog_logger_task(self, mock_task, mock_utils):
    #     mock_task.delay.side_effect = print('YSent to alarm task!')
    #     mock_utils.convert_current_to_height.return_value = 10
    #     mock_utils.convert_height_to_volume.return_value = (1, 500)
    #     sensor_logs = [(1,1,1,'4.587','1.10','b8:27:eb:97:8c:12','SEN','2020-10-01 13:56')]
    #                     # (2,1,1,'4.902','1.20','b8:27:eb:97:8c:12','SEN','2020-10-01 14:00'),
    #                     # (3,1,1,'5.20','1.60','b8:27:eb:97:8c:12','SEN','2020-10-01 14:06')]
    #     analog_probe_logger(sensor_logs)
    #     # mock_task.delay.assert_called_once()
    #     mock_utils.convert_current_to_height.assert_called_once()
    #     mock_utils.convert_height_to_volume.assert_called_once()
    #     self.assertEqual(models.AtgPrimaryLog.objects.count(), 1)
    #     saved_log = models.AtgPrimaryLog.objects.first()
    #     self.assertEqual(saved_log.pv, '500')
    #     self.assertEqual(saved_log.pv_flag, '1')
    #     self.assertEqual(saved_log.sv, '10.0')
    #     self.assertEqual(saved_log.temperature, '4.59')
