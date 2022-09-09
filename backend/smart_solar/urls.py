
from django.urls import path
from . import views

urlpatterns = [
    path('solar_data_logger/', views.SolarDataLogger.as_view(),
         name='solar_data_logger'),
]
