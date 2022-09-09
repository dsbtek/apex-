from backend import models
'''
All Devices accessing remote config
are confirmed to be connected to a site.
It is redundant to check for availability again
'''
class RemoteConfig:
	def __init__(self, device):
		self.device = device
		self.config_objects = [
			TankDetailsConfig(self.device),
			DeviceConfig(self.device),
			FlowmeterConfig(self.device),
			PowermeterConfig(self.device)
		]
		self.config_payload = {}
	
	def get_configurations(self):
		for obj in self.config_objects:
			config = obj.config()
			self.config_payload[config[0]] = config[1]
		return self.config_payload


class TankDetailsConfig:
    """
    Configuration for tanks connected to the device.
	All tanks connected to the device are returned
    """
    def __init__(self, device):
        self.device = device
        self.name = "tank_details"

    def config(self):
        #tank_details = self.device.tank_config_details
	    site = self.device.get_site
	    tank_details = list(site.tanks.values('Name', 'Control_mode', 'Tank_controller',
		'Controller_polling_address', 'Tank_index', 'Tank_height'))
	    return (self.name, tank_details)

class FlowmeterConfig:
	"""
	Configuration for all flowmeters connected to the device
	"""
	def __init__(self, device):
		self.device = device
		self.name = "flowmeter_details"

	def config(self):
		site = self.device.get_site
		flowmeter_details = list(site.flowmeters.values('serial_number', 'meter_type', 'address', 'equipment'))
		return (self.name, flowmeter_details)


class PowermeterConfig:
	"""
	Configuration for all powermeters connected to the device
	"""
	def __init__(self, device):
		self.device = device
		self.name = "powermeter_details"

	def config(self):
		site = self.device.get_site
		powermeter_details = list(site.powermeters.values('serial_number', 'meter_type', 'address', 'equipment'))
		return (self.name, powermeter_details)

class DeviceConfig:
    """
    Configuration for device transmit interval and active status
    """
    def __init__(self, device):
	    self.device = device
	    self.name = "device_details"

    def config(self):
	    details = {
			"transmit_interval": self.device.transmit_interval,
			"active":self.device.Active,
		}
		#add devcice expected version to the payload
	    return (self.name, details)