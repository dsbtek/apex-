from django.urls import path
from . import views

urlpatterns = [
	path('probes/', views.ProbeList.as_view(), name='probe_list'),
    path('probe/<int:pk>/', views.ProbeDetails.as_view(), name='probe_details'),
    path('probe_chart/<int:pk>/', views.ProbeChart.as_view(), name='read_probe_chart'),
]