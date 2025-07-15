from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from .models import Credentials

class CredentialsResource(resources.ModelResource):
    class Meta:
        model = Credentials
        # Optionally specify fields or exclude fields
        # fields = ('location', 'device', 'lan_ip', 'wan_ip')
        # import_id_fields = ('id',)

@admin.register(Credentials)
class CredentialsAdmin(ImportExportModelAdmin):
    resource_class = CredentialsResource
    list_display = [
        'location', 'device', 'lan_ip', 'wan_ip', 'port_no', 'frwd_to', 'url',
        'user_name', 'old_password', 'new_password', 'status', 'action_date', 'expiry_on'
    ]
    list_filter = ['location', 'status', 'action_date', 'expiry_on']
    search_fields = ['device', 'lan_ip', 'wan_ip', 'url', 'user_name']
    readonly_fields = ['action_date']
