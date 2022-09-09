from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APITestCase

from .. import models


class UserModelTests(APITestCase):
    def setUp(self):
        data_1 = {
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
        models.Companies.objects.create(**data_1)

    def test_company_create_model(self):
        user_data = {
            'Name': 'Solanke Abdulrahman',
            'Email': 'rahman.s@e360africa.com',
            'Company_id': 1
        }
        get_user_model().objects.create_user(**user_data)
        self.assertEqual(get_user_model().objects.count(), 1)
        user = get_user_model().objects.get(pk=1)
        self.assertEqual(user.Email, 'rahman.s@e360africa.com')
        self.assertTrue(user.is_active)
        self.assertIsNone(user.last_login)
        self.assertTrue(user.check_password('password'))


class UserCreateViewTests(APITestCase):
    def setUp(self):
        data_1 = {
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
        models.Companies.objects.create(**data_1)
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
        models.Devices.objects.create(**device_data_1)
        models.Devices.objects.create(**device_data_2)
        data_1 = {
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
        models.Sites.objects.create(**data_1)
        models.Sites.objects.create(**data_2)
        user_data = {
            'Name': 'Solanke Abdulrahman',
            'Email': 'rahman.s@e360africa.com',
            'Company_id': 1,
        }
        models.Role.objects.create(Name="Super-Admin")
        get_user_model().objects.create_user(**user_data)
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

    def test_can_create_user(self):
        url = reverse('user_list')
        user_data = {
            'Name': 'Solanke Abdulrahman',
            'Email': 'rahman.sol@e360africa.com',
            'Company_id': 1,
            'Site_id': [1, 2],
            'Role_id': 1,
            'Phone_number': '08146646207'
        }
        response = self.client.post(url, data=user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class UserRetrieveTests(APITestCase):
    def setUp(self):
        data_1 = {
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
        data_2 = {
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
        models.Companies.objects.create(**data_1)
        models.Companies.objects.create(**data_2)
        user_data_1 = {
            'Name': 'Solanke Abdulrahman',
            'Email': 'rahman.s@e360africa.com',
            'Company_id': 1
        }
        user_data_2 = {
            'Name': 'Solanke Abdulraheen',
            'Email': 'raheem.s@e360africa.com',
            'Company_id': 1
        }
        user_data_3 = {
            'Name': 'Ojo Seyi',
            'Email': 'ojo.s@e360africa.com',
            'Company_id': 2
        }
        user_data_4 = {
            'Name': 'Ojo Seyinr',
            'Email': 'ojort.s@e360africa.com',
            'Company_id': 2
        }
        get_user_model().objects.create_user(**user_data_1)
        get_user_model().objects.create_user(**user_data_2)
        get_user_model().objects.create_user(**user_data_3)
        get_user_model().objects.create_user(**user_data_4)
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

    def test_retrieve_all_users(self):
        url = reverse('all_user_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 4)

    def test_retrieve_non_E360_users(self):
        url = reverse('user_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 2)

    def test_retrieve_a_valid_user(self):
        url = reverse('user_detail', kwargs={'pk': 1})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['data']['id'], 1)

    def test_retrieve_an_invalid_user(self):
        url = reverse('user_detail', kwargs={'pk': 20})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_get_users_by_company(self):
        url = reverse('user_by_company', kwargs={'pk':1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 2)


class UserUpdateTests(APITestCase):
    def setUp(self):
        data_1 = {
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
        models.Companies.objects.create(**data_1)
        user_data_1 = {
            'Name': 'Solanke Abdulrahman',
            'Email': 'rahman.s@e360africa.com',
            'Company_id': 1
        }

        user_data_2 = {
            'Name': 'Yusuf Ridwan',
            'Email': 'ridwan.yusuf@smartflowtech.com',
            'Company_id': 1
        }
        get_user_model().objects.create_user(**user_data_1)
        get_user_model().objects.create_user(**user_data_2)
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

    def test_partial_update_for_user(self):
        url = reverse('user_detail', kwargs={'pk': 1})
        data = {
            'Name': 'New Name'
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['data']['Name'], 'New Name')

    def test_delete_user(self):
        url = reverse('user_detail', kwargs={'pk': 2})
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(get_user_model().objects.count(), 1)


class UserActivationTests(APITestCase):
    def setUp(self):
        data_1 = {
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
        models.Companies.objects.create(**data_1)
        user_data_1 = {
            'Name': 'Solanke Abdulrahman',
            'Email': 'rahman.s@e360africa.com',
            'Company_id': 1
        }
        user_data_2 = {
            'Name': 'Solanke Abdulrahman',
            'Email': 'rahman.sol@e360africa.com',
            'Company_id': 1
        }
        get_user_model().objects.create_user(**user_data_1)
        get_user_model().objects.create_user(**user_data_2)
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
    
    def test_deactivate_user(self):
        url = reverse('user_activation', kwargs={'pk':1})
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user = get_user_model().objects.get(pk=1)
        self.assertFalse(user.is_active)
    
    def test_activate_user(self):
        #first deactivate
        url = reverse('user_activation', kwargs={'pk':2})
        self.client.post(url, format='json')

        #activate
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user = get_user_model().objects.get(pk=1)
        self.assertTrue(user.is_active)