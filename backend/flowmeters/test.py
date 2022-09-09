from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APITestCase

from .. import models


class FlowmeterModelTest(APITestCase):
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
            'Number_of_tanks': 3,
            'Country': 'Nigeria',
            'State':'Lagos',
            'City': 'Ikeja',
            'Address':'Plot E, Ikosi Road',
            'Site_type': 'Mining'
        }
        models.Sites.objects.create(**data)

    def test_can_create_flowmeter_model(self):
        data = {
            'serial_number': 'FM-001',
            'max_temp': 100.00,
            'address': 111,
            'site_id': 1
        }
        flowmeter = models.Flowmeter.objects.create(**data)
        self.assertEqual(models.Flowmeter.objects.count(), 1)


class FlowmeterCreateViewTests(APITestCase):
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
            'Number_of_tanks': 3,
            'Country': 'Nigeria',
            'State':'Lagos',
            'City': 'Ikeja',
            'Address':'Plot E, Ikosi Road',
            'Site_type': 'Mining'
        }
        models.Sites.objects.create(**data)
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

    def test_create_flowmeter(self):
        url = reverse('flowmeter_list')
        data = {
            'serial_number': 'FM-001',
            'max_temp': 100.00,
            'address': 111,
            'site_id': None,
            'meter_type': 'DFM'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class FlowmeterRetrieveViewTests(APITestCase):
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
            'Number_of_tanks': 3,
            'Country': 'Nigeria',
            'State':'Lagos',
            'City': 'Ikeja',
            'Address':'Plot E, Ikosi Road',
            'Site_type': 'Mining'
        }
        models.Sites.objects.create(**data)
        get_user_model().objects.create_user(Email='rahman.s@e360africa.com')
        fm_1 = {
            'serial_number': 'FM-001',
            'max_temp': 100.00,
            'address': 111,
            'site_id': 1
        }
        fm_2 = {
            'serial_number': 'FM-002',
            'max_temp': 100.00,
            'address': 111,
            'site_id': 1
        }
        fm_3 = {
            'serial_number': 'FM-003',
            'max_temp': 100.00,
            'address': 111,
            'site_id': 1
        }
        models.Flowmeter.objects.create(**fm_1)
        models.Flowmeter.objects.create(**fm_2)
        models.Flowmeter.objects.create(**fm_3)
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

    def test_can_retrieve_all_flowmeters(self):
        url = reverse('flowmeter_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 3)
    
    def test_retrieve_a_valid_Equipment(self):
        url = reverse('flowmeter_detail', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['data']['id'], 1)

    def test_retrieve_an_invalid_Equipment(self):
        url = reverse('flowmeter_detail', kwargs={'pk': 20})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class FlowmeterUpdateViewTests(APITestCase):
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
            'Number_of_tanks': 3,
            'Country': 'Nigeria',
            'State':'Lagos',
            'City': 'Ikeja',
            'Address':'Plot E, Ikosi Road',
            'Site_type': 'Mining'
        }
        models.Sites.objects.create(**data)
        get_user_model().objects.create_user(Email='rahman.s@e360africa.com')
        fm_1 = {
            'serial_number': 'FM-001',
            'max_temp': 100.00,
            'address': 111
        }
        models.Flowmeter.objects.create(**fm_1)
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

    def test_partial_update_flowmeter(self):
        url = reverse('flowmeter_detail', kwargs={'pk':1})
        data = {
            'max_temp': 120.00
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['data']['max_temp'], 120.00)

    def test_delete_flowmeter(self):
        url = reverse('flowmeter_detail', kwargs={'pk':1})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(models.Flowmeter.objects.count(), 0)


class FlowmeterActivation(APITestCase):
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
            'Number_of_tanks': 3,
            'Country': 'Nigeria',
            'State':'Lagos',
            'City': 'Ikeja',
            'Address':'Plot E, Ikosi Road',
            'Site_type': 'Mining'
        }
        models.Sites.objects.create(**data)
        get_user_model().objects.create_user(Email='rahman.s@e360africa.com')
        fm_1 = {
            'serial_number': 'FM-001',
            'max_temp': 100.00,
            'address': 111,
            'site_id': 1
        }
        models.Flowmeter.objects.create(**fm_1)
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

    def test_deactivate_flowmeter(self):
        url = reverse('flowmeter_activation', kwargs={'pk':1, 'id':1})
        data = {
            'action':'deactivate'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        flowmeter = models.Flowmeter.objects.get(pk=1)
        self.assertFalse(flowmeter.active)

    def test_activate_flowmeter(self):
        #first deactivate
        url = reverse('flowmeter_activation', kwargs={'pk':1, 'id':1})
        self.client.post(url, {'action':'deactivate'}, format='json')
        #activate back
        response = self.client.post(url, {'action':'activate'},format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        flowmeter = models.Flowmeter.objects.get(pk=1)
        self.assertTrue(flowmeter.active)


class FlowmeterFeatureTests(APITestCase):
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
            'Number_of_tanks': 3,
            'Country': 'Nigeria',
            'State':'Lagos',
            'City': 'Ikeja',
            'Address':'Plot E, Ikosi Road',
            'Site_type': 'Mining'
        }
        models.Sites.objects.create(**data)
        get_user_model().objects.create_user(Email='rahman.s@e360africa.com')
        fm_1 = {
            'serial_number': 'FM-001',
            'max_temp': 100.00,
            'address': 111,
            'site_id': 1,
            'active': True
        }
        fm_2 = {
            'serial_number': 'FM-002',
            'max_temp': 100.00,
            'address': 112,
            'site_id': 1,
            'active': True
        }
        models.Flowmeter.objects.create(**fm_1)
        models.Flowmeter.objects.create(**fm_2)
        product_data = {
            'Name': 'Petrol',
            'Code': 'PMS'
        }
        models.Products.objects.create(**product_data)
        eqp = {
            'name': 'Test Equipment',
            'product_id': 1,
            'oem': 'CAT',
            'model': 'R-100',
            'oem_consumption_rate': 30.45,
            'running_hours_source': 'FM',
            'litres_consumed_source': 'TL',
            'flowmeter_id': 1,
            'address': None,
            'model': 'Yamaha',
            'initial_totaliser_hours': 20,
            'site_id': 1,
        }
        models.Equipment.objects.create(**eqp)
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

    def test_flowmeter_unique_validator(self):
        url = reverse('flowmeter_list')
        data = {
            'serial_number': 'FM-003',
            'max_temp': 100.00,
            'address': 113,
            'site_id': 1,
            'meter_type': 'DFM'
        }
        self.client.post(url, data=data, format='json')
        #Should not be able to create anothe FM with same address within same site
        data = {
            'serial_number': 'FM-004',
            'max_temp': 104.00,
            'address': 113,
            'site_id': 1,
            'meter_type': 'DFM'
        }
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_flowmeter_availability_status(self):
        fm1 = models.Flowmeter.objects.get(pk=1)
        #fm1 should be unavailable since an equipment has connected to it
        self.assertFalse(fm1.available)
        fm2 = models.Flowmeter.objects.get(pk=2)
        self.assertTrue(fm2.available)

    def test_retrieve_flowmeters_by_site(self):
        url = reverse('flowmeter_by_site', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 2)

    def test_retrieve_available_flowmeters_by_site(self):
        url = reverse('flowmeter_by_site', kwargs={'pk': 1})+'?available=1'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 1)

    def test_retrieve_flowmeters_by_company(self):
        url = reverse('flowmeter_by_company', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 2)