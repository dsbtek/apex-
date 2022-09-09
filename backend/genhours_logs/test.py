from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APITestCase

from datetime import datetime

import json

from .. import models


class GenHoursModelTest(APITestCase):
    def test_can_bulk_create_genhours_model(self):
        data = [models.GeneratorHours(mac_address='xx:xx:xx:xx',
                                      lineID=1, status=1, timestamp='2020-02-23 12:34') for _ in range(10)]

        models.GeneratorHours.objects.bulk_create(data)
        self.assertEqual(models.GeneratorHours.objects.count(), 10)


class GenHoursViewTest(APITestCase):
    def setUp(self):
        company_data = {
            'Name': 'Test Company',
            'Country': 'Nigeria',
            'State': 'Lagos',
            'City': 'Ikeja',
            'Address': 'Plot E, Ikosi Road',
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
            'State': 'Lagos',
            'City': 'Ikeja',
            'Address': 'Plot E, Ikosi Road',
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

    def test_genhours_logger(self):
        logs = ((1, 'b8:27:eb:37:b9:4e', 0, 0, 0, '2020-07-27 20:32:54'),
                (2, 'b8:27:eb:37:b9:4e', 1, 0, 0, '2020-07-27 20:32:54'),
                (3, 'b8:27:eb:37:b9:4e', 2, 0, 0, '2020-07-27 20:32:54'),
                (4, 'b8:27:eb:37:b9:4e', 3, 0, 0, '2020-07-27 20:32:54'),
                (5, 'b8:27:eb:37:b9:4e', 0, 0, 0, '2020-07-27 20:42:54'),
                (6, 'b8:27:eb:37:b9:4e', 1, 1, 0, '2020-07-27 20:42:54'),
                (7, 'b8:27:eb:37:b9:4e', 2, 0, 0, '2020-07-27 20:42:54'),
                (8, 'b8:27:eb:37:b9:4e', 3, 1, 0, '2020-07-27 20:42:54')
                )
        url = reverse('genhours_logger')
        response = self.client.post(url, data=logs, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(models.GeneratorHours.objects.count(), 8)

    def test_flowmeter_logger(self):
        logs = ((1, 'b8:27:eb:37:b9:4e', 111, 190, 134567, 14.78, 10.87, 4.56, 3.45, None, 1.23, 41, 1, 'Optimal', None, '2020-07-27 20:32:54', 'FM-004', 5),
                (2, 'b8:27:eb:37:b9:4e', 111, 190, 134567, 14.78, 10.87, 4.56, 3.45, None, 1.23, 41, 1,
                 'Optimal', None, '2020-07-27 20:32:54', 'FM-004', 5, 'acb430b7-ca5e-438f-b2e8-ac4030d2184b'),
                (3, 'b8:27:eb:37:b9:4e', 111, 190, 134567, 14.78, 10.87, 4.56, 3.45, None, 1.23, 41, 1,
                 'Optimal', None, '2020-07-27 20:32:54', 'FM-004', 5, 'db8e7c5e-70a1-4d70-828a-c50d5f99d954'),
                )
        url = reverse('flowmeter_logger')
        response = self.client.post(url, data=logs, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(models.FlowmeterLogs.objects.count(), 3)
        obj = models.FlowmeterLogs.objects.first()
        self.assertEqual(obj.flowmeter_serial_number, "Test")


class PowerMeterModuleTest(APITestCase):
    def setUp(self):
        company_data = {
            'Name': 'Test Company',
            'Country': 'Nigeria',
            'State': 'Lagos',
            'City': 'Ikeja',
            'Address': 'Plot E, Ikosi Road',
            'Company_type': 'Large',
            'Contact_person_name': 'Rahman Solanke',
            'Contact_person_designation': 'Tech Lead',
            'Contact_person_mail': 'rahman.s@e360africa.com',
            'Contact_person_phone': '08146646207'
        }
        self.company = models.Companies.objects.create(**company_data)
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
            'State': 'Lagos',
            'City': 'Ikeja',
            'Address': 'Plot E, Ikosi Road',
            'Site_type': 'Mining'
        }
        self.newsite = models.Sites.objects.create(**site_data)
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
        self.equip = models.Equipment.objects.create(**equipment)
        log = {
            'mac_address': 'b8:27:eb:54:d3:09',
            'powermeter_address': 1,
            'current_a': 0,
            'voltage_a': 23.64215279,
            'power_a': 0,
            'equipment': self.equip,
            'timestamp': '2021-02-19 9:21',
            'status': 0,
            'uid': 'db8e7c5e-70a1-4d70-828a-c50d5f99d954'
        }
        self.new_log = models.PowermeterLogs.objects.create(**log)

        new_powermeter = {
            'serial_number': 'PM1234',
            'site': self.newsite,
            'meter_type': 'DPP',
            'address': 1,
            'active': False,
            'created_at': datetime.now(),
            'equipment': self.equip
        }
        self.powermeter = models.PowerMeter.objects.create(**new_powermeter)

    def test_powermeter_logger(self):
        '''
        data in this  format
        id,mac_address,pm_address,equipment_id,Time_stamp,uuid,voltage_a,voltage_b,voltage_c,
        current_a,current_b,current_c,power_a,power_b,power_c,power_total,frequency,power_factor,active_energy, engine_running
        '''
        logs = ((1, "b8:27:eb:54:d3:09", 1, 1, "2021-02-19 9:21", "db8e7c5e-70a1-4d70-828a-c50d5f99d954", 23.64215279, 23.64215279, 23.64215279, 0, 89.27999878, 89.27999878, -18.55699921, -18.55699921, -18.55699921, 19.6060009, 52.72639847, -0.9285299778, 110455919, 0),
                (2, "b8:27:eb:54:d3:09", 1, 1, "2021-02-19 9:21", "db8e7c5e-70a1-4d70-828a-c50d5f99d954", 23.64215279, 23.64215279, 23.64215279,
                 89.27999878, 89.27999878, 89.27999878, -18.55699921, -18.55699921, -18.55699921, 19.6060009, 52.72639847, -0.9285299778, 110455919, 1),
                (3, "b8:27:eb:54:d3:09", 1, 1, "2021-02-19 9:21", "db8e7c5e-70a1-4d70-828a-c50d5f99d954", 23.64215279, 23.64215279, 23.64215279,
                 89.27999878, 89.27999878, 89.27999878, -18.55699921, -18.55699921, -18.55699921, 19.6060009, 52.72639847, -0.9285299778, 110455919, 0),
                (4, "b2:34:eb:54:d3:6", 3, 1, "2021-02-19 9:21", "db8e7c5e-70a1-4d70-828a-c50d5f99d954", 23.64215279, 23.64215279, 23.64215279,
                 89.27999878, 89.27999878, 89.27999878, 18.55699921, 18.55699921, -18.55699921, 19.6060009, 52.72639847, -0.9285299778, 110455919, 1),
                )
        url = reverse('powermeter_logger')
        response = self.client.post(url, data=logs, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(models.PowermeterLogs.objects.count(), 4)
        obj = models.PowermeterLogs.objects.first()
        self.assertEqual(obj.powermeter_address, 1)
        self.assertGreaterEqual(obj.power_a, 0)
        last_obj = models.PowermeterLogs.objects.last()
        self.assertEqual(last_obj.powermeter_address, 3)
        self.assertGreaterEqual(last_obj.power_a, 18.55699921)
        self.assertTrue(last_obj.mac_address == 'b2:34:eb:54:d3:6')

    def test_powermeter_transaction_log(self):
        url = reverse('powermeter_transaction_log')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_powermeter_update(self):
        data = {
            "id": self.powermeter.id,
            "serial_number": "PM1234",
            "meter_type": "DPP",
            "address": 111,
            "active": True,
            "created_at": datetime.now(),
            "site": self.newsite.Site_id,
            "equipment": self.equip.id
        }
        url = reverse('powermeter_update')
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_equipment_list(self):
        url = reverse('all_equipment_site_list')
        response = self.client.get(url, data={"site_id": self.newsite.Site_id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)

    def test_equipment_obj(self):
        url = reverse('equipment_obj')
        data = {
            "site_id": self.newsite.Site_id,
            "name": self.equip.name
        }
        response = self.client.get(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['id'], self.equip.id)
        self.assertEqual(response.data['data']['name'], self.equip.name)
        self.assertEqual(response.data['data']['site'], self.newsite.Site_id)

    def test_powermeters_by_company(self):
        url = reverse('powermeters_by_company')
        response = self.client.get(url, data={'id': self.company.Company_id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data'][0]
                         ['id'], self.company.Company_id)
        self.assertEqual(response.data['data'][0]
                         ['site']['Site_id'], self.newsite.Site_id)
        self.assertEqual(response.data['data'][0]
                         ['equipment'], self.equip.name)

    def test_all_powermeters(self):
        url = reverse('all_powermeters')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)

    def test_activate_deactivate_powermeters(self):
        url = reverse('activate_deactivate_powermeters', kwargs={
                      "powermeter_id": self.powermeter.id, "action": "activate"})
        self.assertEqual(self.powermeter.active, False)
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_powermeter_lastlog(self):
        url = reverse('powermeter_lastlog')
        response = self.client.post(
            url, data={"site_ids": [self.newsite.Site_id]})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_powermeter_trend(self):
        url = reverse('daily_power_trend')
        response = self.client.post(url, data={"site_ids": [
                                    self.newsite.Site_id], "start": "2021-02-12 12:01:01", "end": "2021-02-23 08:04:23"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 3)


class TransactionsCommentModelTest(APITestCase):
    def setUp(self):
        company_data = {
            'Name': 'Test Company',
            'Country': 'Nigeria',
            'State': 'Lagos',
            'City': 'Ikeja',
            'Address': 'Plot E, Ikosi Road',
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
            'State': 'Lagos',
            'City': 'Ikeja',
            'Address': 'Plot E, Ikosi Road',
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

    def test_create_transaction_comment_model(self):
        trx_time = "2020-11-02T14:03:02"
        models.FlowmeterTransactionComment.objects.create(
            equipment_id=1,
            trx_end_time=trx_time,
            comment_create_author="Solanke Abdulrahman",
            comment="Na comment una want? Oya take"
        )
        self.assertEqual(models.FlowmeterTransactionComment.objects.count(), 1)


class TransactionsCommentViewTest(APITestCase):
    def setUp(self):
        company_data = {
            'Name': 'Test Company',
            'Country': 'Nigeria',
            'State': 'Lagos',
            'City': 'Ikeja',
            'Address': 'Plot E, Ikosi Road',
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
            'State': 'Lagos',
            'City': 'Ikeja',
            'Address': 'Plot E, Ikosi Road',
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
        models.FlowmeterTransactionComment.objects.create(
            equipment_id=1,
            trx_end_time="2020-11-02T14:03:02",
            comment_create_author="Solanke Abdulrahman",
            comment="Na comment una want? Oya take"
        )
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

    def test_create_transaction_comment_view(self):
        url = reverse("new_transaction_comment")
        data = {
            'equipment': 1,
            'trx_end_time': "2020-11-02T12:45:08",
            'comment': "This is a new comment",
            'comment_create_author': "Abdulrahman"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_transaction_comment_view(self):
        url = reverse('transaction_comment_update', kwargs={'pk': 1})
        data = {
            'comment': "Na new comment be this",
            'comment_edit_author': "Kazeem ijaya"
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()["data"]
        self.assertEqual(response_data["comment"], "Na new comment be this")
        self.assertEqual(response_data["comment_edit_author"], "Kazeem ijaya")
