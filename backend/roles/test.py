from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APITestCase

from .. import models

class RoleViewTests(APITestCase):
    def setUp(self):
        get_user_model().objects.create_user(Email='rahman.s@e360africa.com')
        models.Role.objects.create(Name="View-only")
        models.Role.objects.create(Name="Company-admin")
        models.Role.objects.create(Name="Super-admin")
        models.Role.objects.create(Name="E360-Admin")
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

    def test_get_all_user_roles(self):
        url = reverse('user_role_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 2)

    def test_get_all_roles(self):
        url = reverse('all_role_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 4)