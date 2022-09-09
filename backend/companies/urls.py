from django.urls import path
from . import views

urlpatterns = [
    
	path('companies/groups/', views.CompanyGroupList.as_view(), name='companygroup_list'),
	path('companies/groups/<int:pk>',
	     views.CompanyGroupDetail.as_view(), name='companygroup_detail'),
 	path('companies/groups/toggle_activation/<int:pk>',
         views.CompanyGroupActivationDetail.as_view(), name='company_group_activation'),
	path('companies/min/', views.AllCompanyList.as_view(), name='all_company_list'),
	path('companies/', views.CompanyList.as_view(), name='company_list'),
	path('companies/multiple/', views.MultipleCompanyList.as_view(), name='many_company_detail'),
	path('companies/<int:pk>', views.CompanyDetail.as_view(), name='company_detail'),
	path('companies/<int:pk>/toggle_activation/', views.CompanyActivationDetail.as_view(), name='company_activation'),
	

]

