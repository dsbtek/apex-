from django.urls import path
from . import views

urlpatterns = [

	path('trends/', views.TrendReadings.as_view(), name="trends"),
	
]
