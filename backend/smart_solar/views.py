import datetime
from http.client import HTTPResponse
from rest_framework.views import APIView
from . import serializer
from .. import utils
from . import utils as u
from rest_framework import status
from backend import models
from django.shortcuts import get_object_or_404
from dateutil import parser


class SolarDataLogger(APIView):
    permission_classes = ()
    authentication_classes = ()
    serializer_class = serializer.SolarDataSerializer
    def post(self, request):
        data=request.data
        for item in range(len(data)):
            device_type, prev_time_log, minute, second = u.get_device_type_and_time_log(data[item])
            mac_address = u.get_mac_address_in_devices(data[item])
            if device_type:
                data_set = u.get_energy_meter_or_inverter(mac_address, device_type,prev_time_log,minute,second,data[item])
                if data_set:
                    # serialized_data = self.serializer_class(data=data_set)
                    # if not serialized_data.is_valid():
                    #     return utils.CustomResponse.Failure(serialized_data.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
                    # serialized_data.update()
                    return utils.CustomResponse.Success(data_set, status=status.HTTP_201_CREATED)
                else:
                    serialized_data = self.serializer_class(data=request.data[item])
                    if not serialized_data.is_valid():
                        return utils.CustomResponse.Failure(serialized_data.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
                    serialized_data.save()
                    return utils.CustomResponse.Success(serialized_data.data, status=status.HTTP_201_CREATED)           
            else:
                return utils.CustomResponse.Failure("No device found", status=status.HTTP_422_UNPROCESSABLE_ENTITY)





        # for item in range(len(data)):
        #     #get the device mac address
        #     mac_address = data['mac_address']

        #     #get the device type in order to know where the request is coming from: either inverter or energy meter
        #     device_type = data['device_type']
        #     if device_type== "inverter":
        #         current_log_time = datetime.datetime.strptime(str(data['inv_time_log']),  "%Y-%m-%d %H:%M:%S") or "00:00:00 00:00:00"
        #     else:
        #         current_log_time = datetime.datetime.strptime(str(data['energy_time_log']),  "%Y-%m-%d %H:%M:%S") or "00:00:00 00:00:00"

        #     if mac_address:
        #         this_device = get_object_or_404(models.Devices, Device_unique_address=mac_address)
        #         if this_device:
        #             #check if the device is either inverter or energy meter and check the
        #             #solar db in order to compare the time difference if is not greater
        #             #than 2 minute and the second is not greater than 20 second we update the
        #             # record else we create new record 
        #             if device_type == "inverter":
        #                 check_device_in_solar = models.SmartSolarData.objects.all().filter(mac_address=mac_address, device_type="energy meter").first()
        #                 id = check_device_in_solar
        #                 if id:
        #                     solar_time_log = datetime.datetime.strptime(str(check_device_in_solar.energy_time_log), "%Y-%m-%d %H:%M:%S") or "00:00:00 00:00:00"
        #                     time_delta = solar_time_log - current_log_time
        #                     get_minutes_second = divmod(time_delta.total_seconds(), 60)
        #                     minutes = abs(get_minutes_second[0])
        #                     print(solar_time_log, current_log_time)
        #                     print(time_delta, minutes)
        #                     second = abs(get_minutes_second[1])
        #                     print(second)
        #                     if minutes < 3 and second <20:
        #                         data_ = {
        #                                 "id": id,
        #                                 "mac_address": data["mac_address"],
        #                                 "inv_time_log": data["inv_time_log"],
        #                                 "battery_voltage": data["battery_voltage"],
        #                                 "solar_voltage": data["solar_voltage"],
        #                                 "grid_voltage": data["grid_voltage"],
        #                                 "output": data["output"],
        #                                 "previous_day_solar_unit": data["previous_day_solar_unit"],
        #                                 "solar_status": data["solar_status"],
        #                                 "today_total_solar": data["today_total_solar"],
        #                                 "today_solar_consume_for_charging": data["today_solar_consume_for_charging"],
        #                                 "solar_current": data["solar_current"],
        #                                 "grid_state": data["grid_state"],
        #                                 "today_solar_consume_for_load": data["today_solar_consume_for_load"],
        #                                 "total_charging_current": data["total_charging_current"],
        #                                 "today_battery_consume_for_load": data["today_battery_consume_for_load"],
        #                                 "discharging_current": data["discharging_current"],
        #                                 "today_grid_consume_for_charging": data["today_grid_consume_for_charging"],
        #                                 "today_load_on_grid": data["today_load_on_grid"],
        #                                 "instantaneous_solar_power": data["instantaneous_solar_power"],
        #                                 "load_on": data["load_on"],
        #                                 "location": data["location"]
        #                         }
        #                         serialized_data = self.serializer_class(data=data_, many=True)
        #                         if not serialized_data.is_valid():
        #                             return utils.CustomResponse.Failure(serialized_data.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        #                         serialized_data.save()
        #                         return utils.CustomResponse.Success(serialized_data.data, status=status.HTTP_201_CREATED)
        #                     else:
        #                         serialized_data = self.serializer_class(data=request.data)
        #                         if not serialized_data.is_valid():
        #                             return utils.CustomResponse.Failure(serialized_data.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        #                         serialized_data.save()
        #                         return utils.CustomResponse.Success(serialized_data.data, status=status.HTTP_201_CREATED)           

        #             elif device_type == "energy meter":
        #                 check_device_in_solar = models.SmartSolarData.objects.all().filter(mac_address=mac_address, device_type="inverter").first()
        #                 id = check_device_in_solar
        #                 if id:
        #                     solar_time_log = datetime.datetime.strptime(str(check_device_in_solar.inv_time_log), "%Y-%m-%d %H:%M:%S") or "00:00:00 00:00:00"
        #                     time_delta = solar_time_log - current_log_time
        #                     get_minutes_second = divmod(time_delta.total_seconds(), 60)
        #                     minutes = abs(get_minutes_second[0])
        #                     print(solar_time_log, current_log_time)
        #                     print(time_delta, minutes)
        #                     second = abs(get_minutes_second[1])
        #                     print(second)
        #                     if minutes < 3 and second <20:
        #                         data_ = {
        #                                 "id": id,
        #                                 "mac_address": data["mac_address"],
        #                                 "energy_time_log": data["energy_time_log"],
        #                                 "output_voltage": data["output_voltage"],
        #                                 "output_current": data["output_current"],
        #                                 "output_power": data["output_power"],
        #                                 "output_energy": data["output_energy"],
        #                                 "device_type": data["device_type"],
        #                                 "location": data["location"]

        #                         }
        #                         serialized_data = self.serializer_class(id, data=data_)
        #                         if not serialized_data.is_valid():
        #                             return utils.CustomResponse.Failure(serialized_data.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        #                         serialized_data.save()
        #                         return utils.CustomResponse.Success(serialized_data.data, status=status.HTTP_201_CREATED)
        #                     else:
        #                         serialized_data = self.serializer_class( data=request.data)
        #                         if not serialized_data.is_valid():
        #                             return utils.CustomResponse.Failure(serialized_data.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        #                         serialized_data.save()
        #                         return utils.CustomResponse.Success(serialized_data.data, status=status.HTTP_201_CREATED)
        #                 else:
        #                     serialized_data = self.serializer_class( data=request.data)
        #                     if not serialized_data.is_valid():
        #                         return utils.CustomResponse.Failure(serialized_data.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        #                     serialized_data.save()
        #                     return utils.CustomResponse.Success(serialized_data.data, status=status.HTTP_201_CREATED)                      
        #     else:
                        
        #         return utils.CustomResponse.Failure("No device found", status=status.HTTP_422_UNPROCESSABLE_ENTITY)
    