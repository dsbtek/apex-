from django.urls import path
from . import views


urlpatterns = [
    path('equipments/', views.EquipmentList.as_view(), name='equipment_list'),
    path('equipments/<int:pk>', views.EquipmentDetail.as_view(), name='equipment_detail'),
    path('equipments/by_company/<int:pk>', views.EquipmentCompanyList.as_view(), name='equipment_by_company'),
    path('equipments/by_companies/',
         views.EquipmentCompanies.as_view(), name='equipment_by_many_company'),
    path('equipments/by_site/<int:pk>', views.EquipmentSiteList.as_view(), name='equipment_by_site'),
    path('equipments/by_sitegroup/', views.EquipmentSitegroupList.as_view(), name='equipment_by_sitegroup'),
    path('equipments/<int:pk>/eligible_tanks/', views.EligibleTanks.as_view(), name='equipment_eligible_tanks'),
    path('equipments/<int:pk>/tanks/', views.EquipmentTanks.as_view(), name='equipment_tanks'),
	path('equipments/<int:pk>/tanks/map', views.EquipmentMapTanks.as_view(), name='equipment_map_tanks'),
    path('equipments/reset_totalisers/', views.EquipmentResetTotalisers.as_view(), name='equipment_reset_totaliser'),
    path('equipments/equipmentlist/', views.SitesEquipmentList.as_view(), name='site_equipment_list')
]
