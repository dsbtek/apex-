import csv
import shutil
import os
import fakeredis
from unittest.mock import patch
from tempfile import NamedTemporaryFile, gettempdir

from django.urls import reverse
from django.test import override_settings
from django.core.files import File
from django.contrib.auth import get_user_model
from django.conf import settings

from rest_framework import status
from rest_framework.test import APITestCase

from .. import models
#test cicd autodeployment

def make_chart(filename):
    with open(filename, 'w') as chart:
        writer = csv.writer(chart, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['Height(mm)','Volume(ltrs)'])
        writer.writerow(['0', '10'])
        writer.writerow(['20', '200'])
        writer.writerow(['40', '400'])
        writer.writerow(['50', '480'])
        writer.writerow(['100', '1000'])

class TankModelTest(APITestCase):
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
        product_data = {
            'Name': 'Petrol',
            'Code': 'PMS'
        }
        models.Products.objects.create(**product_data)
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
            'Number_of_tanks': 3,
            'Country': 'Nigeria',
            'State':'Lagos',
            'City': 'Ikeja',
            'Address':'Plot E, Ikosi Road',
            'Site_type': 'Mining'
        }
        models.Sites.objects.create(**data)

    @classmethod
    @override_settings(MEDIA_ROOT=gettempdir())
    def tearDownClass(cls):
        #remove calibration_charts dir from tmp
        try:
            shutil.rmtree(os.path.join(settings.MEDIA_ROOT, 'calibration_charts'))
        except OSError as e:
            print(e)
    

    @override_settings(MEDIA_ROOT=gettempdir())
    def test_can_create_tank_model(self):
        f = NamedTemporaryFile()
        f.name += '.csv'
        make_chart(f.name)
        chart = f.name

        data = {
            'Name': 'Test Tank',
            'Controller_polling_address': 1,
            'Tank_index': 1,
            'Capacity': 10000,
            'Site_id': 1,
            'Product_id': 1
        }
        tank = models.Tanks.objects.create(**data)
        tank.CalibrationChart.save('calib_chart.csv', File(open(chart, 'rb')))
        self.assertEqual(models.Tanks.objects.count(), 1)
        

