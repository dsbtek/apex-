
import csv
from django.contrib.auth import get_user_model

from django.urls import reverse
from django.test import override_settings
from django.core.files import File
from tempfile import NamedTemporaryFile, gettempdir
from django.conf import settings

from rest_framework import status
from rest_framework.test import APITestCase

from unittest.mock import patch, MagicMock

from .. import models



def make_chart(filename):
    with open(filename, 'w') as chart:
        writer = csv.writer(chart, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['Height(mm)','Volume(ltrs)'])
        writer.writerow(['0', '10'])
        writer.writerow(['20', '200'])
        writer.writerow(['40', '400'])
        writer.writerow(['50', '480'])
        writer.writerow(['100', '1000'])


class TestTrends(APITestCase):
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
    def createTank(self):
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

    def setUp(self):
        user_data = {
            'Email': "rahman.s@e360africa.com",
            'password': 'password'
        }

        get_user_model().objects.create_user(**user_data)
        self.authenticator()
        self.createTank()

    @patch('backend.trends.views.connection')
    def test_valid_tanks_range(self, mock_conn):
        """
            test for valid tanks list and valid date range
        """
        m = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = m

        url = reverse('trends')
        data = {
            "tanks": [1, 2, 3],
            "start": "2021-01-13 16:54",
            "end": "2021-01-14 16:54"
        }
        response = self.client.post(url, data, format='json')
        m.execute.assert_called_once()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('backend.trends.views.connection')
    def test_valid_tank_valid_range(self, mock_conn):
        """
            test for valid tank and valid date range
        """
        m = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = m

        url = reverse('trends')
        data = {
            "tanks": [6],
            "start": "2021-01-13 16:54",
            "end": "2021-01-14 16:54"
        }
        response = self.client.post(url, data, format='json')
        m.execute.assert_called_once()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('backend.trends.views.connection')
    def test_valid_tanks_invalid_date(self, mock_conn):
        """
            test for valid tanks and invalid date range
        """
        m = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = m

        url = reverse('trends')
        data = {
            "tanks": [5, 4, 3],
            "start": "2021-01-14 16:54",
            "end": "2021-01-13 16:54"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_empty_tank_valid_range(self):
        """
            test for empty tank list and valid date range
        """
        url = reverse('trends')
        data = {
            "tanks": [],
            "start": "2021-01-13 16:54",
            "end": "2021-01-14 16:54"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
