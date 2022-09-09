from django.urls import path
from . import views

urlpatterns = [

    path('tanks/', views.TankList.as_view(), name='tank_list'),
    path('tanks/min/', views.AllTankList.as_view(), name='all_tank_list'),
    path('tanks/<int:pk>', views.TankDetail.as_view(), name='tank_detail'),
    path('tanks/toggle_activation/<int:pk>/', views.TankActivationDetail.as_view(), name='tank_activation'),
    path('tanks/by_company/<int:pk>',
         views.TankCompanyList.as_view(), name='tanks_by_company'),
    path('tanks/by_companies/',
         views.TankCompanies.as_view(), name='tanks_by_many_company'),
    path('tanks/by_site/<int:pk>',
         views.TankSiteList.as_view(), name='tanks_by_site'),
    path('tanks/by_sitegroup/', views.TankSitegroupList.as_view(),
         name='tanks_by_sitegroup'),
    path('site/tanks/', views.GetTankIDs.as_view(), name='site_tank_ids'),
    #path('tanks/chart', views.CalibrationChart.as_view()),
    path('tanks/chart-template', views.CalibrationChartTemplate.as_view(), name='chart_template'),
    path('tanks/chart/<int:pk>', views.GetCalibrationChart.as_view(), name='read_tank_chart'),
    path('tanks/sitetanklist/', views.GetTankList.as_view(), name='site_tank_list'),
    path('tanks/tankgrouplist/', views.GetTankFromTankGroup.as_view(), name='tankgroup_tank_list')
]
