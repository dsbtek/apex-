from django.urls import path
from . import views

urlpatterns = [
	path('login/', views.Login.as_view(), name='login'),
	path('password_reset/request', views.PasswordResetRequest.as_view(), name='password_reset'),
	path('password_reset_confirm/<int:uid>/<token>', views.PasswordResetConfirm.as_view(), name='password_reset_confirm'),
	path('password_reset/', views.PasswordChange.as_view(), name='password_change')
]

