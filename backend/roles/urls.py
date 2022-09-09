from django.urls import path
from . import views

urlpatterns = [

	path('user_roles/', views.UserRoleList.as_view(), name='user_role_list'),
	path('roles/', views.AllRoleList.as_view(), name='all_role_list')
]
