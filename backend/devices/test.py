from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APITestCase

from .. import models


class DeviceCreateTests(APITestCase):
    def setUp(self):
        data_1 = {
            'Email': "rahman.s@e360africa.com"
        }
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
        get_user_model().objects.create_user(**data_1)
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

    def test_can_register_device(self):
        url = reverse('device_list')
        data = {
            'Name': 'Test Device',
            'Device_unique_address': 'TEST',
            'Company_id':1
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

class DeviceRetrieveTests(APITestCase):
    def setUp(self):
        user = {
            'Email': "rahman.s@e360africa.com"
        }
        get_user_model().objects.create_user(**user)

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
        company = models.Companies.objects.create(**company_data)

        data_1 = {
            'Name': 'Test Device 1',
            'Device_unique_address': 'TEST01',
            'Company':company,
            'Active': True
        }

        data_2 = {
            'Name': 'Test Device 2',
            'Device_unique_address': 'TEST02',
            'Company':company,
            'Active': True
        }

        data_3 = {
            'Name': 'Test Device 3',
            'Device_unique_address': 'TEST03',
            'Company':None
        }
        models.Devices.objects.create(**data_1)
        models.Devices.objects.create(**data_2)
        models.Devices.objects.create(**data_3)
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

    def test_can_retrieve_all_devices(self):
        url = reverse('all_device_list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 3)

    def test_retrieve_a_valid_device(self):
        url = reverse('device_detail', kwargs={'pk': 1})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['data']['Device_id'], 1)
    
    def test_retrieve_an_invalid_device(self):
        url = reverse('device_detail', kwargs={'pk': 20})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_device_by_company(self):
        url = reverse('device_by_company', kwargs={'pk': 1})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 2)

    def test_retrieve_available_device_by_company(self):
        url = reverse('device_by_company', kwargs={'pk': 1})+'?available=1'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 2)

class DeviceUpdateTests(APITestCase):
    def setUp(self):
        user = {
            'Email': "rahman.s@e360africa.com"
        }
        get_user_model().objects.create_user(**user)

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
        company = models.Companies.objects.create(**company_data)

        data_1 = {
            'Name': 'Test Device 1',
            'Device_unique_address': 'TEST01',
            'Company':company,
            'Active': True
        }
        models.Devices.objects.create(**data_1)
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
    
    def test_partial_update_for_device(self):
        url = reverse('device_detail', kwargs={'pk': 1})
        data = {
            'Name': 'Test Device Updated'
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['data']['Name'], 'Test Device Updated')

    def test_delete_device(self):
        url = reverse('device_detail', kwargs={'pk': 1})
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(models.Devices.objects.count(), 0)


class DeviceRelationshipTests(APITestCase):
    def setUp(self):
        user = {
            'Email': "rahman.s@e360africa.com"
        }
        get_user_model().objects.create_user(**user)

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
        company = models.Companies.objects.create(**company_data)

        data_1 = {
            'Name': 'Test Device 1',
            'Device_unique_address': 'TEST01',
            'Company':company,
            'Active': True
        }
        models.Devices.objects.create(**data_1)
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

    def test_company_delete_sets_null_on_device(self):
        #initially, device has company
        device = models.Devices.objects.get(pk=1)
        self.assertIsNotNone(device.Company)
        #delete company
        url = reverse('company_detail', kwargs={'pk': 1})
        self.client.delete(url, format='json')
        #now, device has null company
        device = models.Devices.objects.get(pk=1)
        self.assertIsNone(device.Company)

class DeviceActivation(APITestCase):
    def setUp(self):
        user = {
            'Email': "rahman.s@e360africa.com"
        }
        get_user_model().objects.create_user(**user)

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
        company = models.Companies.objects.create(**company_data)

        data_1 = {
            'Name': 'Test Device 1',
            'Device_unique_address': 'TEST01',
            'Company':company,
            'Active': True
        }
        models.Devices.objects.create(**data_1)
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

    def test_deactivate_device(self):
        url = reverse('device_activation', kwargs={'pk':1, 'id':1})
        data = {
            'action':'deactivate'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        device = models.Devices.objects.get(pk=1)
        self.assertFalse(device.Active)

    def test_activate_company(self):
        #first deactivate
        url = reverse('device_activation', kwargs={'pk':1, 'id':1})
        self.client.post(url, {'action':'deactivate'}, format='json')
        #activate back
        response = self.client.post(url, {'action':'activate'},format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        device = models.Devices.objects.get(pk=1)
        self.assertTrue(device.Active)