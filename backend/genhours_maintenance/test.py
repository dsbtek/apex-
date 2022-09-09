from tempfile import NamedTemporaryFile, gettempdir
import shutil
import os
from PIL import Image
from unittest.mock import patch

from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.core.files import File
from django.conf import settings

from rest_framework import status
from rest_framework.test import APITestCase

from .. import models


class MaintenanceConfigCreateTests(APITestCase):
    def setUp(self):
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
        device_data = {
            'Name': 'Test Device 1',
            'Device_unique_address': 'b8:27:eb:97:8c:12',
            'Company_id': 1,
            'Active': True
        }
        models.Devices.objects.create(**device_data)
        site_data = {
            'Name': 'Test Site',
            'Company_id': 1,
            'Device_id': 1,
            'Number_of_tanks': 1,
            'Country': 'Nigeria',
            'State':'Lagos',
            'City': 'Ikeja',
            'Address':'Plot E, Ikosi Road',
            'Site_type': 'Mining'
        }
        models.Sites.objects.create(**site_data)
        models.Products.objects.create(**{
            'Name': 'Petrol',
            'Code': 'PMS'
        })
        equipment = {
            'name': 'Test Equipment',
            'product_id': 1,
            'oem': 'CAT',
            'model': 'R-100',
            'oem_consumption_rate': 30.45,
            'running_hours_source': 'DI',
            'litres_consumed_source': 'TL',
            'address': 1,
            'flowmeter_id': None,
            'model': 'Yamaha',
            'initial_totaliser_hours': 20,
            'site_id': 1,
        }
        models.Equipment.objects.create(**equipment)
        get_user_model().objects.create_user(Email='rahman.s@e360africa.com')
        self.authenticator()

    def authenticator(self):
        url = reverse('login')
        data = {
            'Email': 'rahman.s@e360africa.com',
            'password': 'password'
        }
        response = self.client.post(url, data, format='json')
        token = response.json()['data']['token']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)

    def test_can_register_maintenance_config(self):
        url = reverse('equipment_maintenance_config')
        data = {
            'equipment_id': 1,
            'mode': 'HR/D',
            'hours': 100,
            'days': 20,
            'scheduled_days': None
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class MaintenanceConfigRetrieveUpdateTests(APITestCase):
    def setUp(self):
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
        device_data = {
            'Name': 'Test Device 1',
            'Device_unique_address': 'b8:27:eb:97:8c:12',
            'Company_id': 1,
            'Active': True
        }
        models.Devices.objects.create(**device_data)
        data = {
            'Name': 'Test Site',
            'Company_id': 1,
            'Device_id': 1,
            'Number_of_tanks': 1,
            'Country': 'Nigeria',
            'State':'Lagos',
            'City': 'Ikeja',
            'Address':'Plot E, Ikosi Road',
            'Site_type': 'Mining'
        }
        models.Sites.objects.create(**data)
        models.Products.objects.create(**{
            'Name': 'Petrol',
            'Code': 'PMS'
        })
        gen_1 = {
            'name': 'Test Equipment 1',
            'product_id': 1,
            'oem': 'CAT',
            'model': 'R-100',
            'oem_consumption_rate': 30.45,
            'running_hours_source': 'DI',
            'litres_consumed_source': 'TL',
            'address': 1,
            'model': 'Yamaha',
            'initial_totaliser_hours': 20,
            'site_id': 1,
        }
        gen_2 = {
            'name': 'Test Equipment 2',
            'product_id': 1,
            'oem': 'CAT',
            'model': 'R-200',
            'oem_consumption_rate': 30.45,
            'running_hours_source': 'DI',
            'litres_consumed_source': 'TL',
            'address': 2,
            'model': 'Yamaha',
            'initial_totaliser_hours': 20,
            'site_id': 1,
        }
        models.Equipment.objects.create(**gen_1)
        models.Equipment.objects.create(**gen_2)

        config_1 = {
            'equipment_id': 1,
            'mode': 'HR/D',
            'hours': 100,
            'days': 20,
            'scheduled_days': None
        }
        config_2 = {
            'equipment_id': 2,
            'mode': 'SCH',
            'hours': None,
            'days': None,
            'scheduled_days': 30
        }
        models.MaintenanceConfig.objects.create(**config_1)
        models.MaintenanceConfig.objects.create(**config_2)
        get_user_model().objects.create_user(Email='rahman.s@e360africa.com')
        self.authenticator()

    def authenticator(self):
        url = reverse('login')
        data = {
            'Email': 'rahman.s@e360africa.com',
            'password': 'password'
        }
        response = self.client.post(url, data, format='json')
        token = response.json()['data']['token']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)

    def test_retrieve_all_equipment_maintenance_config(self):
        url = reverse('equipment_maintenance_config')
        response = self.client.get(url)
        self.assertEqual(len(response.json()['data']), 2)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_valid_equipment_maintenance_config(self):
        url = reverse('equipment_maintenance_config_detail', kwargs={'pk':1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_maintenance_config(self):
        url = reverse('equipment_maintenance_config_detail', kwargs={'pk':1})
        data = {
            'mode': 'SCH',
            'scheduled_days': 30,
            'hours': None,
            'days': None
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class MaintenanceInfoCreateTests(APITestCase):
    def setUp(self):
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
        device_data = {
            'Name': 'Test Device 1',
            'Device_unique_address': 'b8:27:eb:97:8c:12',
            'Company_id': 1,
            'Active': True
        }
        models.Devices.objects.create(**device_data)
        data = {
            'Name': 'Test Site',
            'Company_id': 1,
            'Device_id': 1,
            'Number_of_tanks': 1,
            'Country': 'Nigeria',
            'State':'Lagos',
            'City': 'Ikeja',
            'Address':'Plot E, Ikosi Road',
            'Site_type': 'Mining'
        }
        models.Sites.objects.create(**data)
        models.Products.objects.create(**{
            'Name': 'Petrol',
            'Code': 'PMS'
        })
        gen_1 = {
            'name': 'Test Equipment 1',
            'product_id': 1,
            'oem': 'CAT',
            'model': 'R-100',
            'oem_consumption_rate': 30.45,
            'running_hours_source': 'DI',
            'litres_consumed_source': 'TL',
            'address': 1,
            'model': 'Yamaha',
            'initial_totaliser_hours': 20,
            'site_id': 1,
        }
        gen_2 = {
            'name': 'Test Equipment 2',
            'product_id': 1,
            'oem': 'CAT',
            'model': 'R-200',
            'oem_consumption_rate': 30.45,
            'running_hours_source': 'DI',
            'litres_consumed_source': 'TL',
            'address': 2,
            'model': 'Yamaha',
            'initial_totaliser_hours': 20,
            'site_id': 1,
        }
        models.Equipment.objects.create(**gen_1)
        models.Equipment.objects.create(**gen_2)
        get_user_model().objects.create_user(Email='rahman.s@e360africa.com')
        self.authenticator()

    @classmethod
    @override_settings(MEDIA_ROOT=gettempdir())
    def tearDownClass(cls):
        #remove calibration_charts dir from tmp
        try:
            shutil.rmtree(os.path.join(settings.MEDIA_ROOT, 'maintenance_images'))
        except OSError as e:
            print(e)

    def authenticator(self):
        url = reverse('login')
        data = {
            'Email': 'rahman.s@e360africa.com',
            'password': 'password'
        }
        response = self.client.post(url, data, format='json')
        token = response.json()['data']['token']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
    
    @override_settings(MEDIA_ROOT=gettempdir())
    def test_can_add_new_maintenance_info(self):
        url = reverse('equipment_maintenance_info')
        f = NamedTemporaryFile()
        f.name += '.png'
        image_1 = Image.new('RGBA', (200, 200), 'white')
        image_1.save(f.name)
        image_1_file = open(f.name, 'rb')
        
        g = NamedTemporaryFile()
        g.name += '.png'
        image_2 = Image.new('RGBA', (200, 200), 'black')
        image_2.save(g.name)
        image_2_file = open(g.name, 'rb')

        data = {
            'equipment_id': 1,
            'maintenance_date': "2020-09-21",
            'images': [image_1_file, image_2_file],
            'genhours': "700",
            'notes': "jdgjdiuhdbjdjh"
        }

        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        #get the images of the info
        info_id = response.json()['data']['id']
        image_count = models.MaintenanceInfoImage.objects.filter(maintenance_info=info_id).count()
        self.assertEqual(image_count, 2)


class MaintenanceInfoRetrieveTests(APITestCase):
    @override_settings(MEDIA_ROOT=gettempdir())
    def setUp(self):
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
        device_data = {
            'Name': 'Test Device 1',
            'Device_unique_address': 'b8:27:eb:97:8c:12',
            'Company_id': 1,
            'Active': True
        }
        models.Devices.objects.create(**device_data)
        data = {
            'Name': 'Test Site',
            'Company_id': 1,
            'Device_id': 1,
            'Number_of_tanks': 1,
            'Country': 'Nigeria',
            'State':'Lagos',
            'City': 'Ikeja',
            'Address':'Plot E, Ikosi Road',
            'Site_type': 'Mining'
        }
        models.Sites.objects.create(**data)
        models.Products.objects.create(**{
            'Name': 'Petrol',
            'Code': 'PMS'
        })
        gen_1 = {
            'name': 'Test Equipment 1',
            'product_id': 1,
            'oem': 'CAT',
            'model': 'R-100',
            'oem_consumption_rate': 30.45,
            'running_hours_source': 'DI',
            'litres_consumed_source': 'TL',
            'address': 1,
            'model': 'Yamaha',
            'initial_totaliser_hours': 20,
            'site_id': 1,
        }
        gen_2 = {
            'name': 'Test Equipment 2',
            'product_id': 1,
            'oem': 'CAT',
            'model': 'R-200',
            'oem_consumption_rate': 30.45,
            'running_hours_source': 'DI',
            'litres_consumed_source': 'TL',
            'address': 2,
            'model': 'Yamaha',
            'initial_totaliser_hours': 20,
            'site_id': 1,
        }
        models.Equipment.objects.create(**gen_1)
        models.Equipment.objects.create(**gen_2)
        config_1 = {
            'equipment_id': 1,
            'mode': 'HR/D',
            'hours': 100,
            'days': 20,
            'scheduled_days': None
        }
        config_2 = {
            'equipment_id': 2,
            'mode': 'SCH',
            'hours': None,
            'days': None,
            'scheduled_days': 30
        }
        models.MaintenanceConfig.objects.create(**config_1)
        models.MaintenanceConfig.objects.create(**config_2)
        info_1 = {
            'equipment_id': 1,
            'maintenance_date': "2020-09-21",
            'notes': "jbdjgjsugifkjbvfuifjbkvugisjvudsjbkvhbdsv",
            'genhours': 800
        }
        info_2 = {
            'equipment_id': 1,
            'maintenance_date': "2020-08-21",
            'notes': "jkdgjkvdsguiueueinvm vhzxhouhioahiovauoudaj",
            'genhours': 550
        }
        info_3 = {
            'equipment_id': 2,
            'maintenance_date': "2020-09-02",
            'notes': "khsvdbhildsyuhsdbjkdsvilugbdsgilkueaiuabkj",
            'genhours': 475
        }
        info_4 = {
            'equipment_id': 2,
            'maintenance_date': "2020-09-17",
            'notes': "bjvsnbjkvslkjhjuaoushjsvbjjlvbjskcjgisvbkm",
            'genhours': 600
        }
        f = NamedTemporaryFile()
        f.name += '.png'
        image_1 = Image.new('RGBA', (200, 200), 'white')
        image_1.save(f.name)

        info_1 = models.MaintenanceInfo.objects.create(**info_1)
        info_1_image_1 = models.MaintenanceInfoImage.objects.create(maintenance_info_id=info_1.id)
        info_1_image_1.image.save('image_1.png', File(open(f.name, 'rb')))
        info_1_image_2 = models.MaintenanceInfoImage.objects.create(maintenance_info_id=info_1.id)
        info_1_image_2.image.save('image_2.png', File(open(f.name, 'rb')))

        info_2 = models.MaintenanceInfo.objects.create(**info_2)
        info_2_image_1 = models.MaintenanceInfoImage.objects.create(maintenance_info_id=info_2.id)
        info_2_image_1.image.save('image_3.png', File(open(f.name, 'rb')))
        info_2_image_2 = models.MaintenanceInfoImage.objects.create(maintenance_info_id=info_2.id)
        info_2_image_2.image.save('image_4.png', File(open(f.name, 'rb')))

        info_3 = models.MaintenanceInfo.objects.create(**info_3)
        info_3_image_1 = models.MaintenanceInfoImage.objects.create(maintenance_info_id=info_3.id)
        info_3_image_1.image.save('image_5.png', File(open(f.name, 'rb')))
        info_3_image_2 = models.MaintenanceInfoImage.objects.create(maintenance_info_id=info_3.id)
        info_3_image_2.image.save('image_6.png', File(open(f.name, 'rb')))

        info_4 = models.MaintenanceInfo.objects.create(**info_4)
        info_4_image_1 = models.MaintenanceInfoImage.objects.create(maintenance_info_id=info_4.id)
        info_4_image_1.image.save('image_7.png', File(open(f.name, 'rb')))
        info_4_image_2 = models.MaintenanceInfoImage.objects.create(maintenance_info_id=info_4.id)
        info_4_image_2.image.save('image_8.png', File(open(f.name, 'rb')))

        get_user_model().objects.create_user(Email='rahman.s@e360africa.com')
        self.authenticator()

    @classmethod
    @override_settings(MEDIA_ROOT=gettempdir())
    def tearDownClass(cls):
        #remove calibration_charts dir from tmp
        try:
            shutil.rmtree(os.path.join(settings.MEDIA_ROOT, 'maintenance_images'))
        except OSError as e:
            print(e)

    def authenticator(self):
        url = reverse('login')
        data = {
            'Email': 'rahman.s@e360africa.com',
            'password': 'password'
        }
        response = self.client.post(url, data, format='json')
        token = response.json()['data']['token']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)

    def test_retrieve_maintenance_info_records(self):
        url = reverse('equipment_maintenance_info_records', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_maintenance_summary(self):
        url = reverse('equipment_maintenance_summary', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)