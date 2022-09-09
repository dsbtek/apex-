from django.urls import path
from . import views

urlpatterns = [
	path('device_generator/', views.GenerateDevice.as_view(), name='generate_device'),
	path('devices/', views.DeviceList.as_view(), name='device_list'),
	path('devices/min/', views.AllDeviceList.as_view(), name='all_device_list'),
	path('devices/<int:pk>', views.DeviceDetail.as_view(), name='device_detail'),
	path('devices/by_company/<int:pk>', views.DeviceByCompanyList.as_view(), name='device_by_company'),
	path('devices/by_companies/',
	     views.DeviceByCompanies.as_view(), name='device_by_many_company'),
	path('devices/for_pump/by_company/<int:pk>', views.PumpDeviceByCompanyList.as_view(), name='pump_device_by_company'),
	path('devices/<int:pk>/company/<int:id>/activate/', views.DeviceActivationDetail.as_view(), name='device_activation'),
	path('devices/registered/online_status/', views.RegisteredDevicesOnlineStatusRedis.as_view(), name='registered_devices_heartbeat_redis'),
	# path('devices/redis/online_status/', views.RegisteredDevicesOnlineStatusRedis.as_view(), name='registered_devices_heartbeat_redis'),
	path('devices/adc_sensor_config/', views.ADC_Sensor_Configuration.as_view(), name='adc_sensor_config'),
	path('devices/tank_config_details/', views.Tank_Configuration_Details.as_view(), name='tank_config_details'),
	path('devices/remote_config/', views.RemoteConfigView.as_view(), name="remote_config")
]

