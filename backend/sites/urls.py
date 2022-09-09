from django.urls import path
from . import views

urlpatterns = [

	path('sites/', views.SiteList.as_view(), name='site_list'),
	path('sites/min/', views.E360SiteList.as_view(), name='all_site_list'),
	path('sites/<int:pk>', views.SiteDetail.as_view(), name='site_detail'),
	path('sites/by_company/<int:pk>', views.SiteByCompanyList.as_view(), name='site_by_company'),
	path('sites/by_companies/',
	     views.SiteByCompanies.as_view(), name='site_by_many_company'),
	path('sites/<int:pk>/toggle_activation/', views.SiteActivationDetail.as_view(), name='site_activation'),
	path('sites/<int:pk>/location_activation/', views.SiteLocationActivationToggle.as_view(), name='site_location_activation_toggler'),

]
