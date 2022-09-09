from django.urls import path, include
from rest_framework.urlpatterns import format_suffix_patterns

urlpatterns = [
	
	path('', include('backend.authentication.urls')),
	path('', include('backend.users.urls')),
	path('', include('backend.companies.urls')),
	path('', include('backend.devices.urls')),
	path('', include('backend.sites.urls')),
	path('', include('backend.roles.urls')),
	path('', include('backend.tanks.urls')),
	path('', include('backend.smarteye_logs.urls')),
	path('', include('backend.tankgroups.urls')),
	path('auth/', include('backend.authentication.urls')),
	path('', include('backend.trends.urls')),
	path('', include('backend.reports.urls')),
	path('', include('backend.version.urls')),
	path('', include('backend.probes.urls')),
	path('', include('backend.genhours_logs.urls')),
	path('', include('backend.equipments.urls')),
	path('', include('backend.flowmeters.urls')),
	path('', include('backend.genhours_maintenance.urls')),
	path('', include('backend.genhours_config.urls')),
	path('smartpump/', include('backend.smart_pump.urls')),
	path('smartsolar/', include('backend.smart_solar.urls')),
	path('public/', include('backend.public_endpoints.urls')),
	path('audit/', include('backend.audit_logs.urls')),
]

# urlpatterns = format_suffix_patterns(urlpatterns)
