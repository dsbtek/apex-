from django.urls import path
from . import views

urlpatterns = [

    path('audit_logs/', views.AllLogList.as_view(), name='audit_log_list'),
    path('audit_logs_timestamp/', views.AuditLogTimeStamp.as_view(), name='audit_logs_timestamp'),

]

