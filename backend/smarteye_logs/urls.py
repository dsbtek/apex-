from django.urls import path
from . import views

urlpatterns = [
	path('data_logger/', views.DataLogger.as_view(), name='data_logger'),
	path('delivery_logger/', views.DeliveryLogger.as_view(), name='tls_delivery_logger'),
	path('sensor_data_logger/', views.SensorDataLogger.as_view(), name='sensor_data_logger'),
	path('smarthub/data_logger/', views.SmarthubLogsLogger.as_view(), name='smarthub_data_logger'),
	path('smarthub/deliveries_logger/', views.SmarthubDeliveriesLogger.as_view(), name='smarthub_deliveries_logger'),
	path('revampedtanklogs/', views.RevampedTankReadings.as_view()),
	path('tanklogs/', views.TankReadings.as_view()),
	path('anomaly/', views.AnomalyTankReadingReport.as_view()), # Reading anomaly
	path('revampedtankreading/latest/', views.RevampedCurrentTankDetails.as_view(), name="revamped_latest_tank_reading"),
	path('tankreading/latest/', views.CurrentTankDetails.as_view(), name="latest_tank_reading"),
	path('modifiedtankreading/latest/', views.ModifiedCurrentTankDetails.as_view(), name="modified_latest_tank_reading"),
	path('tankgrouptanklogs/', views.TankReadingsForTankGroups.as_view()),
	path('tankreading/tankgroup/latest/', views.CurrentTankDetailsForTankgroup.as_view()),
	path('revampedtankreading/tankgroup/latest/', views.RevampedCurrentTankDetailsForTankgroup.as_view()),
	path('tank/<int:pk>/recent-logs/', views.SpecificTankReading.as_view()),
	path('tank_map/', views.TankMap.as_view(), name='tank_map'),
]
