from django.urls import path
from . import views

urlpatterns = [
	path('stockreport/download/', views.DownloadStockReport.as_view(), name='stock_report'),
	path('report/consumption/', views.ConsumptionReport.as_view(), name='consumption_report'),
	path('report/delivery/', views.DeliveryReport.as_view(), name='delivery_report'),
]
