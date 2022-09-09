from django.urls import reverse
from django.core.files import File
from django.contrib.auth import get_user_model
from django.conf import settings

from rest_framework import status
from rest_framework.test import APITestCase

from .. import models


class TankGroupModelTest(APITestCase):
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

    def test_can_create_tankgroup_model(self):
        data = {
          'Name': 'Tank group 1',
          'UOM': 'L',
          'Company_id': 1,
          'Product_id': 1
        }
        models.TankGroups.objects.create(**data)
        self.assertEqual(models.TankGroups.objects.count(), 1)


class TankGroupViewsTest(APITestCase):
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

    def test_can_create_tankgroup(self):
        url = reverse('tankgroup_list')
        data = {
          'Name': 'Tank group 1',
          'UOM': 'L',
          'Company': 1,
          'Product': 1
        }
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(models.TankGroups.objects.count(), 1)


class TankGroupRetrieveTests(APITestCase):
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
        product_data = {
            'Name': 'Petrol',
            'Code': 'PMS'
        }
        models.Products.objects.create(**product_data)
        models.Companies.objects.create(**company_data_1)
        models.Companies.objects.create(**company_data_2)
        data_1 = {
          'Name': 'Tank group 1',
          'UOM': 'L',
          'Company_id': 1,
          'Product_id': 1
        }
        data_2 = {
          'Name': 'Tank group 2',
          'UOM': 'L',
          'Company_id': 1,
          'Product_id': 1
        }
        data_3 = {
          'Name': 'Tank group 1',
          'UOM': 'L',
          'Company_id': 2,
          'Product_id': 1
        }
        data_4 = {
          'Name': 'Tank group 2',
          'UOM': 'L',
          'Company_id': 2,
          'Product_id': 1
        }
        models.TankGroups.objects.create(**data_1)
        models.TankGroups.objects.create(**data_2)
        models.TankGroups.objects.create(**data_3)
        models.TankGroups.objects.create(**data_4)
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

    def test_retrieve_all_tankgroups(self):
        url = reverse('all_tankgroup_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 4)

    def test_retrieve_non_E360_tankgroups(self):
        url = reverse('tankgroup_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 2)

    def test_retrieve_a_valid_tankgroup(self):
        url = reverse('tankgroup_detail', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_an_invalid_tankgroup(self):
        url = reverse('tankgroup_detail', kwargs={'pk': 20})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_tankgroups_in_a_company(self):
        url = reverse('tankgroup_by_company',kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 2)


class TankGroupUpdateTests(APITestCase):
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
        data_1 = {
          'Name': 'Tank group 1',
          'UOM': 'L',
          'Company_id': 1,
          'Product_id': 1
        }
        models.TankGroups.objects.create(**data_1)
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

    def test_partial_update_tankgroup(self):
        url = reverse('tankgroup_detail', kwargs={'pk':1})
        data = {
          'Name': 'New Tank Group',
          'Reorder_Level': 20000
        }
        response = self.client.put(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['data']['Name'], 'New Tank Group')
    
    def test_delete_tankgroup(self):
        url = reverse('tankgroup_detail', kwargs={'pk':1})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(models.TankGroups.objects.count(), 0)


class TankGroupFeatureTests(APITestCase):
    '''
    Test for the following features:
    - Get eligible tanks for a tankgroup
    - Map tanks to tankgroup
    - Get tanks mapped to a tankgroup
    '''
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
            'Number_of_tanks': 6,
            'Country': 'Nigeria',
            'State':'Lagos',
            'City': 'Ikeja',
            'Address':'Plot E, Ikosi Road',
            'Site_type': 'Mining'
        }
        models.Sites.objects.create(**data_1)
        product_data = {
            'Name': 'Petrol',
            'Code': 'PMS'
        }
        product_data_2 = {
            'Name': 'Diesel',
            'Code': 'AGO'
        }
        models.Products.objects.create(**product_data)
        models.Products.objects.create(**product_data_2)
        tank_1 = {
            'Name': 'Test Tank 1',
            'Controller_polling_address': 1,
            'Tank_index': 1,
            'Capacity': 10000,
            'Site_id': 1,
            'Product_id': 1
        }
        tank_2 = {
            'Name': 'Test Tank 2',
            'Controller_polling_address': 1,
            'Tank_index': 2,
            'Capacity': 15000,
            'Site_id': 1,
            'Product_id': 1
        }
        tank_3 = {
            'Name': 'Test Tank 3',
            'Controller_polling_address': 1,
            'Tank_index': 3,
            'Capacity': 8000,
            'Site_id': 1,
            'Product_id': 1
        }
        tank_4 = {
            'Name': 'Test Tank 4',
            'Controller_polling_address': 1,
            'Tank_index': 4,
            'Capacity': 10000,
            'Site_id': 1,
            'Product_id': 2
        }
        tank_5 = {
            'Name': 'Test Tank 5',
            'Controller_polling_address': 1,
            'Tank_index': 5,
            'Capacity': 15000,
            'Site_id': 1,
            'Product_id': 2
        }
        models.Tanks.objects.create(**tank_1)
        models.Tanks.objects.create(**tank_2)
        models.Tanks.objects.create(**tank_3)
        models.Tanks.objects.create(**tank_4)
        models.Tanks.objects.create(**tank_5)
        data_1 = {
          'Name': 'Tank group 1',
          'UOM': 'L',
          'Product_id': 1,
          'Company_id': 1
        }
        models.TankGroups.objects.create(**data_1)
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

    def test_get_eligible_tanks_for_a_tankgroup(self):
        url = reverse('tankgroup_eligible_tanks', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 3)

    def test_tank_to_tankgroups_mapping(self):
        url = reverse('tankgroup_map_tanks', kwargs={'pk': 1})
        data = {'Tank': [1,2,3]}
        response = self.client.put(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(models.TankGroups.objects.get(pk=1).tank_count, 3)
    
    def test_get_all_tanks_mapped_to_a_tankgroup(self):
        #Map tanks
        url = reverse('tankgroup_map_tanks', kwargs={'pk': 1})
        data = {'Tank': [1,2,3]}
        self.client.put(url, data=data, format='json')
        url = reverse('tankgroup_tanks', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']['Tanks']), 3)