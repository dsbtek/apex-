from rest_framework.test import APITestCase, APIClient
from rest_framework import status
import json
from django.urls import reverse, resolve
from django.contrib.auth import get_user_model
from . import views
from .. import models
from rest_framework.test import APIRequestFactory
from datetime import datetime
#test copy media file

class PumpCreateTests(APITestCase):
    def setUp(self):
        user = {
            'Email': 'alabarise@gmail.com',
        }

        get_user_model().objects.create_user(**user)

        company_data = {
            "Name": "Test Company 1",
            "Country": "Nigera",
            "State": "Lagos",
            "City": "Ikeja",
            "Address": "1, Ayo way.",
            "Company_type": "Multinational",
            "Contact_person_name": "Ridwan Alaba",
            "Contact_person_designation": "Software Engineer",
            "Contact_person_mail": "ridwan.yusuf@smartflowtech",
            "Contact_person_phone": "08011002200"
        }

        company = models.Companies.objects.create(**company_data)

        device_data = {

            "Name": "DUTCHESS HOSPITAL LTD",
            "Device_unique_address": "aa:27:eb:4c:fd:124",
            "Company": company,
            "Phone_number": "08033717850",
            "transmit_interval": 150,
            "Active": True,
        }

        models.Devices.objects.create(**device_data)

        pump_brand_data = {
            "Name": 'sample pump brand',
            "OEM": "0em Manufacurer 1"
        }

        models.PumpBrand.objects.create(**pump_brand_data)

        site_data = {
            "Name": "First Test Site",
            "Company_id": 1,
            "Country": "Nigeria",
            "State": "lagos",
            "City": "Ikeja",
            "Address": 'Ikosi road',
            "Site_type": "Aviation",
            "Number_of_tanks": 3

        }

        models.Sites.objects.create(**site_data)

        product_1_data = {
            "Name": "Sample Product",
            "Code": "R2006"
        }

        product_2_data = {
            "Name": "Sample Product",
            "Code": "R2006"
        }

        models.Products.objects.create(**product_1_data)
        models.Products.objects.create(**product_2_data)

        self.authenticator()

    def authenticator(self):
        url = reverse('login')
        data = {
            'Email': 'alabarise@gmail.com',
            'password': 'password'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = response.json()['data']['token']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)

    def test_create_pump(self):
        url = reverse('pumps')
        data = {

            "Device": 1,
            "Site": 1,
            "Pumpbrand": 1,
            "Name": "Test Pump 1",
            "Pump_protocol": "RS485",
            "Nozzle_count": 2,
            "Note": "just a note",
            'Nozzles': [
                {
                    "Name": "Test Nozzle 1",
                    "Nozzle_address": 1,
                    "Decimal_setting_price_unit": 0,
                    "Decimal_setting_amount": 1,
                    "Decimal_setting_volume": 1,
                    "Totalizer_at_installation": 2000,
                    "Display_unit": "L",
                    "Nominal_flow_rate": 1,
                    "Product": 2,
                    "First_initial_price": 165.00


                },
                {
                    "Name": "Test Nozzle 2",
                    "Nozzle_address": 1,
                    "Decimal_setting_price_unit": 0,
                    "Decimal_setting_amount": 1,
                    "Decimal_setting_volume": 1,
                    "Totalizer_at_installation": 2000,
                    "Display_unit": "L",
                    "Nominal_flow_rate": 1,
                    "Product": 1,
                    "First_initial_price": 160.00

                }
            ],

        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(models.Pump.objects.count(),  1)
        self.assertEqual(models.Nozzle.objects.count(), 2)


class PumpUpdateTests(APITestCase):
    def setUp(self):
        user = {
            'Email': 'alabarise@gmail.com',
            'password': 'password'
        }
        get_user_model().objects.create_user(**user)
        self.assertEqual(get_user_model().objects.count(), 1)

        company_data = {
            "Name": "Test Company 1",
            "Country": "Nigera",
            "State": "Lagos",
            "City": "Ikeja",
            "Address": "1, Ayo way.",
            "Company_type": "Multinational",
            "Contact_person_name": "Ridwan Alaba",
            "Contact_person_designation": "Software Engineer",
            "Contact_person_mail": "ridwan.yusuf@smartflowtech",
            "Contact_person_phone": "08011002200"
        }

        models.Companies.objects.create(**company_data)

        device_data = {

            "Name": "DUTCHESS HOSPITAL LTD",
            "Device_unique_address": "aa:27:eb:4c:fd:124",
            "Company_id": 1,
            "Phone_number": "08033717850",
            "transmit_interval": 150,
            "Active": True,

        }

        models.Devices.objects.create(**device_data)

        site_data = {
            "Name": "First Test Site",
            "Company_id": 1,
            "Country": "Nigeria",
            "State": "lagos",
            "City": "Ikeja",
            "Address": 'Ikosi road',
            "Site_type": "Aviation",
            "Number_of_tanks": 3

        }

        models.Sites.objects.create(**site_data)

        product_1_data = {
            "Name": "PMS",
            "Code": "1001"
        }

        product_2_data = {
            "Name": "AGO",
            "Code": "1002"
        }

        product_3_data = {
            "Name": "KERO",
            "Code": "1001"
        }

        models.Products.objects.create(**product_1_data)
        models.Products.objects.create(**product_2_data)
        models.Products.objects.create(**product_3_data)

        pump_brand_data = {
            "Name": 'sample test brand',
            "OEM": "0em 1"
        }

        models.PumpBrand.objects.create(**pump_brand_data)

        pump_data = {
            "Name": "First Pump Name",
            "Pump_protocol": "RS485",
            "Nozzle_count": 2,
            "Note": "First Pump short note",
            "Device_id": 1,
            "Site_id": 1,
            "Pumpbrand_id": 1,


        }

        models.Pump.objects.create(**pump_data)

        nozzle_data_1 = {
            "Name": "sample nozzle 1",
            "Nozzle_address": 1,
            "Product_id": 1,
            "Pump_id": 1,
            "Decimal_setting_price_unit": 1,
            "Decimal_setting_amount": 2,
            "Decimal_setting_volume": 2,
            "Totalizer_at_installation": 120000,
            "Nominal_flow_rate": 1

        }

        nozzle_data_2 = {
            "Name": "sample nozzle 2",
            "Nozzle_address": 2,
            "Product_id": 2,
            "Pump_id": 1,
            "Decimal_setting_price_unit": 1,
            "Decimal_setting_amount": 2,
            "Decimal_setting_volume": 2,
            "Totalizer_at_installation": 120000,
            "Nominal_flow_rate": 1
        }

        models.Nozzle.objects.create(**nozzle_data_1)
        models.Nozzle.objects.create(**nozzle_data_2)

        self.authenticator()

    def authenticator(self):
        url = reverse('login')
        data = {
            'Email': 'alabarise@gmail.com',
            'password': 'password'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = response.json()['data']['token']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)

    def test_update_pump(self):
        url = reverse('pumps')
        data = {
            "id": 1,
            "Name": "Newly Updated Pump Name",

            "Nozzles": [
                {"id": 1,
                    "Name": "updated sample nozzle 1",
                    "Nozzle_address": 1,
                    "Decimal_setting_price_unit": 1,
                    "Decimal_setting_amount": 2,
                    "Decimal_setting_volume": 2,
                    "Totalizer_at_installation": 1111,
                    "Nominal_flow_rate": 1,
                    "Display_unit": {
                        "alias": "L",
                    },

                    "Product": {
                        "Product_id": 2,

                    },

                 },
                {
                    "id": 2,
                    "Name": "upated sample nozzle 2",
                    "Nozzle_address": 2,
                    "Decimal_setting_price_unit": 1,
                    "Decimal_setting_amount": 2,
                    "Decimal_setting_volume": 2,
                    "Totalizer_at_installation": 2222,
                    "Nominal_flow_rate": 1,
                    "Display_unit": {
                        "alias": "L",

                    },
                    "Product": {
                        "Product_id": 2,

                    },


                }

            ]
        }

        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(response.json()['data']
                         ['Name'], 'Newly Updated Pump Name')
        # check pump name updated
        self.assertEqual(models.Pump.objects.get(
            pk=1).Name, 'Newly Updated Pump Name')

        # check nozzzle count
        self.assertEqual(models.Nozzle.objects.filter(Pump_id=1).count(), 2)

        # check Product is updated
        self.assertEqual(models.Nozzle.objects.filter(Product_id=2).count(), 2)

        # check Totalizer_at_installation updated

        self.assertEqual(models.Nozzle.objects.get(
            pk=1).Totalizer_at_installation, 1111)
        self.assertEqual(models.Nozzle.objects.get(
            pk=2).Totalizer_at_installation, 2222)


class PumpRetrieveTests(APITestCase):

    def setUp(self):
        user = {
            'Email': 'alabarise@gmail.com',
            'password': 'password'
        }
        get_user_model().objects.create_user(**user)
        self.assertEqual(get_user_model().objects.count(), 1)
        self.assertEqual(get_user_model().objects.get().Email,
                         'alabarise@gmail.com')

        company_data = {


            "Name": "Test Company 1",
            "Country": "Nigera",
            "State": "Lagos",
            "City": "Ikeja",
            "Address": "1, Ayo way.",
            "Company_type": "Multinational",
            "Contact_person_name": "Ridwan Alaba",
            "Contact_person_designation": "Software Engineer",
            "Contact_person_mail": "ridwan.yusuf@smartflowtech",
            "Contact_person_phone": "08011002200"


        }

        models.Companies.objects.create(**company_data)

        devise_1_data = {

            "Name": "DUTCHESS HOSPITAL LTD",
            "Device_unique_address": "aa:27:eb:4c:fd:124",
            "Company_id": 1,
            "Phone_number": "08033717850",
            "transmit_interval": 150,
            "Active": True,

        }

        devise_2_data = {

            "Name": "DUTCHESS HOSPITAL LTD",
            "Device_unique_address": "18:90:eb:4c:fd:000",
            "Company_id": 1,
            "Phone_number": "08033717850",
            "transmit_interval": 150,



        }
        models.Devices.objects.create(**devise_1_data)
        models.Devices.objects.create(**devise_2_data)

        site_1_data = {
            "Name": "First Test Site",
            "Company_id": 1,
            "Country": "Nigeria",
            "State": "lagos",
            "City": "Ikeja",
            "Address": 'Ikosi road',
            "Site_type": "Aviation",
            "Number_of_tanks": 3

        }

        site_2_data = {
            "Name": "2nd Test Site",
            "Company_id": 1,
            "Country": "USA",
            "State": "LA",
            "City": "LA",
            "Address": 'Kennel road',
            "Site_type": "Upstream",
            "Number_of_tanks": 3

        }

        models.Sites.objects.create(**site_1_data)
        models.Sites.objects.create(**site_2_data)

        product_data_1 = {
            "Name": "PMS",
            "Code": "1001"
        }

        product_data_2 = {
            "Name": "AGO",
            "Code": "1002"
        }

        models.Products.objects.create(**product_data_1)
        models.Products.objects.create(**product_data_2)

        pump_brand_data = {
            "Name": 'sample test brand',
            "OEM": "0em 1"
        }

        models.PumpBrand.objects.create(**pump_brand_data)

        pump_data_1 = {
            "Name": "First Pump Name",
            "Pump_protocol": "RS485",
            "Nozzle_count": 1,
            "Note": "First Pump short note",
            "Device_id": 1,
            "Site_id": 1,
            "Pumpbrand_id": 1,


        }

        pump_data_2 = {
            "Name": "Second Pump Name",
            "Pump_protocol": "RS890",
            "Nozzle_count": 3,
            "Note": "First Pump short note",
            "Device_id": 2,
            "Site_id": 2,
            "Pumpbrand_id": 1
        }

        models.Pump.objects.create(**pump_data_1)
        models.Pump.objects.create(**pump_data_2)

        first_pump_nozzle_data = {
            "Name": "sample nozzle 1",
            "Nozzle_address": 1,
            "Product_id": 1,
            "Pump_id": 2,
            "Decimal_setting_price_unit": 1,
            "Decimal_setting_amount": 2,
            "Decimal_setting_volume": 2,
            "Totalizer_at_installation": 120000,
            "Nominal_flow_rate": 1

        }

        second_pump_nozzle_data = {
            "Name": "sample nozzle 2",
            "Nozzle_address": 1,
            "Product_id": 2,
            "Pump_id": 2,
            "Decimal_setting_price_unit": 1,
            "Decimal_setting_amount": 2,
            "Decimal_setting_volume": 2,
            "Totalizer_at_installation": 120000,
            "Nominal_flow_rate": 1
        }
        models.Nozzle.objects.create(**first_pump_nozzle_data)
        models.Nozzle.objects.create(**second_pump_nozzle_data)
        self.authenticator()

    def authenticator(self):
        url = reverse('login')
        data = {
            'Email': 'alabarise@gmail.com',
            'password': 'password'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = response.json()['data']['token']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)

    def test_can_retrieve_all_pump(self):
        url = 'pumps'
        reversed_url = reverse(url)
        response = self.client.get(reversed_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 2)


class NozzlesTest(APITestCase):
    def setUp(self):
        user = {
            'Email': "alabarise@gmail.com"
        }
        get_user_model().objects.create_user(**user)

        product_data = {
            "Name": "Sample Product",
            "Code": "R2006"
        }

        product = models.Products.objects.create(**product_data)

        device_data = {

            "Name": "DUTCHESS HOSPITAL LTD",
            "Device_unique_address": "aa:27:eb:4c:fd:124",
            "Company_id": 1,
            "Phone_number": "08033717850",
            "transmit_interval": 150,
            "Active": True,

        }
        device = models.Devices.objects.create(**device_data)

        company_data = {


            "Name": "Test Company 1",
            "Country": "Nigera",
            "State": "Lagos",
            "City": "Ikeja",
            "Address": "1, Ayo way.",
            "Company_type": "Multinational",
            "Contact_person_name": "Ridwan Alaba",
            "Contact_person_designation": "Software Engineer",
            "Contact_person_mail": "ridwan.yusuf@smartflowtech",
            "Contact_person_phone": "08011002200"


        }
        company = models.Companies.objects.create(**company_data)
        site_data = {
            "Name": "First Test Site",
            "Company": company,
            "Country": "Nigeria",
            "State": "lagos",
            "City": "Ikeja",
            "Address": 'Ikosi road',
            "Site_type": "Aviation",
            "Number_of_tanks": 3

        }
        site = models.Sites.objects.create(**site_data)

        pump_brand_data = {
            "Name": 'sample test brand',
            "OEM": "0em 1"
        }

        pump_brand = models.PumpBrand.objects.create(**pump_brand_data)

        pump_data_1 = {
            "Name": "First Pump Name",
            "Pump_protocol": "RS485",
            "Nozzle_count": 1,
            "Note": "First Pump short note",
            "Device": device,
            "Site": site,
            "Pumpbrand": pump_brand,


        }
        pump = models.Pump.objects.create(**pump_data_1)

        nozzle_data = {
            "Name": "Test Nozzle 1",
            "Nozzle_address": 1,
            "Decimal_setting_price_unit": 0,
            "Decimal_setting_amount": 1,
            "Decimal_setting_volume": 1,
            "Totalizer_at_installation": 2000,
            "Display_unit": "L",
            "Nominal_flow_rate": 1,
            "Product": product,
            "Pump": pump
        }

        models.Nozzle.objects.create(**nozzle_data)
        self.authenticator()

    def authenticator(self):
        url = reverse('login')
        data = {
            'Email': 'alabarise@gmail.com',
            'password': 'password'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = response.json()['data']['token']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)

    # def test_retrieve_nozzle_by_pump_id(self):
    #     url = 'nozzle'
    #     response = self.client.get(reverse(url), {'Pump_id': 1}, format='json',)
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_nozzle(self):
        url = reverse('nozzle')
        data = {
            "Name": "sample nozzle create",
            "Nozzle_address": 1,
            "Product": 1,
            "Pump": 1,
            "Decimal_setting_price_unit": 1,
            "Decimal_setting_amount": 2,
            "Decimal_setting_volume": 2,
            "Totalizer_at_installation": 120000,
            "Nominal_flow_rate": 1
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['data']
                         ['Name'], 'sample nozzle create')
        self.assertEqual(models.Nozzle.objects.count(), 2)

    def test_update_nozzle_by_id(self):
        url = reverse('nozzle_update', kwargs={'nozzle_id': 1})

        data = {
            "Name": "new nozzle name",
            "Nozzle_address": 2,
            "Product": 1,
            "Pump": 1,
        }

        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(response.json()['data']['Name'], 'new nozzle name')
        self.assertEqual(response.json()['data']['Nozzle_address'], 2)


class TestNozzleDashboard(APITestCase):
    def setUp(self):
        user = {
            'Email': "alabarise@gmail.com"
        }
        get_user_model().objects.create_user(**user)
        product_1_data = {
            "Name": "Sample Product 1",
            "Code": "R2005"
        }

        product_2_data = {
            "Name": "Sample Product 2",
            "Code": "R2006"
        }

        product_1 = models.Products.objects.create(**product_1_data)
        product_2 = models.Products.objects.create(**product_2_data)

        company_data = {
            "Name": "Test Company 1",
            "Country": "Nigera",
            "State": "Lagos",
            "City": "Ikeja",
            "Address": "1, Ayo way.",
            "Company_type": "Multinational",
            "Contact_person_name": "Ridwan Alaba",
            "Contact_person_designation": "Software Engineer",
            "Contact_person_mail": "ridwan.yusuf@smartflowtech",
            "Contact_person_phone": "08011002200"
        }
        company = models.Companies.objects.create(**company_data)

        device_data = {

            "Name": "DUTCHESS HOSPITAL LTD",
            "Device_unique_address": "aa:27:eb:4c:fd:124",
            "Company": company,
            "Phone_number": "08033717850",
            "transmit_interval": 150,
            "Active": True,

        }
        device = models.Devices.objects.create(**device_data)

        site_data = {
            "Name": "First Test Site",
            "Company": company,
            "Country": "Nigeria",
            "State": "lagos",
            "City": "Ikeja",
            "Address": 'Ikosi road',
            "Site_type": "Aviation",
            "Number_of_tanks": 3

        }
        site = models.Sites.objects.create(**site_data)

        pump_brand_data = {
            "Name": 'sample test brand',
            "OEM": "0em 1"
        }

        pump_brand = models.PumpBrand.objects.create(**pump_brand_data)

        pump_data_1 = {
            "Name": "First Pump Name",
            "Pump_protocol": "RS485",
            "Nozzle_count": 1,
            "Note": "First Pump short note",
            "Device": device,
            "Site": site,
            "Pumpbrand": pump_brand,


        }
        pump = models.Pump.objects.create(**pump_data_1)

        nozzle_1_data = {
            "Name": "Test Nozzle 1",
            "Nozzle_address": 1,
            "Decimal_setting_price_unit": 0,
            "Decimal_setting_amount": 1,
            "Decimal_setting_volume": 1,
            "Totalizer_at_installation": 2000,
            "Display_unit": "L",
            "Nominal_flow_rate": 1,
            "Product": product_1,
            "Pump": pump
        }

        nozzle_2_data = {
            "Name": "Test Nozzle 2",
            "Nozzle_address": 1,
            "Decimal_setting_price_unit": 0,
            "Decimal_setting_amount": 1,
            "Decimal_setting_volume": 1,
            "Totalizer_at_installation": 2000,
            "Display_unit": "L",
            "Nominal_flow_rate": 1,
            "Product": product_2,
            "Pump": pump
        }

        nozzle_3_data = {
            "Name": "Test Nozzle 3",
            "Nozzle_address": 1,
            "Decimal_setting_price_unit": 0,
            "Decimal_setting_amount": 1,
            "Decimal_setting_volume": 1,
            "Totalizer_at_installation": 2000,
            "Display_unit": "L",
            "Nominal_flow_rate": 1,
            "Product": product_2,
            "Pump": pump
        }

        models.Nozzle.objects.create(**nozzle_1_data)
        models.Nozzle.objects.create(**nozzle_2_data)
        models.Nozzle.objects.create(**nozzle_3_data)
        self.authenticator()

    def authenticator(self):
        url = reverse('login')
        data = {
            'Email': 'alabarise@gmail.com',
            'password': 'password'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = response.json()['data']['token']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)

    # def test_retrieve_nozzle_dashboard_data(self):
    #     # Nozzle dashboard failing
    #     url = reverse('nozzle_dashboard')
    #     response = self.client.get(url, {'Site_id': 1})
    #     self.assertGreater(len(response.json()['data']), 0)
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)


