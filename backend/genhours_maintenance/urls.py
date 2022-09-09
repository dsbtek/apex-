from django.urls import path
from . import views

urlpatterns = [
    path('maintenance_config/', views.NewMaintenanceConfig.as_view(), name='equipment_maintenance_config'),
    path('maintenance_config/<int:pk>', views.MaintenanceConfigDetail.as_view(), name='equipment_maintenance_config_detail'),
    path('maintenance_info/', views.NewMaintenanceInfo.as_view(), name='equipment_maintenance_info'),
    path('maintenance_info_records/equipment/<int:pk>', views.MaintenanceInfoRecords.as_view(), name='equipment_maintenance_info_records'),
    path('maintenance_summary/equipment/<int:pk>', views.EquipmentMaintenanceSummary.as_view(), name='equipment_maintenance_summary')
]