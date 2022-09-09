from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APITestCase

from .. import models


class SiteCreateTests(APITestCase):
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
        device_data = {
            'Name': 'Test Device 1',
            'Device_unique_address': 'b8:27:eb:97:8c:12',
            'Company_id': 1,
            'Active': True
        }
        models.Devices.objects.create(**device_data)
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

    def test_can_create_site(self):
        url = reverse('site_list')
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
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

class SiteRetrieveTests(APITestCase):
    def setUp(self):
        user = {
            'Email': "rahman.s@e360africa.com"
        }
        get_user_model().objects.create_user(**user)

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
            'Name': 'Test Company_2',
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

    def test_can_retrieve_all_sites(self):
        url = reverse('all_site_list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 3)

    def test_can_retrieve_nonE360_owned_sites(self):
        url = reverse('site_list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 2)

    def test_retrieve_a_valid_site(self):
        url = reverse('site_detail', kwargs={'pk': 1})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['data']['Site_id'], 1)
    
    def test_retrieve_an_invalid_site(self):
        url = reverse('site_detail', kwargs={'pk': 20})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

class SiteFeatureTests(APITestCase):
    def setUp(self):
        user = {
            'Email': "rahman.s@e360africa.com"
        }
        get_user_model().objects.create_user(**user)

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
            'Name': 'Test Company_2',
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

    # def test_can_not_create_site_with_another_company_device(self):
    #     url = reverse('site_list')
    #     data = {
    #         'Name': 'Test Site',
    #         'Company_id': 1,
    #         'Device_id': 3,
    #         'Number_of_tanks': 3,
    #         'Country': 'Nigeria',
    #         'State':'Lagos',
    #         'City': 'Ikeja',
    #         'Address':'Plot E, Ikosi Road',
    #         'Site_type': 'Mining'
    #     }
    #     response = self.client.post(url, data, format='json')
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    # def test_can_not_create_site_with_unavailable_device(self):
    #     url = reverse('site_list')
    #     data = {
    #         'Name': 'Test Site',
    #         'Company_id': 1,
    #         'Device_id': 1,
    #         'Number_of_tanks': 3,
    #         'Country': 'Nigeria',
    #         'State':'Lagos',
    #         'City': 'Ikeja',
    #         'Address':'Plot E, Ikosi Road',
    #         'Site_type': 'Mining'
    #     }
    #     self.client.post(url, data, format='json')
    #     #A site has been created with Device of id 1.
    #     #Now, that device is unavailable
    #     self.assertFalse(models.Devices.objects.get(pk=1).available)
    #     #ANy attempt to create another site with that device should throw a 400 error
    #     data = {
    #         'Name': 'New Test Site',
    #         'Company_id': 1,
    #         'Device_id': 1,
    #         'Number_of_tanks': 3,
    #         'Country': 'Nigeria',
    #         'State':'Lagos',
    #         'City': 'Ikeja',
    #         'Address':'Plot E, Ikosi Road',
    #         'Site_type': 'Mining'
    #     }
    #     response = self.client.post(url, data, format='json')
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class SiteUpdateTests(APITestCase):
    def setUp(self):
        user = {
            'Email': "rahman.s@e360africa.com"
        }
        get_user_model().objects.create_user(**user)

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
        models.Sites.objects.create(**data_1)
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
    
    def test_partial_update_for_site(self):
        url = reverse('site_detail', kwargs={'pk': 1})
        data = {
            'Name': 'New Site',
            'Device_id': 2,
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['data']['Name'], 'New Site')
        #The device was changed
        #Check that the device change was successful
        self.assertEqual(models.Sites.objects.get(pk=1).Device.pk, 2)
        self.assertEqual(models.Sites.objects.get(pk=1).Device.get_site.Name, 'New Site')
        #Check that old device is now available
        self.assertTrue(models.Devices.objects.get(pk=1).available)
        #Check that new device is not available
        self.assertFalse(models.Devices.objects.get(pk=2).available)

    def test_delete_site(self):
        url = reverse('site_detail', kwargs={'pk': 1})
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(models.Sites.objects.count(), 0)


class SiteActivationTests(APITestCase):
    def setUp(self):
        user = {
            'Email': "rahman.s@e360africa.com"
        }
        get_user_model().objects.create_user(**user)
        user_1 = get_user_model().objects.create_user(Email='rahman.sol@gmail.com')
        user_2 = get_user_model().objects.create_user(Email='rahman.sola@gmail.com')
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
        site = models.Sites.objects.create(**data_1)
        user_1.Sites.add(site)
        user_1.save()
        user_2.Sites.add(site)
        user_2.save()
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

    def test_deactivate_site(self):
        url = reverse('site_activation', kwargs={'pk':1})
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        site = models.Sites.objects.get(pk=1)
        self.assertFalse(site.Active)
        #get users in the company
        users = site.users.all()
        for user in users:
            self.assertFalse(user.is_active)

    def test_activate_site(self):
        #first deactivate
        url = reverse('site_activation', kwargs={'pk':1})
        self.client.post(url, format='json')
        #activate back
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        site = models.Sites.objects.get(pk=1)
        self.assertTrue(site.Active)
        #get users in the company
        users = site.users.all()
        for user in users:
            self.assertTrue(user.is_active)