class TankCreateViewsTests(APITestCase):
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
        product_data = {
            'Name': 'Petrol',
            'Code': 'PMS'
        }
        models.Products.objects.create(**product_data)
        models.Sites.objects.create(**data)
        get_user_model().objects.create_user(Email='rahman.s@e360africa.com')
        self.authenticator()

    @classmethod
    @override_settings(MEDIA_ROOT=gettempdir())
    def tearDownClass(cls):
        #remove calibration_charts dir from tmp
        try:
            shutil.rmtree(os.path.join(settings.MEDIA_ROOT, 'calibration_charts'))
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
    def test_can_create_tank(self):
        url = reverse('tank_list')
        f = NamedTemporaryFile()
        f.name += '.csv'
        make_chart(f.name)
        chart_url = f.name
        with open(chart_url, 'rb') as chart:
            data = {
                'Name': 'Test Tank',
                'Product': 1,
                'Controller_polling_address': 1,
                'Tank_index': 1,
                'Capacity': 10000,
                'Site_id': 1,
                'Control_mode': 'C',
                'Tank_controller': 'MTC',
                'UOM': 'L',
                'Shape': 'LC',
                'CalibrationChart': chart
            }
            response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_tank_unique_validator(self):
        url = reverse('tank_list')
        data = {
                'Name': 'Test Tank',
                'Product': 1,
                'Controller_polling_address': 1,
                'Tank_index': 1,
                'Capacity': 10000,
                'Site_id': 1,
                'Control_mode': 'C',
                'Tank_controller': 'MTC',
                'UOM': 'L',
                'Shape': 'LC'
            }
        self.client.post(url, data=data, format='json')
        #Should not be able to create anothe tank with same address within same site
        data = {
                'Name': 'Test Tank',
                'Product': 1,
                'Controller_polling_address': 1,
                'Tank_index': 1,
                'Capacity': 5000,
                'Site_id': 1,
                'Control_mode': 'C',
                'Tank_controller': 'MTC',
                'UOM': 'L',
                'Shape': 'LC'
            }
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_can_not_create_tank_when_site_max_tanks_exceeded(self):
        url = reverse('tank_list')
        data = {
                'Name': 'Test Tank',
                'Product': 1,
                'Controller_polling_address': 1,
                'Tank_index': 1,
                'Capacity': 10000,
                'Site_id': 1,
                'Control_mode': 'C',
                'Tank_controller': 'MTC',
                'UOM': 'L',
                'Shape': 'LC'
            }
        self.client.post(url, data=data, format='json')
        #site's number of tanks is 1, so limit has been reached
        data = {
                'Name': 'Test Tank',
                'Product': 1,
                'Controller_polling_address': 1,
                'Tank_index': 2,
                'Capacity': 5000,
                'Site_id': 1,
                'Control_mode': 'C',
                'Tank_controller': 'MTC',
                'UOM': 'L',
                'Shape': 'LC'
            }
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TankRetrieveTests(APITestCase):
    @override_settings(MEDIA_ROOT=gettempdir())
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
        company_data_2 = {
            'Name': 'Test Company 2',
            'Country': 'Nigeria',
            'State':'Lagos',
            'City': 'Ikeja',
            'Address':'Plot E, Ikosi Road',
            'Company_type': 'Large',
            'Contact_person_name': 'Rahman Solanke',
            'Contact_person_designation': 'Tech Lead',
            'Contact_person_mail': 'rahman.s@e360africa.com',
            'Contact_person_phone': '08146646207',
            'Owned': True
        }
        models.Companies.objects.create(**company_data_1)
        models.Companies.objects.create(**company_data_2)
        device_data_1 = {
            'Name': 'Test Device 1',
            'Device_unique_address': 'b8:27:eb:97:8c:12',
            'Company_id': 1,
            'Active': True
        }
        device_data_2 = {
            'Name': 'Test Device 2',
            'Device_unique_address': 'b8:27:eb:97:8c:13',
            'Company_id': 1,
            'Active': True
        }
        device_data_3 = {
            'Name': 'Test Device 3',
            'Device_unique_address': 'b8:27:eb:97:8c:14',
            'Company_id': 2,
            'Active': True
        }
        models.Devices.objects.create(**device_data_1)
        models.Devices.objects.create(**device_data_2)
        models.Devices.objects.create(**device_data_3)
        data_1 = {
            'Name': 'Test Site 1',
            'Company_id': 1,
            'Device_id': 1,
            'Number_of_tanks': 3,
            'Country': 'Nigeria',
            'State':'Lagos',
            'City': 'Ikeja',
            'Address':'Plot E, Ikosi Road',
            'Site_type': 'Mining'
        }
        data_2 = {
            'Name': 'Test Site 2',
            'Company_id': 1,
            'Device_id': 2,
            'Number_of_tanks': 3,
            'Country': 'Nigeria',
            'State':'Lagos',
            'City': 'Ikeja',
            'Address':'Plot E, Ikosi Road',
            'Site_type': 'Mining'
        }
        data_3 = {
            'Name': 'Test Site 3',
            'Company_id': 2,
            'Device_id': 3,
            'Number_of_tanks': 3,
            'Country': 'Nigeria',
            'State':'Lagos',
            'City': 'Ikeja',
            'Address':'Plot E, Ikosi Road',
            'Site_type': 'Mining'
        }
        models.Sites.objects.create(**data_1)
        models.Sites.objects.create(**data_2)
        models.Sites.objects.create(**data_3)
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
            'Site_id': 1,
        }
        tank_2 = {
            'Name': 'Test Tank 2',
            'Controller_polling_address': 1,
            'Tank_index': 2,
            'Capacity': 15000,
            'Site_id': 1,
        }
        tank_3 = {
            'Name': 'Test Tank 3',
            'Controller_polling_address': 1,
            'Tank_index': 1,
            'Capacity': 8000,
            'Site_id': 2,
        }
        tank_4 = {
            'Name': 'Test Tank 1',
            'Controller_polling_address': 1,
            'Tank_index': 2,
            'Capacity': 10000,
            'Site_id': 2,
        }
        tank_5 = {
            'Name': 'Test Tank 2',
            'Controller_polling_address': 1,
            'Tank_index': 1,
            'Capacity': 15000,
            'Site_id': 3,
        }
        tank_6 = {
            'Name': 'Test Tank 3',
            'Controller_polling_address': 1,
            'Tank_index': 2,
            'Capacity': 8000,
            'Site_id': 3,
        }
        f = NamedTemporaryFile()
        f.name += '.csv'
        make_chart(f.name)
        chart = f.name

        tank1 = models.Tanks.objects.create(**tank_1)
        tank1.CalibrationChart.save('calib_chart_1.csv', File(open(chart, 'rb')))
        tank2 = models.Tanks.objects.create(**tank_2)
        tank2.CalibrationChart.save('calib_chart_2.csv', File(open(chart, 'rb')))
        tank3 = models.Tanks.objects.create(**tank_3)
        tank3.CalibrationChart.save('calib_chart_3.csv', File(open(chart, 'rb')))
        models.Tanks.objects.create(**tank_4)
        models.Tanks.objects.create(**tank_5)
        models.Tanks.objects.create(**tank_6)
        get_user_model().objects.create_user(Email='rahman.s@e360africa.com')
        self.authenticator()

    @classmethod
    @override_settings(MEDIA_ROOT=gettempdir())
    def tearDownClass(cls):
        #remove calibration_charts dir from tmp
        try:
            shutil.rmtree(os.path.join(settings.MEDIA_ROOT, 'calibration_charts'))
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

    def test_can_retrieve_all_tanks(self):
        url = reverse('all_tank_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 6)
    
    def test_can_retrieve_non_E360_tanks(self):
        url = reverse('tank_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 4)
    
    def test_retrieve_a_valid_tank(self):
        url = reverse('tank_detail', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['data']['Tank_id'], 1)

    def test_retrieve_an_invalid_tank(self):
        url = reverse('tank_detail', kwargs={'pk': 20})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_tanks_in_a_company(self):
        url = reverse('tanks_by_company', kwargs={'pk':1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 4)

    def test_retrieve_tanks_in_a_site(self):
        url = reverse('tanks_by_site', kwargs={'pk':1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 2)

    def test_retrieve_tanks_in_a_sitegroup(self):
        url = reverse('tanks_by_sitegroup')
        response = self.client.post(url, data={'site_ids': [1,2]}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 4)

    def test_retrieve_tank_ids_from_site(self):
        url = reverse('site_tank_ids')
        response = self.client.post(url, data={'site': 1}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 2)

    @override_settings(MEDIA_ROOT=gettempdir())
    @patch('backend.tanks.views.redis.Redis', fakeredis.FakeRedis)
    def test_read_tank_calibration_chart(self):
        url = reverse('read_tank_chart', kwargs={'pk':1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TankUpdateTests(APITestCase):
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
        product_data = {
            'Name': 'Petrol',
            'Code': 'PMS'
        }
        models.Products.objects.create(**product_data)
        models.Sites.objects.create(**data)
        tank_1 = {
            'Name': 'Test Tank 1',
            'Controller_polling_address': 1,
            'Tank_index': 1,
            'Capacity': 8000,
            'Site_id': 1,
        }
        f = NamedTemporaryFile()
        f.name += '.csv'
        make_chart(f.name)
        chart = f.name

        tank1 = models.Tanks.objects.create(**tank_1)
        tank1.CalibrationChart.save('calib_chart_1.csv', File(open(chart, 'rb')))
        get_user_model().objects.create_user(Email='rahman.s@e360africa.com')
        self.authenticator()

    @classmethod
    @override_settings(MEDIA_ROOT=gettempdir())
    def tearDownClass(cls):
        #remove calibration_charts dir from tmp
        try:
            shutil.rmtree(os.path.join(settings.MEDIA_ROOT, 'calibration_charts'))
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
    def test_partial_update_tank(self):
        url = reverse('tank_detail', kwargs={'pk':1})
        f = NamedTemporaryFile()
        f.name += '.csv'
        make_chart(f.name)
        chart_url = f.name
        with open(chart_url, 'rb') as chart:
            data = {
                'Name': 'New Tank',
                'CalibrationChart': chart
            }
            response = self.client.put(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['data']['Name'], 'New Tank')

    def test_delete_tank(self):
        url = reverse('tank_detail', kwargs={'pk':1})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(models.Tanks.objects.count(), 0)