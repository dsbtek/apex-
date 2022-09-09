from django.urls import path
from . import views

urlpatterns = [

	path('versions/', views.VersionList.as_view(), name='version_list'),
	path('firmware/update/', views.DeviceFirmwareUpdate.as_view(), name='update_devices_firmware'),
	path('firmware/devices/', views.DeviceFirmwareList.as_view(), name='device_firmware_list'),
]

