from django.urls import path
from . import views

urlpatterns = [

	path('tanks/inventory/', views.GetTankInventory.as_view()),
	path('tanks/products/', views.GetTankProductList.as_view()),
	path('tanks/reports/daily/', views.GetDailyConsumptionReport.as_view()),
	path('tanks/deliveries/', views.GetDeliveriesByTanks.as_view()),
	path('token/<int:pk>/', views.GenerateAPIToken.as_view()),
	# path('devices/online_status/', views.GetOnlineDevices.as_view())
]
