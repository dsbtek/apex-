from django.urls import path
from . import views

urlpatterns = [
    path('genhours_config/', views.GenHoursConfig.as_view(), name='site_genhours_config'),
    path('genhours_config/<int:pk>', views.GenHoursConfigDetail.as_view(), name='site_genhours_config_detail'),
]