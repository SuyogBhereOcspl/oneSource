from django.contrib import admin
from .models import Vehicle

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('vehicle_no', 'name_of_supplier', 'material', 'reporting_date', 'unloading_date', 'status')
    list_filter = ('status', 'reporting_date', 'unloading_date', 'name_of_supplier')
    search_fields = ('vehicle_no', 'name_of_supplier', 'material', 'invoice')
    ordering = ('-record_date',)  # Orders by the most recent record first
    readonly_fields = ('unloading_days',)  # Prevent manual changes in unloading_days
