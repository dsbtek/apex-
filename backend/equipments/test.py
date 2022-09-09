from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APITestCase

from .. import models


class EquipmentModelTest(APITestCase):
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
        models.Products.objects.create(**{
            'Name': 'Petrol',
            'Code': 'PMS'
        })

    def test_can_create_Equipment_model(self):
        data = {
            'name': 'Test Equipment',
            'product_id': 1,
            'oem': 'CAT',
            'model': 'R-100',
            'oem_consumption_rate': 30.45,
            'running_hours_source': 'DI',
            'litres_consumed_source': 'TL',
            'address': 1,
            'model': 'Yamaha',
            'initial_totaliser_hours': 20,
            'site_id': 1,
        }
        equipment = models.Equipment.objects.create(**data)
        self.assertEqual(models.Equipment.objects.count(), 1)
        self.assertEqual(equipment.initial_totaliser_hours, equipment.totaliser_hours)


class EquipmentCreateViewTests(APITestCase):
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
        fm_1 = {
            'serial_number': 'FM-001',
            'max_temp': 100.00,
            'address': 111,
            'site_id': 1
        }
        models.Flowmeter.objects.create(**fm_1)
        models.Products.objects.create(**{
            'Name': 'Petrol',
            'Code': 'PMS'
        })
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

    def test_can_create_Equipment_with_DI_hours_source(self):
        url = reverse('equipment_list')
        data = {
            'name': 'Test Equipment',
            'product_id': 1,
            'oem': 'CAT',
            'model': 'R-100',
            'oem_consumption_rate': 30.45,
            'running_hours_source': 'DI',
            'litres_consumed_source': 'TL',
            'address': 1,
            'flowmeter_id': None,
            'model': 'Yamaha',
            'initial_totaliser_hours': 20,
            'site_id': 1,
        }
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)        

    def test_site_equipment_list(self):
        url = reverse('site_equipment_list')
        data = [
            65,
        ]
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)        

    def test_can_create_Equipment_with_FM_hours_source(self):
        url = reverse('equipment_list')
        data = {
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
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_can_create_Equipment_with_HYB_hours_source(self):
        url = reverse('equipment_list')
        data = {
            'name': 'Test Equipment',
            'product_id': 1,
            'oem': 'CAT',
            'model': 'R-100',
            'oem_consumption_rate': 30.45,
            'running_hours_source': 'HYB-FM',
            'litres_consumed_source': 'TL',
            'flowmeter_id': 1,
            'address': 1,
            'model': 'Yamaha',
            'initial_totaliser_hours': 20,
            'site_id': 1,
        }
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_can_create_Equipment_with_FM_litres_source(self):
        url = reverse('equipment_list')
        data = {
            'name': 'Test Equipment',
            'product_id': 1,
            'oem': 'CAT',
            'model': 'R-100',
            'oem_consumption_rate': 30.45,
            'running_hours_source': 'FM',
            'litres_consumed_source': 'FM',
            'flowmeter_id': 1,
            'address': None,
            'model': 'Yamaha',
            'initial_totaliser_hours': 20,
            'site_id': 1,
        }
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_Equipment_unique_validator(self):
        url = reverse('equipment_list')
        data = {
            'name': 'Test Equipment',
            'product_id': 1,
            'oem': 'CAT',
            'model': 'R-100',
            'oem_consumption_rate': 30.45,
            'running_hours_source': 'DI',
            'litres_consumed_source': 'TL',
            'address': 1,
            'model': 'Yamaha',
            'initial_totaliser_hours': 20,
            'site_id': 1,
        }
        self.client.post(url, data=data, format='json')
        #Should not be able to create anothe gen with address 1 within same site
        data = {
            'name': 'Test Equipment 2',
            'product_id': 1,
            'oem': 'CAT',
            'model': 'R-200',
            'oem_consumption_rate': 40.45,
            'running_hours_source': 'DI',
            'litres_consumed_source': 'TL',
            'address': 1,
            'model': 'Yamaha',
            'initial_totaliser_hours': 20,
            'site_id': 1,
        }
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_Equipment_zero_address_validator(self):
        #should not create Equipment with address 0, reserved for NEPA line
        url = reverse('equipment_list')
        data = {
            'name': 'Test Equipment',
            'product_id': 1,
            'oem': 'CAT',
            'model': 'R-100',
            'oem_consumption_rate': 30.45,
            'running_hours_source': 'DI',
            'litres_consumed_source': 'TL',
            'address': 0,
            'model': 'Yamaha',
            'initial_totaliser_hours': 20,
            'site_id': 1,
        }
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_Equipment_address_range_validator(self):
        #should not create Equipment with address > 3
        url = reverse('equipment_list')
        data = {
            'name': 'Test Equipment',
            'product_id': 1,
            'oem': 'CAT',
            'model': 'R-100',
            'oem_consumption_rate': 30.45,
            'running_hours_source': 'DI',
            'litres_consumed_source': 'TL',
            'address': 4,
            'model': 'Yamaha',
            'initial_totaliser_hours': 20,
            'site_id': 1,
        }
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_Equipment_DI_running_hours_source_validator(self):
        #Validation error if hours source is DI and no address is set 
        url = reverse('equipment_list')
        data = {
            'name': 'Test Equipment',
            'product_id': 1,
            'oem': 'CAT',
            'model': 'R-100',
            'oem_consumption_rate': 30.45,
            'running_hours_source': 'DI',
            'litres_consumed_source': 'TL',
            'address': None,
            'model': 'Yamaha',
            'initial_totaliser_hours': 20,
            'site_id': 1,
        }
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_Equipment_FM_running_hours_source_validator(self):
        #Validation error if hours source is FM and no flowmeter is selected
        url = reverse('equipment_list')
        data = {
            'name': 'Test Equipment',
            'product_id': 1,
            'oem': 'CAT',
            'model': 'R-100',
            'oem_consumption_rate': 30.45,
            'running_hours_source': 'FM',
            'litres_consumed_source': 'TL',
            'address': None,
            'model': 'Yamaha',
            'initial_totaliser_hours': 20,
            'site_id': 1,
        }
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_Equipment_HYB_running_hours_source_validator(self):
        #Validation error if hours source is HYB and no flowmeter or address is selected
        url = reverse('equipment_list')
        data = {
            'name': 'Test Equipment',
            'product_id': 1,
            'oem': 'CAT',
            'model': 'R-100',
            'oem_consumption_rate': 30.45,
            'running_hours_source': 'HYB-FM',
            'litres_consumed_source': 'TL',
            'address': 1,
            'flowmeter_id': None,
            'model': 'Yamaha',
            'initial_totaliser_hours': 20,
            'site_id': 1,
        }
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_Equipment_FM_litres_consumed_source_validator(self):
        #Validation error if litres consumed source is FM and no flowmeter is selected
        url = reverse('equipment_list')
        data = {
            'name': 'Test Equipment',
            'product_id': 1,
            'oem': 'CAT',
            'model': 'R-100',
            'oem_consumption_rate': 30.45,
            'running_hours_source': 'DI',
            'litres_consumed_source': 'FM',
            'address': 1,
            'flowmeter_id': None,
            'model': 'Yamaha',
            'initial_totaliser_hours': 20,
            'site_id': 1,
        }
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class EquipmentRetrieveTests(APITestCase):
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
        models.Products.objects.create(**{
            'Name': 'Petrol',
            'Code': 'PMS'
        })
        gen_1 = {
            'name': 'Test Equipment 1',
            'product_id': 1,
            'oem': 'CAT',
            'model': 'R-100',
            'oem_consumption_rate': 30.45,
            'running_hours_source': 'DI',
            'litres_consumed_source': 'TL',
            'address': 1,
            'model': 'Yamaha',
            'initial_totaliser_hours': 20,
            'site_id': 1,
        }
        gen_2 = {
            'name': 'Test Equipment 2',
            'product_id': 1,
            'oem': 'CAT',
            'model': 'R-200',
            'oem_consumption_rate': 30.45,
            'running_hours_source': 'DI',
            'litres_consumed_source': 'TL',
            'address': 2,
            'model': 'Yamaha',
            'initial_totaliser_hours': 20,
            'site_id': 1,
        }
        gen_3 = {
            'name': 'Test Equipment 3',
            'product_id': 1,
            'oem': 'CAT',
            'model': 'R-100',
            'oem_consumption_rate': 30.45,
            'running_hours_source': 'DI',
            'litres_consumed_source': 'TL',
            'address': 3,
            'model': 'Yamaha',
            'initial_totaliser_hours': 20,
            'site_id': 1,
        }
        models.Equipment.objects.create(**gen_1)
        models.Equipment.objects.create(**gen_2)
        models.Equipment.objects.create(**gen_3)
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

    def test_can_retrieve_all_Equipments(self):
        url = reverse('equipment_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 3)
    
    def test_retrieve_a_valid_Equipment(self):
        url = reverse('equipment_detail', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['data']['id'], 1)

    def test_retrieve_an_invalid_Equipment(self):
        url = reverse('equipment_detail', kwargs={'pk': 20})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class EquipmentUpdateTests(APITestCase):
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
        models.Products.objects.create(**{
            'Name': 'Petrol',
            'Code': 'PMS'
        })
        gen_1 = {
            'name': 'Test Equipment 1',
            'product_id': 1,
            'oem': 'CAT',
            'model': 'R-100',
            'oem_consumption_rate': 30.45,
            'running_hours_source': 'DI',
            'litres_consumed_source': 'TL',
            'address': 1,
            'model': 'Yamaha',
            'initial_totaliser_hours': 20,
            'site_id': 1,
        }
        models.Equipment.objects.create(**gen_1)
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

    def test_partial_update_Equipment(self):
        url = reverse('equipment_detail', kwargs={'pk':1})
        data = {
            'name': 'New Equipment'
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['data']['name'], 'New Equipment')

    def test_delete_Equipment(self):
        url = reverse('equipment_detail', kwargs={'pk':1})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(models.Equipment.objects.count(), 0)

    def test_reset_equipment_totalisers(self):
        url = reverse('equipment_reset_totaliser')
        data = {
            'equipment': 1,
            'totaliser_hours': 100,
            'totaliser_litres': 17.89
        }
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        eq = models.Equipment.objects.get(pk=1)
        self.assertEqual(eq.totaliser_hours, data['totaliser_hours'])
        self.assertEqual(eq.totaliser_litres, data['totaliser_litres'])


class EquipmentTankMappingTests(APITestCase):
    '''
    Test for the following features:
    - Get eligible tanks for an equipment
    - Map tanks to equipment
    - Get tanks mapped to an equipment
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
        gen_1 = {
            'name': 'Test Equipment 1',
            'product_id': 1,
            'oem': 'CAT',
            'model': 'R-100',
            'oem_consumption_rate': 30.45,
            'running_hours_source': 'DI',
            'litres_consumed_source': 'TL',
            'address': 1,
            'model': 'Yamaha',
            'initial_totaliser_hours': 20,
            'site_id': 1,
        }
        models.Equipment.objects.create(**gen_1)
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

    def test_get_eligible_tanks_for_an_equipment(self):
        url = reverse('equipment_eligible_tanks', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']), 3)

    def test_tank_to_equipment_mapping(self):
        url = reverse('equipment_map_tanks', kwargs={'pk': 1})
        data = {'Tank': [1,2,3]}
        response = self.client.put(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(models.Equipment.objects.get(pk=1).source_tanks.count(), 3)
    
    def test_get_all_tanks_mapped_to_an_equipment(self):
        #Map tanks
        url = reverse('equipment_map_tanks', kwargs={'pk': 1})
        data = {'Tank': [1,2,3]}
        self.client.put(url, data=data, format='json')
        url = reverse('equipment_tanks', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']['source_tanks']), 3)