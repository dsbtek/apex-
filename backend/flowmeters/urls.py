from django.urls import path
from . import views


urlpatterns = [
    path('flowmeters/', views.FlowmeterList.as_view(), name='flowmeter_list'),
    path('flowmeters/<int:pk>', views.FlowmeterDetail.as_view(), name='flowmeter_detail'),
    path('flowmeters/<int:pk>/site/<int:id>/activate/', views.FlowmeterActivationDetail.as_view(), name='flowmeter_activation'),
    path('flowmeters/by_site/<int:pk>', views.FlowmeterBySiteList.as_view(), name='flowmeter_by_site'),
    path('flowmeters/by_company/<int:pk>', views.FlowmeterCompanyList.as_view(), name='flowmeter_by_company'),
    path('flowmeters/by_companies/', views.FlowmeterCompanies.as_view(), name='flowmeter_by_many_company')
]