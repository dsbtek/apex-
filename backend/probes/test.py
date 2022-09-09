import csv
import os
import shutil
from tempfile import NamedTemporaryFile, gettempdir

from django.urls import reverse
from django.core.files import File
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.conf import settings

from rest_framework import status
from rest_framework.test import APITestCase

from .. import models

def make_chart(filename):
    with open(filename, 'w') as chart:
        writer = csv.writer(chart, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['Current(mA)','Height(mm)'])
        writer.writerow(['4', '0'])
        writer.writerow(['20', '2000'])


class ProbeCreateTests(APITestCase):
    def setUp(self):
        data_1 = {
            'Email': "rahman.s@e360africa.com"
        }

        get_user_model().objects.create_user(**data_1)
        self.authenticator()

    @classmethod
    @override_settings(MEDIA_ROOT=gettempdir())
    def tearDownClass(cls):
        #remove probe_charts dir from tmp
        try:
            shutil.rmtree(os.path.join(settings.MEDIA_ROOT, 'probe_charts'))
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

    def test_can_create_probe(self):
        url = reverse('probe_list')
        data = {
            'name': 'Test Probe',
            'slug': 'PRB'
        }
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @override_settings(MEDIA_ROOT=gettempdir())
    def test_can_create_probe_with_chart(self):
        url = reverse('probe_list')
        f = NamedTemporaryFile()
        make_chart(f.name)
        chart_url = f.name
        with open(chart_url, 'rb') as chart:
            data = {
                'name': 'Test Probe',
                'slug': 'PRB',
                'probe_chart': chart
            }
            response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class ProbeRetrieveTests(APITestCase):

    @override_settings(MEDIA_ROOT=gettempdir())
    def setUp(self):
        f = NamedTemporaryFile()
        make_chart(f.name)
        chart = f.name

        data1 = {
            'name': 'Test Probe 1',
            'slug': 'PRB1'
        }
        data2 = {
            'name': 'Test Probe 2',
            'slug': 'PRB2'
        }
        data3 = {
            'name': 'Test Probe 3',
            'slug': 'PRB3'
        }

        get_user_model().objects.create_user(Email='rahman.s@e360africa.com')
        probe1 = models.Probes.objects.create(**data1)
        probe1.probe_chart.save('chart1.csv', File(open(chart, 'rb')))
        probe2 = models.Probes.objects.create(**data2)
        probe2.probe_chart.save('chart2.csv', File(open(chart, 'rb')))
        probe3 = models.Probes.objects.create(**data3)
        probe3.probe_chart.save('chart3.csv', File(open(chart, 'rb')))
        self.authenticator()

    @classmethod
    @override_settings(MEDIA_ROOT=gettempdir())
    def tearDownClass(cls):
        #remove probe_charts dir from tmp
        try:
            shutil.rmtree(os.path.join(settings.MEDIA_ROOT, 'probe_charts'))
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

    def test_get_all_probes(self):
        url = reverse('probe_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 3)

    def test_get_a_valid_probe(self):
        url = reverse('probe_details', kwargs={'pk': 1})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['data']['id'], 1)

    def test_retrieve_an_invalid_probe(self):
        url = reverse('probe_details', kwargs={'pk': 20})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ProbeUpdateDeleteTests(APITestCase):
    @override_settings(MEDIA_ROOT=gettempdir())
    def setUp(self):
        f = NamedTemporaryFile()
        make_chart(f.name)
        chart = f.name

        data1 = {
            'name': 'Test Probe 1',
            'slug': 'PRB1'
        }

        get_user_model().objects.create_user(Email='rahman.s@e360africa.com')
        probe1 = models.Probes.objects.create(**data1)
        probe1.probe_chart.save('chart1.csv', File(open(chart, 'rb')))
        self.authenticator()

    @classmethod
    @override_settings(MEDIA_ROOT=gettempdir())
    def tearDownClass(cls):
        #remove probe_charts dir from tmp
        try:
            shutil.rmtree(os.path.join(settings.MEDIA_ROOT, 'probe_charts'))
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

    @override_settings(MEDIA_ROOT=gettempdir())
    def test_partial_update_for_probe(self):
        url = reverse('probe_details', kwargs={'pk': 1})
        f = NamedTemporaryFile()
        make_chart(f.name)
        chart_url = f.name
        with open(chart_url, 'rb') as chart:
            data = {
                'name': 'Test Probe',
                'probe_chart': chart
            }
            response = self.client.put(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['data']['name'], 'Test Probe')

    def test_delete_probe(self):
        url = reverse('probe_details', kwargs={'pk': 1})
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(models.Probes.objects.count(), 0)
    
    @override_settings(MEDIA_ROOT=gettempdir())
    def test_retrieve_probe_chart(self):
        #first create a probe
        url = reverse('probe_list')
        f = NamedTemporaryFile()
        make_chart(f.name)
        chart_url = f.name
        with open(chart_url, 'rb') as chart:
            data = {
                'name': 'Test Probe',
                'slug': 'PRB',
                'probe_chart': chart
            }
            self.client.post(url, data, format='multipart')
        url = reverse('read_probe_chart', kwargs={'pk': 2})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
