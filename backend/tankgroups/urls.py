from django.urls import path
from . import views

urlpatterns = [

	path('tankgroups/', views.TankGroupList.as_view(), name='tankgroup_list'),
	path('tankgroups/min/', views.AllTankGroupList.as_view(), name='all_tankgroup_list'),
	path('tankgroups/<int:pk>/', views.TankGroupDetail.as_view(), name='tankgroup_detail'),
	path('tankgroups/by_company/<int:pk>/', views.TankGroupByCompany.as_view(), name='tankgroup_by_company'),
	path('tankgroups/by_companies/',
	     views.TankGroupByCompanies.as_view(), name='tankgroup_by_many_company'),
	path('tankgroups/<int:pk>/eligible_tanks/', views.EligibleTanks.as_view(), name='tankgroup_eligible_tanks'),
	path('tankgroups/<int:pk>/tanks/', views.TankGroupTanks.as_view(), name='tankgroup_tanks'),
	path('tankgroups/<int:pk>/tanks/map', views.TankGroupMapTanks.as_view(), name='tankgroup_map_tanks'),
]
