from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APITestCase

from .. import models


class VersionCreateTest(APITestCase):
    def setUp(self):
        get_user_model().objects.create_user(Email="rahman.s@e360africa.com")
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

    def test_register_new_version(self):
        url = reverse('version_list')
        data = {
            'Version_number': '1.0.0',
            'Download_link': 'https://api.smarteye.com.au/smarteye.zip',
            'Filename': 'smarteye'
        }
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(models.Version.objects.count(), 1)

    
class VersionRetrieveTests(APITestCase):
    def setUp(self):
        get_user_model().objects.create_user(Email="rahman.s@e360africa.com")
        data_1 = {
            'Version_number': '1.0.0',
            'Download_link': 'https://api.smarteye.com.au/smarteye1.zip',
            'Filename': 'smarteye1'
        }
        data_2 = {
            'Version_number': '1.1.0',
            'Download_link': 'https://api.smarteye.com.au/smarteye2.zip',
            'Filename': 'smarteye2'
        }
        data_3 = {
            'Version_number': '1.2.0',
            'Download_link': 'https://api.smarteye.com.au/smarteye3.zip',
            'Filename': 'smarteye3'
        }
        models.Version.objects.create(**data_1)
        models.Version.objects.create(**data_2)
        models.Version.objects.create(**data_3)
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

    def test_retrieve_versions(self):
        url = reverse('version_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 3)