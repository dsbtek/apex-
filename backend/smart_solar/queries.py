
from django.db import connection
from backend import models
from . import utils as log_utils

def update_energy_meter(self):
    query = f"""
            UPDATE smarteye_db.backend_smartsolardata 
            SET 
                mac_address="{self["mac_address"]}",
                inv_time_log="{self["inv_time_log"]}",
                battery_voltage="{self["battery_voltage"]}",
                solar_voltage="{self["solar_voltage"]}",
                grid_voltage="{self["grid_voltage"]}",
                output="{self["output"]}",
                previous_day_solar_unit="{self["previous_day_solar_unit"]}",
                solar_status="{self["solar_status"]}",
                today_total_solar="{self["today_total_solar"]}",
                today_solar_consume_for_charging="{self["today_solar_consume_for_charging"]}",
                solar_current="{self["solar_current"]}",
                grid_state="{self["grid_state"]}",
                today_solar_consume_for_load="{self["today_solar_consume_for_load"]}",
                total_charging_current="{self["total_charging_current"]}",
                today_battery_consume_for_load="{self["today_battery_consume_for_load"]}",
                discharging_current="{self["discharging_current"]}",
                today_grid_consume_for_charging="{self["today_grid_consume_for_charging"]}",
                today_load_on_grid="{self["today_load_on_grid"]}",
                instantaneous_solar_power="{self["instantaneous_solar_power"]}",
                load_on="{self["load_on"]}",
                location="{self["location"]}"
            WHERE id = {self['id']} """
    with connection.cursor() as c:
        c.execute(query)
        # data = c.fetchone()
    return "Record Updated successfully"

def update_invater(self):
    query = f"""
            UPDATE smarteye_db.backend_smartsolardata 
            SET 
                mac_address="{self["mac_address"]}",
                energy_time_log="{self["energy_time_log"]}",
                output_voltage="{self["output_voltage"]}",
                output_current="{self["output_current"]}",
                output_power="{self["output_power"]}",
                output_energy="{self["output_energy"]}",
                device_type="{self["device_type"]}",
                location="{self["location"]}"
            WHERE id = {self['id']} """
    with connection.cursor() as c:
        c.execute(query)
        # data = c.fetchone()
    return "Record Updated successfully"