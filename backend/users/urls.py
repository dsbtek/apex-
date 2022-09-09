from django.urls import path
from . import views

urlpatterns = [

	path('users/', views.UserList.as_view(), name='user_list'),
	path('users/min/', views.AllUserList.as_view(), name='all_user_list'),
	path('users/<int:pk>', views.UserDetail.as_view(), name='user_detail'),
	path('users/by_companies/', views.UserByCompanies.as_view(), name='user_by_many_company'),
	path('users/by_company/<int:pk>', views.UserByCompany.as_view(), name='user_by_company'),
	path('users/toggle_activation/<int:pk>', views.UserActivationDetail.as_view(), name='user_activation'),
]