class PumpBrandCreateTests(APITestCase):
    def setUp(self):
        user = {
            'Email': "alabarise@gmail.com"
        }

        pumpBrand_data_1 = {
            "Name": "Test brand 1",
            "OEM": "Gilbaco"
        }

        pumpBrand_data_2 = {
            "Name": "Test pump brand 2",
            "OEM": "Bilp"
        }

        models.PumpBrand.objects.create(**pumpBrand_data_1)
        models.PumpBrand.objects.create(**pumpBrand_data_2)
        get_user_model().objects.create_user(**user)
        self.authenticator()

    def authenticator(self):
        url = reverse('login')
        data = {
            'Email': 'alabarise@gmail.com',
            'password': 'password'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = response.json()['data']['token']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)

    def test_can_create_pump_brand(self):
        url = reverse('pump_brand')

        data = {
            "Name": "New Pump Brand",
            "OEM": "New OEM"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(models.PumpBrand.objects.count(), 3)

    def test_pump_brand_unique(self):
        url = reverse('pump_brand')

        data = {
            "Name": "Test brand 1",
            "OEM": "Gilbaco"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(models.PumpBrand.objects.count(), 2)


class RetrievePumpBrandTests(APITestCase):
    def setUp(self):
        user = {
            'Email': "alabarise@gmail.com"
        }

        pumpBrand_data_1 = {
            "Name": "brand 1",
            "OEM": "Gil"
        }

        pumpBrand_data_2 = {
            "Name": "brand 2",
            "OEM": "Bil"
        }

        models.PumpBrand.objects.create(**pumpBrand_data_1)
        models.PumpBrand.objects.create(**pumpBrand_data_2)
        get_user_model().objects.create_user(**user)
        self.authenticator()

    def authenticator(self):
        url = reverse('login')
        data = {
            'Email': 'alabarise@gmail.com',
            'password': 'password'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = response.json()['data']['token']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)

    def test_retrieve_all__pump_brand(self):
        url = reverse('pump_brand')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 2)


class PumpBrandUpdateTests(APITestCase):
    def setUp(self):
        user = {
            'Email': "alabarise@gmail.com"
        }

        pumpBrand_data = {
            "Name": "brand 1",
            "OEM": "Gil"
        }

        models.PumpBrand.objects.create(**pumpBrand_data)
        get_user_model().objects.create_user(**user)
        self.authenticator()

    def authenticator(self):
        url = reverse('login')
        data = {
            'Email': 'alabarise@gmail.com',
            'password': 'password'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = response.json()['data']['token']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)

    def test_can_update_pump_brand(self):
        url = reverse('pump_brand')

        data = {
            "id": 1,
            "Name": "Updated Name Now",
            "OEM": "Gilbaco 1"
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['data']['Name'], 'Updated Name Now')


class RawPriceChangeTests(APITestCase):
    def setUp(self):
        user = {
            'Email': 'alabarise@gmail.com',
        }

        get_user_model().objects.create_user(**user)

        company_data = {
            "Name": "Test Company 1",
            "Country": "Nigera",
            "State": "Lagos",
            "City": "Ikeja",
            "Address": "1, Ayo way.",
            "Company_type": "Multinational",
            "Contact_person_name": "Ridwan Alaba",
            "Contact_person_designation": "Software Engineer",
            "Contact_person_mail": "ridwan.yusuf@smartflowtech",
            "Contact_person_phone": "08011002200"
        }

        company = models.Companies.objects.create(**company_data)

        site_data = {
            "Name": "First Test Site",
            "Company": company,
            "Country": "Nigeria",
            "State": "lagos",
            "City": "Ikeja",
            "Address": 'Ikosi road',
            "Site_type": "Aviation",
            "Number_of_tanks": 3
        }

        site = models.Sites.objects.create(**site_data)
        product_data = {
            "Name": "Sample Product",
            "Code": "R2006"
        }

        product = models.Products.objects.create(**product_data)

        raw_price_change_data = {
            "Site": site,
            "Product": product,
            "New_price": 18,
            "Scheduled_time": "2021-10-24 14:15:22.000000"
        }
        models.RawPriceChangeData.objects.create(**raw_price_change_data)
        self.authenticator()

    def authenticator(self):
        url = reverse('login')
        data = {
            'Email': 'alabarise@gmail.com',
            'password': 'password'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = response.json()['data']['token']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)

    def test_create_raw_price_change(self):
        url = reverse('raw_price_change')
        data = {
            "Site": 1,
            "Product": 1,
            "New_price": 190.00,
            "Scheduled_time": "2021-10-24 14:15:22.000000"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(models.RawPriceChangeData.objects.count(), 2)

    def test_retrieve_raw_price_change_by_site_id(self):
        url = reverse('raw_price_change')
        response = self.client.get(url, {"Site_id": 1}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['data']), 1)

    def test_approve_raw_price_change(self):
        # a test to approve/reject raw_price_change
        ''' A TEST TO APPROVE AN EXISTING RAW_PRICE_CHANGE '''
        url = reverse('raw_price_change')
        data = {
            "id": 1,
            "Approval": True,
            "New Price": 190.00,
            "Schedule Time": "19-08-24 02:15:22 PM",
            "product_details": {
                "Product_id": 1,
            },
            "site_details": {
                "Site_id": 1
            }


        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['data'],
                         'Price change approved successfully')
        # check if RawPriceChangeData Approved has been updated to True
        self.assertTrue(models.RawPriceChangeData.objects.get(pk=1).Approved)

    def test_reject_raw_price_change(self):
        # a test to approve/reject raw_price_change
        ''' A TEST TO REJECT AN EXISTING RAW_PRICE_CHANGE '''
        url = reverse('raw_price_change')
        data = {
            "id": 1,
            "Approval": False,

        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['data'],
                         'Price change rejected successfully')
        # check if RawPriceChangeData Approved has been updated to False
        self.assertFalse(models.RawPriceChangeData.objects.get(pk=1).Approved)


class PriceChangeTests(APITestCase):
    def setUp(self):
        user = {
            'Email': "alabarise@gmail.com"
        }
        get_user_model().objects.create_user(**user)

        company_data = {
            "Name": "Test Company 1",
            "Country": "Nigera",
            "State": "Lagos",
            "City": "Ikeja",
            "Address": "1, Ayo way.",
            "Company_type": "Multinational",
            "Contact_person_name": "Ridwan Alaba",
            "Contact_person_designation": "Software Engineer",
            "Contact_person_mail": "ridwan.yusuf@smartflowtech",
            "Contact_person_phone": "08011002200"
        }

        company = models.Companies.objects.create(**company_data)

        product_data = {
            "Name": "Sample Product",
            "Code": "R2006"
        }

        product = models.Products.objects.create(**product_data)

        site_data = {
            "Name": "First Test Site",
            "Company": company,
            "Country": "Nigeria",
            "State": "lagos",
            "City": "Ikeja",
            "Address": 'Ikosi road',
            "Site_type": "Aviation",
            "Number_of_tanks": 3
        }

        site = models.Sites.objects.create(**site_data)

        price_change_data = {

            "New_price": 145.00,
            "mac_address": "b2:223:ba",
            "Nozzle_address": 1,
            "Note": "just a note",
            "Scheduled_time": "2021-10-24 14:15:22.000000",
            "Site": site,
            "Product": product

        }

        models.PriceChange.objects.create(**price_change_data)

        self.authenticator()

    def authenticator(self):
        url = reverse('login')
        data = {
            'Email': 'alabarise@gmail.com',
            'password': 'password'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = response.json()['data']['token']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)

    
    def test_create_price_change(self):
        url = reverse('price_change')
        data = [{
            "New_price": 50.00,
            "mac_address": "b2:223:ba",
            "Nozzle_address": 1,
            "Note": "just a note",
            "Scheduled_time": "2021-10-24 14:15:22.000000",
            "Site": 1,
            "Product": 1,
        }]
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_authorize_price_change(self):
        url = reverse('price_change_authorize', kwargs={'pricechange_id': 1})

        data = {
            "New_price": 123.00,

        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(models.PriceChange.objects.get(
            pk=1).New_price, 123.00)


class RetrievePumpsInSiteTests(APITestCase):
    def setUp(self):
        user = {
            'Email': "alabarise@gmail.com"
        }
        get_user_model().objects.create_user(**user)

        company_data = {
            "Name": "Test Company 1",
            "Country": "Nigera",
            "State": "Lagos",
            "City": "Ikeja",
            "Address": "1, Ayo way.",
            "Company_type": "Multinational",
            "Contact_person_name": "Ridwan Alaba",
            "Contact_person_designation": "Software Engineer",
            "Contact_person_mail": "ridwan.yusuf@smartflowtech",
            "Contact_person_phone": "08011002200"
        }

        company = models.Companies.objects.create(**company_data)

        devise_1_data = {

            "Name": "DUTCHESS HOSPITAL LTD",
            "Device_unique_address": "aa:27:eb:4c:fd:124",
            "Company": company,
            "Phone_number": "08033717850",
            "transmit_interval": 150,
            "Active": True,

        }

        devise_2_data = {

            "Name": "DUTCHESS HOSPITAL LTD",
            "Device_unique_address": "bb:27:eb:4c:fd:124",
            "Company": company,
            "Phone_number": "08033717850",
            "transmit_interval": 150,
            "Active": True,

        }

        devise_3_data = {

            "Name": "DUTCHESS HOSPITAL LTD",
            "Device_unique_address": "cc:27:eb:4c:fd:124",
            "Company": company,
            "Phone_number": "08033717850",
            "transmit_interval": 150,
            "Active": True,

        }

        devise_4_data = {

            "Name": "DUTCHESS HOSPITAL LTD",
            "Device_unique_address": "dd:27:eb:4c:fd:124",
            "Company": company,
            "Phone_number": "08033717850",
            "transmit_interval": 150,
            "Active": True,

        }

        devise_1 = models.Devices.objects.create(**devise_1_data)
        devise_2 = models.Devices.objects.create(**devise_2_data)
        devise_3 = models.Devices.objects.create(**devise_3_data)
        devise_4 = models.Devices.objects.create(**devise_4_data)

        site_1_data = {
            "Name": "First Test Site",
            "Company": company,
            "Country": "Nigeria",
            "State": "lagos",
            "City": "Ikeja",
            "Address": 'Ikosi road',
            "Site_type": "Aviation",
            "Number_of_tanks": 3

        }

        site_2_data = {
            "Name": "2nd Test Site",
            "Company": company,
            "Country": "Nigeria",
            "State": "lagos",
            "City": "Ikeja",
            "Address": 'Ikosi road',
            "Site_type": "Aviation",
            "Number_of_tanks": 3

        }

        site_3_data = {
            "Name": "3rd Test Site",
            "Company": company,
            "Country": "Nigeria",
            "State": "lagos",
            "City": "Ikeja",
            "Address": 'Ikosi road',
            "Site_type": "Aviation",
            "Number_of_tanks": 3

        }

        site_1 = models.Sites.objects.create(**site_1_data)
        site_2 = models.Sites.objects.create(**site_2_data)
        site_3 = models.Sites.objects.create(**site_3_data)

        product_1_data = {
            "Name": "PMS",
            "Code": "1001"
        }

        product_2_data = {
            "Name": "AGO",
            "Code": "1002"
        }

        product_1 = models.Products.objects.create(**product_1_data)
        product_2 = models.Products.objects.create(**product_2_data)

        pump_brand_data = {
            "Name": 'sample test brand',
            "OEM": "0em 1"
        }

        pump_brand = models.PumpBrand.objects.create(**pump_brand_data)

        pump_1_data = {
            "Name": "First Pump Name",
            "Pump_protocol": "RS485",
            "Nozzle_count": 2,
            "Note": "First Pump short note",
            "Device": devise_1,
            "Site": site_1,
            "Pumpbrand": pump_brand,


        }

        pump_2_data = {
            "Name": "2ND Pump Name",
            "Pump_protocol": "RS485",
            "Nozzle_count": 1,
            "Note": "2nd Pump short note",
            "Device": devise_2,
            "Site": site_3,
            "Pumpbrand": pump_brand,
        }

        pump_3_data = {
            "Name": "3RD Pump Name",
            "Pump_protocol": "RS485",
            "Nozzle_count": 1,
            "Note": "3rd Pump short note",
            "Device": devise_3,
            "Site": site_2,
            "Pumpbrand": pump_brand,
        }

        pump_4_data = {
            "Name": "4TH Pump Name",
            "Pump_protocol": "RS485",
            "Nozzle_count": 1,
            "Note": "4th Pump short note",
            "Device": devise_4,
            "Site": site_1,
            "Pumpbrand": pump_brand,
        }

        models.Pump.objects.create(**pump_1_data)
        models.Pump.objects.create(**pump_2_data)
        models.Pump.objects.create(**pump_3_data)
        models.Pump.objects.create(**pump_4_data)

        self.authenticator()

    def authenticator(self):
        url = reverse('login')
        data = {
            'Email': 'alabarise@gmail.com',
            'password': 'password'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = response.json()['data']['token']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)

    def test_retrieve_pumps_in_site(self):
        self.assertEqual(models.Pump.objects.count(), 4)
        self.assertEqual(models.Sites.objects.count(), 3)

        url = reverse('pumps_site')
        response = self.client.get(url, {"Site_id": 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 2)


class RemoteConfigTests(APITestCase):
    def setUp(self):
        user = {
            'Email': "alabarise@gmail.com"
        }
        get_user_model().objects.create_user(**user)

        product_data = {
            "Name": "Sample Product",
            "Code": "R2005"
        }

        product = models.Products.objects.create(**product_data)

        company_data = {
            "Name": "Test Company 1",
            "Country": "Nigera",
            "State": "Lagos",
            "City": "Ikeja",
            "Address": "1, Ayo way.",
            "Company_type": "Multinational",
            "Contact_person_name": "Ridwan Alaba",
            "Contact_person_designation": "Software Engineer",
            "Contact_person_mail": "ridwan.yusuf@smartflowtech",
            "Contact_person_phone": "08011002200"
        }

        company = models.Companies.objects.create(**company_data)

        device_1_data = {

            "Name": "DUTCHESS HOSPITAL LTD",
            "Device_unique_address": "aa:27:eb:4c:fd:14",
            "Company": company,
            "Phone_number": "08033717850",
            "transmit_interval": 150,
            "Active": True,

        }

        device_2_data = {

            "Name": "DUTCHESS HOSPITAL LTD",
            "Device_unique_address": "bb:00:22:33:11",
            "Company": company,
            "Phone_number": "08033717850",
            "transmit_interval": 150,
            "Active": True,

        }

        device_1 = models.Devices.objects.create(**device_1_data)
        device_2 = models.Devices.objects.create(**device_2_data)

        site_data = {
            "Name": "First Test Site",
            "Company": company,
            "Country": "Nigeria",
            "State": "lagos",
            "City": "Ikeja",
            "Address": 'Ikosi road',
            "Site_type": "Aviation",
            "Number_of_tanks": 3

        }
        site = models.Sites.objects.create(**site_data)

        pump_brand_data = {
            "Name": 'sample test brand',
            "OEM": "0em 1"
        }

        pump_brand = models.PumpBrand.objects.create(**pump_brand_data)

        pump_1_data = {
            "Name": "First Pump Name",
            "Pump_protocol": "RS485",
            "Nozzle_count": 2,
            "Note": "First Pump short note",
            "Device": device_1,
            "Site": site,
            "Pumpbrand": pump_brand,


        }

        pump_2_data = {
            "Name": "First Pump Name",
            "Pump_protocol": "RS485",
            "Nozzle_count": 2,
            "Note": "First Pump short note",
            "Device": device_2,
            "Site": site,
            "Pumpbrand": pump_brand,


        }
        pump_1 = models.Pump.objects.create(**pump_1_data)
        pump_2 = models.Pump.objects.create(**pump_2_data)

        nozzle_1_data = {
            "Name": "Test Nozzle 1",
            "Nozzle_address": 1,
            "Decimal_setting_price_unit": 0,
            "Decimal_setting_amount": 1,
            "Decimal_setting_volume": 1,
            "Totalizer_at_installation": 2000,
            "Display_unit": "L",
            "Nominal_flow_rate": 1,
            "Product": product,
            "Pump": pump_1,
        }

        nozzle_2_data = {
            "Name": "Test Nozzle 2",
            "Nozzle_address": 1,
            "Decimal_setting_price_unit": 0,
            "Decimal_setting_amount": 1,
            "Decimal_setting_volume": 1,
            "Totalizer_at_installation": 2000,
            "Display_unit": "L",
            "Nominal_flow_rate": 1,
            "Product": product,
            "Pump": pump_1
        }

        nozzle_3_data = {
            "Name": "Test Nozzle 2",
            "Nozzle_address": 1,
            "Decimal_setting_price_unit": 0,
            "Decimal_setting_amount": 1,
            "Decimal_setting_volume": 1,
            "Totalizer_at_installation": 2000,
            "Display_unit": "L",
            "Nominal_flow_rate": 1,
            "Product": product,
            "Pump": pump_1
        }

        nozzle_4_data = {
            "Name": "Test Nozzle 2",
            "Nozzle_address": 1,
            "Decimal_setting_price_unit": 0,
            "Decimal_setting_amount": 1,
            "Decimal_setting_volume": 1,
            "Totalizer_at_installation": 2000,
            "Display_unit": "L",
            "Nominal_flow_rate": 1,
            "Product": product,
            "Pump": pump_2
        }

        models.Nozzle.objects.create(**nozzle_1_data)
        models.Nozzle.objects.create(**nozzle_2_data)
        models.Nozzle.objects.create(**nozzle_3_data)
        models.Nozzle.objects.create(**nozzle_4_data)
        self.authenticator()

    def authenticator(self):
        url = reverse('login')
        data = {
            'Email': 'alabarise@gmail.com',
            'password': 'password'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = response.json()['data']['token']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)

  

class RetrieveNozzleLoggerTransactionData(APITestCase):
    def setUp(self):
        user = {
            'Email': 'alabarise@gmail.com',
        }

        get_user_model().objects.create_user(**user)

        company_data = {
            "Name": "Test Company 1",
            "Country": "Nigera",
            "State": "Lagos",
            "City": "Ikeja",
            "Address": "1, Ayo way.",
            "Company_type": "Multinational",
            "Contact_person_name": "Ridwan Alaba",
            "Contact_person_designation": "Software Engineer",
            "Contact_person_mail": "ridwan.yusuf@smartflowtech",
            "Contact_person_phone": "08011002200"
        }

        company = models.Companies.objects.create(**company_data)

        site_data = {
            "Name": "First Test Site",
            "Company": company,
            "Country": "Nigeria",
            "State": "lagos",
            "City": "Ikeja",
            "Address": 'Ikosi road',
            "Site_type": "Aviation",
            "Number_of_tanks": 3
        }

        site = models.Sites.objects.create(**site_data)

        devise_data = {

            "Name": "DUTCHESS HOSPITAL LTD",
            "Device_unique_address": "b3:78:90:09",
            "Company": company,
            "Phone_number": "08033717850",
            "transmit_interval": 150,
            "Active": True,

        }

        device = models.Devices.objects.create(**devise_data)
        pump_brand_data = {
            "Name": 'sample test brand',
            "OEM": "0em 1"
        }

        pump_brand = models.PumpBrand.objects.create(**pump_brand_data)

        pump_data = {
            "Name": "First Pump Name",
            "Pump_protocol": "RS485",
            "Nozzle_count": 3,
            "Note": "First Pump short note",
            "Device": device,
            "Site": site,
            "Pumpbrand": pump_brand,


        }

        pump = models.Pump.objects.create(**pump_data)

        product_data_1 = {
            "Name": "Sample Product 1",
            "Code": "R2099"
        }

        product_data_2 = {
            "Name": "Sample Product 2",
            "Code": "R2005"
        }

        product1 = models.Products.objects.create(**product_data_1)
        product2 = models.Products.objects.create(**product_data_2)

        nozzle_1_data = {
            "Name": "Test Nozzle 1",
            "Nozzle_address": 1,
            "Decimal_setting_price_unit": 0,
            "Decimal_setting_amount": 1,
            "Decimal_setting_volume": 1,
            "Totalizer_at_installation": 2000,
            "Display_unit": "L",
            "Nominal_flow_rate": 1,
            "Product": product1,
            "Pump": pump
        }

        nozzle_2_data = {
            "Name": "Test Nozzle 2",
            "Nozzle_address": 2,
            "Decimal_setting_price_unit": 0,
            "Decimal_setting_amount": 1,
            "Decimal_setting_volume": 1,
            "Totalizer_at_installation": 2000,
            "Display_unit": "L",
            "Nominal_flow_rate": 1,
            "Product": product2,
            "Pump": pump
        }

        models.Nozzle.objects.create(**nozzle_1_data)
        models.Nozzle.objects.create(**nozzle_2_data)

        transaction_1_data = {

            "local_id": 2147483641,
            "Nozzle_address": "2",
            "Transaction_start_time": datetime.strptime("2019-08-24 00:00",  "%Y-%m-%d %H:%M"),
            "Transaction_stop_time": datetime.strptime("2019-08-24 00:00",  "%Y-%m-%d %H:%M"),
            "Transaction_raw_volume": 20.00,
            "Transaction_raw_amount": 2500.00,
            "Raw_transaction_price_per_unit": 120.00,
            "Pump_mac_address": "b3:78:90:09",
            "Transaction_start_pump_totalizer_volume": 23000,
            "Transaction_stop_pump_totalizer_volume": 24000,
            "Transaction_start_pump_totalizer_amount": 60000,
            "Transaction_stop_pump_totalizer_amount": 65000,
            "Device": device,
            "Site": site

        }

        transaction_2_data = {

            "local_id": 2147483638,
            "Nozzle_address": "1",
            "Transaction_start_time": datetime.strptime("2019-08-24 00:00",  "%Y-%m-%d %H:%M"),
            "Transaction_stop_time": datetime.strptime("2019-11-24 00:00",  "%Y-%m-%d %H:%M"),
            "Transaction_raw_volume": 20.00,
            "Transaction_raw_amount": 2500.00,
            "Raw_transaction_price_per_unit": 120.00,
            "Pump_mac_address": "b3:78:90:09",
            "Transaction_start_pump_totalizer_volume": 23000,
            "Transaction_stop_pump_totalizer_volume": 24000,
            "Transaction_start_pump_totalizer_amount": 60000,
            "Transaction_stop_pump_totalizer_amount": 65000,
            "Device": device,
            "Site": site

        }

        transaction_3_data = {

            "local_id": 21347483648,
            "Nozzle_address": "1",
            "Transaction_start_time": datetime.strptime("2019-08-24 00:00",  "%Y-%m-%d %H:%M"),
            "Transaction_stop_time": datetime.strptime("2019-09-24 00:00",  "%Y-%m-%d %H:%M"),
            "Transaction_raw_volume": 20.00,
            "Transaction_raw_amount": 2500.00,
            "Raw_transaction_price_per_unit": 120.00,
            "Pump_mac_address": "b3:78:90:09",
            "Transaction_start_pump_totalizer_volume": 23000,
            "Transaction_stop_pump_totalizer_volume": 24000,
            "Transaction_start_pump_totalizer_amount": 60000,
            "Transaction_stop_pump_totalizer_amount": 65000,
            "Device": device,
            "Site": site

        }
        # USE_TZ = True for this date format to work

        models.TransactionData.objects.create(**transaction_1_data)
        models.TransactionData.objects.create(**transaction_2_data)
        models.TransactionData.objects.create(**transaction_3_data)

        self.authenticator()

    def authenticator(self):
        url = reverse('login')
        data = {
            'Email': 'alabarise@gmail.com',
            'password': 'password'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = response.json()['data']['token']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)

    def test_retrieve_transaction_data(self):
        url = reverse('transaction_logger')
        response = self.client.get(url, {"Nozzle_addresses": "1", "Site_id": 1, "products": "",
                                   "Pump_mac_address": "b3:78:90:09", "period": "2019-05-24 00:00,2019-11-24 00:00"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 2)


class CreateNozzleLoggerTransactionData(APITestCase):
    def setUp(self):
        user = {
            'Email': 'alabarise@gmail.com',
        }

        get_user_model().objects.create_user(**user)

        company_data = {
            "Name": "Test Company 1",
            "Country": "Nigera",
            "State": "Lagos",
            "City": "Ikeja",
            "Address": "1, Ayo way.",
            "Company_type": "Multinational",
            "Contact_person_name": "Ridwan Alaba",
            "Contact_person_designation": "Software Engineer",
            "Contact_person_mail": "ridwan.yusuf@smartflowtech",
            "Contact_person_phone": "08011002200"
        }

        company = models.Companies.objects.create(**company_data)

        site_data = {
            "Name": "First Test Site",
            "Company": company,
            "Country": "Nigeria",
            "State": "lagos",
            "City": "Ikeja",
            "Address": 'Ikosi road',
            "Site_type": "Aviation",
            "Number_of_tanks": 3
        }

        site = models.Sites.objects.create(**site_data)

        product_data_1 = {
            "Name": "Sample Product 1",
            "Code": "R2099"
        }

        product_data_2 = {
            "Name": "Sample Product 2",
            "Code": "R2005"
        }

        product1 = models.Products.objects.create(**product_data_1)
        product2 = models.Products.objects.create(**product_data_2)
        device_data = {

            "Name": "DUTCHESS HOSPITAL LTD",
            "Device_unique_address": "b3:12:232:ab",
            "Company": company,
            "Phone_number": "08033717850",
            "transmit_interval": 150,
            "Active": True,

        }

        device = models.Devices.objects.create(**device_data)

        pump_brand_data = {
            "Name": 'sample test brand',
            "OEM": "0em 1"
        }

        pump_brand = models.PumpBrand.objects.create(**pump_brand_data)

        pump_data = {
            "Name": "First Pump Name",
            "Pump_protocol": "RS485",
            "Nozzle_count": 3,
            "Note": "First Pump short note",
            "Device": device,
            "Site": site,
            "Pumpbrand": pump_brand,


        }

        pump = models.Pump.objects.create(**pump_data)

        nozzle_1_data = {
            "Name": "Test Nozzle 1",
            "Nozzle_address": 1,
            "Decimal_setting_price_unit": 0,
            "Decimal_setting_amount": 1,
            "Decimal_setting_volume": 1,
            "Totalizer_at_installation": 2000,
            "Display_unit": "L",
            "Nominal_flow_rate": 1,
            "Product": product1,
            "Pump": pump
        }

        nozzle_2_data = {
            "Name": "Test Nozzle 2",
            "Nozzle_address": 2,
            "Decimal_setting_price_unit": 0,
            "Decimal_setting_amount": 1,
            "Decimal_setting_volume": 1,
            "Totalizer_at_installation": 2000,
            "Display_unit": "L",
            "Nominal_flow_rate": 1,
            "Product": product2,
            "Pump": pump
        }

        models.Nozzle.objects.create(**nozzle_1_data)
        models.Nozzle.objects.create(**nozzle_2_data)
        devise_data = {

            "Name": "DUTCHESS HOSPITAL LTD",
            "Device_unique_address": "aa:27:eb:4c:fd:124",
            "Company": company,
            "Phone_number": "08033717850",
            "transmit_interval": 150,
            "Active": True,

        }

        models.Devices.objects.create(**devise_data)

        transaction_1_data = {

            "local_id": 1,
            "Nozzle_address": "2",
            "Transaction_start_time": "2019-05-24 00:00",
            "Transaction_stop_time": "2019-05-24 00:00",
            "Transaction_raw_volume": 20.00,
            "Transaction_raw_amount": 2500.00,
            "Raw_transaction_price_per_unit": 120.00,
            "Pump_mac_address": "b3:12:232:ab",
            "Transaction_start_pump_totalizer_volume": 23000,
            "Transaction_stop_pump_totalizer_volume": 24000,
            "Transaction_start_pump_totalizer_amount": 60000,
            "Transaction_stop_pump_totalizer_amount": 65000,
            "Device": device,
            "Site": site

        }

        models.TransactionData.objects.create(**transaction_1_data)
        self.authenticator()

    def authenticator(self):
        url = reverse('login')
        data = {
            'Email': 'alabarise@gmail.com',
            'password': 'password'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = response.json()['data']['token']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)

    def test_create_transaction_data(self):
        url = reverse('transaction_logger')
        data = [{

            "local_id": 2,
            "Nozzle_address": "1",
            "Transaction_start_time": "2019-08-24T14:15:22Z",
            "Transaction_stop_time": "2019-08-24T14:15:22Z",
            "Transaction_raw_volume": 20.00,
            "Transaction_raw_amount": 2500.00,
            "Raw_transaction_price_per_unit": 120.00,
            "Pump_mac_address": "b3:12:232:ab",
            "Transaction_start_pump_totalizer_volume": 23000,
            "Transaction_stop_pump_totalizer_volume": 24000,
            "Transaction_start_pump_totalizer_amount": 60000,
            "Transaction_stop_pump_totalizer_amount": 65000,
            "Device": 1,
            "Site": 1

        },
            {

            "local_id": 3,
            "Nozzle_address": "1",
            "Transaction_start_time": "2019-08-24T14:15:22Z",
            "Transaction_stop_time": "2019-08-24T14:15:22Z",
            "Transaction_raw_volume": 20.00,
            "Transaction_raw_amount": 2500.00,
            "Raw_transaction_price_per_unit": 120.00,
            "Pump_mac_address": "b3:12:232:ab",
            "Transaction_start_pump_totalizer_volume": 23000,
            "Transaction_stop_pump_totalizer_volume": 24000,
            "Transaction_start_pump_totalizer_amount": 60000,
            "Transaction_stop_pump_totalizer_amount": 65000,
            "Device": 1,
            "Site": 1

        }]
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(models.TransactionData.objects.count(),  3)

    # def test_pic_create_transaction_data(self):
    #     url = reverse('pic_transaction_logger')
    #     data = [ 
    #             ["221908135806100000390","1","2022-08-22 13:29:12","2022-08-22 13:29:12","055410","087548","1580","Pic-00001","44358623","44364164","80568768","80656316","1",230]
    #         ]
    #     response = self.client.post(url, data, format='json')
    #     self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    #     self.assertEqual(models.TransactionData.objects.count(),  3)
    # def test_pic_double_transaction_not_saved(self):
    #     url = reverse('pic_transaction_logger')
    #     data = [ 
    #             ["221908135806100000351","1","2022-08-22 13:29:12","2022-08-22 13:29:12","055410","087548","1580","Pic-00001","44358623","44364164","80568768","80656316","1",230],
    #             ["221908135806100000351","1","2022-08-22 13:29:12","2022-08-22 13:29:12","055410","087548","1580","Pic-00001","44358623","44364164","80568768","80656316","1",230],
    #         ]
    #     response = self.client.post(url, data, format='json')
    #     self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    #     self.assertEqual(models.TransactionData.objects.count(),  3)

    def test_double_transaction_data_not_saved(self):
        url = reverse('transaction_logger')
        data = [{

            "local_id": 1,
            "Nozzle_address": "2",
            "Transaction_start_time": "2019-08-24T14:15:22Z",
            "Transaction_stop_time": "2019-08-24T14:15:22Z",
            "Transaction_raw_volume": 20.00,
            "Transaction_raw_amount": 2500.00,
            "Raw_transaction_price_per_unit": 120.00,
            "Pump_mac_address": "b3:12:232:ab",
            "Transaction_start_pump_totalizer_volume": 23000,
            "Transaction_stop_pump_totalizer_volume": 24000,
            "Transaction_start_pump_totalizer_amount": 60000,
            "Transaction_stop_pump_totalizer_amount": 65000,
            "Device": 1,
            "Site": 1

        },
            {

            "local_id": 2,
            "Nozzle_address": "2",
            "Transaction_start_time": "2019-08-24T14:15:22Z",
            "Transaction_stop_time": "2019-08-24T14:15:22Z",
            "Transaction_raw_volume": 20.00,
            "Transaction_raw_amount": 2500.00,
            "Raw_transaction_price_per_unit": 120.00,
            "Pump_mac_address": "b3:12:232:ab",
            "Transaction_start_pump_totalizer_volume": 23000,
            "Transaction_stop_pump_totalizer_volume": 24000,
            "Transaction_start_pump_totalizer_amount": 60000,
            "Transaction_stop_pump_totalizer_amount": 65000,
            "Device": 1,
            "Site": 1

        },
            {

            "local_id": 2,
            "Nozzle_address": "2",
            "Transaction_start_time": "2019-08-24T14:15:22Z",
            "Transaction_stop_time": "2019-08-24T14:15:22Z",
            "Transaction_raw_volume": 20.00,
            "Transaction_raw_amount": 2500.00,
            "Raw_transaction_price_per_unit": 120.00,
            "Pump_mac_address": "b3:12:232:ab",
            "Transaction_start_pump_totalizer_volume": 23000,
            "Transaction_stop_pump_totalizer_volume": 24000,
            "Transaction_start_pump_totalizer_amount": 60000,
            "Transaction_stop_pump_totalizer_amount": 65000,
            "Device": 1,
            "Site": 1

        },
            {

            "local_id": 2,
            "Nozzle_address": "2",
            "Transaction_start_time": "2019-08-24T14:15:22Z",
            "Transaction_stop_time": "2019-08-24T14:15:22Z",
            "Transaction_raw_volume": 20.00,
            "Transaction_raw_amount": 2500.00,
            "Raw_transaction_price_per_unit": 120.00,
            "Pump_mac_address": "b3:12:232:ab",
            "Transaction_start_pump_totalizer_volume": 23000,
            "Transaction_stop_pump_totalizer_volume": 24000,
            "Transaction_start_pump_totalizer_amount": 60000,
            "Transaction_stop_pump_totalizer_amount": 65000,
            "Device": 1,
            "Site": 1

        },
        {
            "local_id": '15890-b8:27:eb:00:c5:c9-2022-03-22 18:47:26',
            "Nozzle_address": "2",
            "Transaction_start_time": "2019-08-24T14:15:22Z",
            "Transaction_stop_time": "2019-08-24T14:15:22Z",
            "Transaction_raw_volume": 20.00,
            "Transaction_raw_amount": 2500.00,
            "Raw_transaction_price_per_unit": 120.00,
            "Pump_mac_address": "b3:12:232:ab",
            "Transaction_start_pump_totalizer_volume": 23000,
            "Transaction_stop_pump_totalizer_volume": 24000,
            "Transaction_start_pump_totalizer_amount": 60000,
            "Transaction_stop_pump_totalizer_amount": 65000,
            "Device": 1,
            "Site": 1

        },
         {
            "local_id": '15890-b8:27:eb:00:c5:c9-2022-03-22 18:47:26',
            "Nozzle_address": "2",
            "Transaction_start_time": "2019-08-24T14:15:22Z",
            "Transaction_stop_time": "2019-08-24T14:15:22Z",
            "Transaction_raw_volume": 20.00,
            "Transaction_raw_amount": 2500.00,
            "Raw_transaction_price_per_unit": 120.00,
            "Pump_mac_address": "b3:12:232:ab",
            "Transaction_start_pump_totalizer_volume": 23000,
            "Transaction_stop_pump_totalizer_volume": 24000,
            "Transaction_start_pump_totalizer_amount": 60000,
            "Transaction_stop_pump_totalizer_amount": 65000,
            "Device": 1,
            "Site": 1

        },

        ]
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # temporarily
        self.assertEqual(models.TransactionData.objects.count(),  3)


class RetrieveNozzleTrends(APITestCase):
    def setUp(self):
        user = {
            'Email': 'alabarise@gmail.com',
        }

        get_user_model().objects.create_user(**user)

        company_data = {
            "Name": "Test Company 1",
            "Country": "Nigera",
            "State": "Lagos",
            "City": "Ikeja",
            "Address": "1, Ayo way.",
            "Company_type": "Multinational",
            "Contact_person_name": "Ridwan Alaba",
            "Contact_person_designation": "Software Engineer",
            "Contact_person_mail": "ridwan.yusuf@smartflowtech",
            "Contact_person_phone": "08011002200"
        }

        company = models.Companies.objects.create(**company_data)

        site_data = {
            "Name": "First Test Site",
            "Company": company,
            "Country": "Nigeria",
            "State": "lagos",
            "City": "Ikeja",
            "Address": 'Ikosi road',
            "Site_type": "Aviation",
            "Number_of_tanks": 3
        }

        site = models.Sites.objects.create(**site_data)

        device_data = {

            "Name": "DUTCHESS HOSPITAL LTD",
            "Device_unique_address": "b3:12:232:ab",
            "Company": company,
            "Phone_number": "08033717850",
            "transmit_interval": 150,
            "Active": True,

        }

        device = models.Devices.objects.create(**device_data)

        pump_brand_data = {
            "Name": 'sample test brand',
            "OEM": "0em 1"
        }

        pump_brand = models.PumpBrand.objects.create(**pump_brand_data)

        pump_data = {
            "Name": "First Pump Name",
            "Pump_protocol": "RS485",
            "Nozzle_count": 3,
            "Note": "First Pump short note",
            "Device": device,
            "Site": site,
            "Pumpbrand": pump_brand,


        }

        pump = models.Pump.objects.create(**pump_data)

        product_data_1 = {
            "Name": "Sample Product 1",
            "Code": "R2099"
        }

        product_data_2 = {
            "Name": "Sample Product 2",
            "Code": "R2005"
        }

        product1 = models.Products.objects.create(**product_data_1)
        product2 = models.Products.objects.create(**product_data_2)

        nozzle_1_data = {
            "Name": "Test Nozzle 1",
            "Nozzle_address": 1,
            "Decimal_setting_price_unit": 0,
            "Decimal_setting_amount": 1,
            "Decimal_setting_volume": 1,
            "Totalizer_at_installation": 2000,
            "Display_unit": "L",
            "Nominal_flow_rate": 1,
            "Product": product1,
            "Pump": pump
        }

        nozzle_2_data = {
            "Name": "Test Nozzle 2",
            "Nozzle_address": 2,
            "Decimal_setting_price_unit": 0,
            "Decimal_setting_amount": 1,
            "Decimal_setting_volume": 1,
            "Totalizer_at_installation": 2000,
            "Display_unit": "L",
            "Nominal_flow_rate": 1,
            "Product": product2,
            "Pump": pump
        }

        nozzle_3_data = {
            "Name": "Test Nozzle 2",
            "Nozzle_address": 3,
            "Decimal_setting_price_unit": 0,
            "Decimal_setting_amount": 1,
            "Decimal_setting_volume": 1,
            "Totalizer_at_installation": 2000,
            "Display_unit": "L",
            "Nominal_flow_rate": 1,
            "Product": product1,
            "Pump": pump
        }

        models.Nozzle.objects.create(**nozzle_1_data)
        models.Nozzle.objects.create(**nozzle_2_data)
        models.Nozzle.objects.create(**nozzle_3_data)

        transaction_1_data = {

            "local_id": 1111,
            "Nozzle_address": "1",
            "Transaction_start_time": "2019-08-24 14:15",
            "Transaction_stop_time": "2019-08-24 14:15",
            "Transaction_raw_volume": 10.00,
            "Transaction_raw_amount": 2500.00,
            "Raw_transaction_price_per_unit": 120.00,
            "Pump_mac_address": "b3:12:232:ab",
            "Transaction_start_pump_totalizer_volume": 23000,
            "Transaction_stop_pump_totalizer_volume": 24000,
            "Transaction_start_pump_totalizer_amount": 60000,
            "Transaction_stop_pump_totalizer_amount": 65000,
            "Device": device,
            "Site": site

        }

        transaction_2_data = {

            "local_id": 22222,
            "Nozzle_address": "2",
            "Transaction_start_time": datetime.strptime("2019-08-24 00:00",  "%Y-%m-%d %H:%M"),
            "Transaction_stop_time": datetime.strptime("2019-08-24 00:00", "%Y-%m-%d %H:%M"),
            "Transaction_raw_volume": 20.00,
            "Transaction_raw_amount": 5300.00,
            "Raw_transaction_price_per_unit": 120.00,
            "Pump_mac_address": "b3:12:232:ab",
            "Transaction_start_pump_totalizer_volume": 23000,
            "Transaction_stop_pump_totalizer_volume": 24000,
            "Transaction_start_pump_totalizer_amount": 60000,
            "Transaction_stop_pump_totalizer_amount": 65000,
            "Device": device,
            "Site": site

        }

        transaction_3_data = {

            "local_id": 333333,
            "Nozzle_address": "2",
            "Transaction_start_time": datetime.strptime("2019-08-24 14:15", "%Y-%m-%d %H:%M"),
            "Transaction_stop_time": datetime.strptime("2019-08-24 15:15", "%Y-%m-%d %H:%M"),
            "Transaction_raw_volume": 30.00,
            "Transaction_raw_amount": 7000.00,
            "Raw_transaction_price_per_unit": 120.00,
            "Pump_mac_address": "b3:12:232:ab",
            "Transaction_start_pump_totalizer_volume": 23000,
            "Transaction_stop_pump_totalizer_volume": 24000,
            "Transaction_start_pump_totalizer_amount": 60000,
            "Transaction_stop_pump_totalizer_amount": 65000,
            "Device": device,
            "Site": site

        }

        transaction_4_data = {

            "local_id": 4444,
            "Nozzle_address": "3",
            "Transaction_start_time": datetime.strptime("2019-05-24 00:00", "%Y-%m-%d %H:%M"),
            "Transaction_stop_time": datetime.strptime("2019-06-24 00:00", "%Y-%m-%d %H:%M"),
            "Transaction_raw_volume": 40.00,
            "Transaction_raw_amount": 9000.00,
            "Raw_transaction_price_per_unit": 120.00,
            "Pump_mac_address": "b3:12:232:ab",
            "Transaction_start_pump_totalizer_volume": 23000,
            "Transaction_stop_pump_totalizer_volume": 24000,
            "Transaction_start_pump_totalizer_amount": 60000,
            "Transaction_stop_pump_totalizer_amount": 65000,
            "Device": device,
            "Site": site

        }

        models.TransactionData.objects.create(**transaction_1_data)
        models.TransactionData.objects.create(**transaction_2_data)
        models.TransactionData.objects.create(**transaction_3_data)
        models.TransactionData.objects.create(**transaction_4_data)
        self.authenticator()

    def authenticator(self):
        url = reverse('login')
        data = {
            'Email': 'alabarise@gmail.com',
            'password': 'password'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = response.json()['data']['token']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)

    def test_retrieve_nozzle_trends(self):
        url = reverse('nozzle_trends')
        data = {
            "Nozzle_addresses": "1,2",
            "Site_id": 1,
            "pump_id": 1,
            "Pump_mac_address": "b3:12:232:ab",
            "period": "2019-04-24 00:00,2019-11-24 00:00"

        }
        response = self.client.get(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # check nozzle_names length
        self.assertEqual(len(response.json()['data']['trendList'][1]), 2)
        # Site_id, Pump_mac_address,Nozzle_address, Transaction_stop_time_

        # check nozzle_dates lenght for matching transactions
        self.assertEqual(len(response.json()['data']['trendList'][0]), 3)

        # check total voume of match transaction
        self.assertEqual(response.json()['data']
                         ['totalVolume'], 10.00+20.00+30.00)

        # check total revenue of match transaction
        self.assertEqual(
            response.json()['data']['totalRevenue'], 2500.00+5300.00+7000.00)
