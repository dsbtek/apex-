from tempfile import NamedTemporaryFile, gettempdir
import shutil
import os
from PIL import Image

from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.core.files import File
from django.conf import settings

from rest_framework import status
from rest_framework.test import APITestCase

from .. import models


class CompanyCreateTests(APITestCase):
    def setUp(self):
        data_1 = {
            'Email': "rahman.s@e360africa.com"
        }

        get_user_model().objects.create_user(**data_1)
        self.authenticator()

    @classmethod
    @override_settings(MEDIA_ROOT=gettempdir())
    def tearDownClass(cls):
        #remove calibration_charts dir from tmp
        try:
            shutil.rmtree(os.path.join(settings.MEDIA_ROOT, 'company_avatars'))
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

    def test_can_create_company(self):
        url = reverse('company_list')
        data = {
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
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    @override_settings(MEDIA_ROOT=gettempdir())
    def test_can_create_company_with_avatar(self):
        url = reverse('company_list')
        f = NamedTemporaryFile()
        f.name += '.png'
        image_1 = Image.new('RGBA', (200, 200), 'white')
        image_1.save(f.name)
        image_1_file = open(f.name, 'rb')

        data = {
            'Name': 'Test Company',
            'Country': 'Nigeria',
            'State':'Lagos',
            'City': 'Ikeja',
            'Address':'Plot E, Ikosi Road',
            'Company_type': 'Large',
            'Contact_person_name': 'Rahman Solanke',
            'Contact_person_designation': 'Tech Lead',
            'Contact_person_mail': 'rahman.s@e360africa.com',
            'Contact_person_phone': '08146646207',
            'Company_image': image_1_file
        }
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class CompanyRetrieveTests(APITestCase):
    def setUp(self):
        user = {
            'Email': "rahman.s@e360africa.com"
        }
        
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
            'Contact_person_phone': '08146646207'
        }

        data_3 = {
            'Name': 'Test Company 3',
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


        get_user_model().objects.create_user(**user)
        models.Companies.objects.create(**data_1)
        models.Companies.objects.create(**data_2)
        models.Companies.objects.create(**data_3)
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

    def test_can_retrieve_all_companies(self):
        url = reverse('all_company_list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 3)

    def test_can_retrieve_nonE360_owned_companies(self):
        url = reverse('company_list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 2)

    def test_retrieve_a_valid_company(self):
        url = reverse('company_detail', kwargs={'pk': 1})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['data']['Company_id'], 1)
    
    def test_retrieve_an_invalid_company(self):
        url = reverse('company_detail', kwargs={'pk': 20})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class CompanyUpdateTests(APITestCase):
    def setUp(self):
        user = {
            'Email': "rahman.s@e360africa.com"
        }
        
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

        get_user_model().objects.create_user(**user)
        models.Companies.objects.create(**data_1)
        self.authenticator()

    @classmethod
    @override_settings(MEDIA_ROOT=gettempdir())
    def tearDownClass(cls):
        #remove calibration_charts dir from tmp
        try:
            shutil.rmtree(os.path.join(settings.MEDIA_ROOT, 'company_avatars'))
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
    
    def test_partial_update_for_company(self):
        url = reverse('company_detail', kwargs={'pk': 1})
        data = {
            'Name': 'Test Company Updated'
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['data']['Name'], 'Test Company Updated')

    @override_settings(MEDIA_ROOT=gettempdir())
    def test_update_for_company_with_logo(self):
        url = reverse('company_detail', kwargs={'pk': 1})
        f = NamedTemporaryFile()
        f.name += '.png'
        image_1 = Image.new('RGBA', (200, 200), 'white')
        image_1.save(f.name)
        image_1_file = open(f.name, 'rb')
        data = {
            'Company_image': image_1_file
        }
        response = self.client.put(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_company(self):
        url = reverse('company_detail', kwargs={'pk': 1})
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(models.Companies.objects.count(), 0)

class CompanyActivation(APITestCase):
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
        company = models.Companies.objects.create(**data_1)
        
        user = {
            'Email': "rahman.s@e360africa.com"
        }

        user_1 = {
            'Email': "rahman.sho@e360africa.com",
            'Company': company
        }
        
        user_2 = {
            'Email': "rahman.sol@e360africa.com",
            'Company': company
        }
        get_user_model().objects.create_user(**user)
        get_user_model().objects.create_user(**user_1)
        get_user_model().objects.create_user(**user_2)
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

    def test_deactivate_company(self):
        url = reverse('company_activation', kwargs={'pk':1})
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        company = models.Companies.objects.get(pk=1)
        self.assertFalse(company.Active)
        #get users in the company
        users = company.users.all()
        for user in users:
            self.assertFalse(user.is_active)

    def test_activate_company(self):
        #first deactivate
        url = reverse('company_activation', kwargs={'pk':1})
        self.client.post(url, format='json')
        #activate back
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        company = models.Companies.objects.get(pk=1)
        self.assertTrue(company.Active)
        #get users in the company
        users = company.users.all()
        for user in users:
            self.assertTrue(user.is_active)