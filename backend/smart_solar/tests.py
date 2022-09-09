# from rest_framework.test import APITestCase
# from rest_framework import statuss



# class CreateSolarData(APITestCase):
#     def setUp(self):

#         company_data = {
#             "Name": "Test Company 1",
#             "Country": "Nigera",
#             "State": "Lagos",
#             "City": "Ikeja",
#             "Address": "1, Ayo way.",
#             "Company_type": "Multinational",
#             "Contact_person_name": "Muhammad Salihu",
#             "Contact_person_designation": "Software Engineer",
#             "Contact_person_mail": "muhammad.salihu@smartflowtech",
#             "Contact_person_phone": "08111084200"
#         }
#         devices_1 = {
#                     "Name": "PIC-0001",
#                     "Device_unique_address": "b8:27:eb:d9:ea:ea:00:00",
#                     "Company_id": 1,
#                     "Phone_number": "07038185641",
#                     "Deleted_at": "2022-08-30 11:39:01.693",
#                     "transmit_interval": 0,
#                     "Active": True,
#                     "ForPump": True,
#                     "Used": True
#                 }
#         devices_2 =  {
#                     "Name": "PIC-0002",
#                     "Device_unique_address": "b8:27:eb:55:74:d1",
#                     "Company_id": 1,
#                     "Phone_number": "07038185641",
#                     "Deleted_at": "2022-08-30 11:39:01.693",
#                     "transmit_interval": 0,
#                     "Active": True,
#                     "ForPump": True,
#                     "Used": True
#                 }

#         models.Companies.objects.create(**company_data)
#         models.Devices.objects.create(**devices_1)
#         models.Devices.objects.create(**devices_2)
        
#     def test_create_smartsolar_data(self):
#         url = reverse('solar_data_logger')
#         data = [
#                 {
#                     "mac_address":"b8:27:eb:d9:ea:ea:00:00", 
#                     "log_time":"2022-03-11T17:24:18", 
#                     "battery_voltage":"23.00", 
#                     "solar_voltage":"23.00", 
#                     "grid_voltage":"23.00",
#                     "output":"23.00", 
#                     "previous_day_solar_unit":"23.00", 
#                     "solar_status":"23.00", 
#                     "today_total_solar":"23.00", 
#                     "today_solar_consume_for_charging":"23.00", 
#                     "solar_current":"23.00", 
#                     "grid_state":"23.00", 
#                     "today_solar_consume_for_load":"23.00", 
#                     "total_charging_current":"23.00", 
#                     "today_battery_consume_for_load":"23.00", 
#                     "discharging_current":"23.00", 
#                     "today_grid_consume_for_charging":"23.00", 
#                     "today_load_on_grid":"23.00", 
#                     "instantaneous_solar_power":"23.00", 
#                     "load_on":"23.00", 
#                     "output_voltage":"23.00", 
#                     "output_current":"23.00", 
#                     "output_power":"23.00", 
#                     "output_energy":"23.00"
#                     },
#                     {
#                     "mac_address":"b8:27:eb:55:74:d1", 
#                     "log_time":"2022-03-11T17:24:18", 
#                     "battery_voltage":"23.00", 
#                     "solar_voltage":"23.00", 
#                     "grid_voltage":"23.00",
#                     "output":"23.00", 
#                     "previous_day_solar_unit":"23.00", 
#                     "solar_status":"23.00", 
#                     "today_total_solar":"23.00", 
#                     "today_solar_consume_for_charging":"23.00", 
#                     "solar_current":"23.00", 
#                     "grid_state":"23.00", 
#                     "today_solar_consume_for_load":"23.00", 
#                     "total_charging_current":"23.00", 
#                     "today_battery_consume_for_load":"23.00", 
#                     "discharging_current":"23.00", 
#                     "today_grid_consume_for_charging":"23.00", 
#                     "today_load_on_grid":"23.00", 
#                     "instantaneous_solar_power":"23.00", 
#                     "load_on":"23.00", 
#                     "output_voltage":"23.00", 
#                     "output_current":"23.00", 
#                     "output_power":"23.00", 
#                     "output_energy":"23.00"
#                     }
#         ]
#         response = self.client.post(url, data, format='json')
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#         self.assertEqual(models.SmartSolarData.objects.count(), 2)
