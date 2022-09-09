import datetime
from django.shortcuts import get_object_or_404
from backend import models
from backend.smart_solar.queries import update_energy_meter, update_invater
# from backend.smart_solar.queries import update_energy_meter



def get_device_type_and_time_log(data):
    device_type = data['device_type']
    if device_type == "inverter":
        current_log_time = datetime.datetime.strptime(str(data['inv_time_log']),  "%Y-%m-%d %H:%M:%S") or "00:00:00 00:00:00"
        minute =current_log_time = datetime.datetime.strptime(str(data['inv_time_log']),  "%Y-%m-%d %H:%M:%S").minute or "00:00:00 00:00:00"
        second = current_log_time = datetime.datetime.strptime(str(data['inv_time_log']),  "%Y-%m-%d %H:%M:%S").second or "00:00:00 00:00:00"
        return [device_type, current_log_time, minute, second]
    elif device_type == "energy meter":
        current_log_time = datetime.datetime.strptime(str(data['energy_time_log']),  "%Y-%m-%d %H:%M:%S") or "00:00:00 00:00:00"
        minute =current_log_time = datetime.datetime.strptime(str(data['energy_time_log']),  "%Y-%m-%d %H:%M:%S").minute or "00:00:00 00:00:00"
        second = current_log_time = datetime.datetime.strptime(str(data['energy_time_log']),  "%Y-%m-%d %H:%M:%S").second or "00:00:00 00:00:00"
        return [device_type, current_log_time, minute, second]
    
def get_mac_address_in_devices(data):
    mac_address = data['mac_address']
    if mac_address:
        get_object_or_404(models.Devices, Device_unique_address=mac_address)
    return mac_address
    
def get_energy_meter_or_inverter(mac_address,device_type,prev_time_log,minute, second,data):
    if device_type == "inverter":
        check_device_in_solar = models.SmartSolarData.objects.all().filter(mac_address=mac_address, device_type="energy meter").values()
        if check_device_in_solar:
            id = check_device_in_solar[0]['id']
            if id:
                # solar_time_log = datetime.datetime.strptime(str(check_device_in_solar.energy_time_log), "%Y-%m-%d %H:%M:%S") or "00:00:00 00:00:00"
                tm1 = datetime.datetime.strptime(str(check_device_in_solar[0]['energy_time_log']), "%Y-%m-%d %H:%M:%S").minute or "00:00:00 00:00:00"
                ts2 = datetime.datetime.strptime(str(check_device_in_solar[0]['energy_time_log']), "%Y-%m-%d %H:%M:%S").second or "00:00:00 00:00:00"
                dif_min = tm1 - minute
                dif_sec = ts2 - second
                if dif_min < 3 and dif_sec <20:
                    data["id"]=id
                    update_rec = update_energy_meter(data)
                    return update_rec 
                else:
                    return None
    elif device_type == "energy meter":
        check_device_in_solar = models.SmartSolarData.objects.filter(mac_address=mac_address, device_type="inverter").values()
        if check_device_in_solar:
            id = check_device_in_solar[0]['id']
            if id:
                # solar_time_log = datetime.datetime.strptime(str(check_device_in_solar.inv_time_log), "%Y-%m-%d %H:%M:%S") or "00:00:00 00:00:00"
                tm1 = datetime.datetime.strptime(str(check_device_in_solar[0]['inv_time_log']), "%Y-%m-%d %H:%M:%S").minute or '01/08/2022 00:00:00.000'
                ts2 = datetime.datetime.strptime(str(check_device_in_solar[0]['inv_time_log']), "%Y-%m-%d %H:%M:%S").second or '01/08/2022 00:00:00.000'
                dif_min = tm1 - minute
                dif_sec = ts2 - second
                if dif_min < 3 and dif_sec <20:   
                    data["id"]=id
                    update_rec = update_invater(data)
                    return update_rec 
                else:
                    return None
            