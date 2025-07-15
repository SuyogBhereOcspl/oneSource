from django.contrib import admin
from .models import GeneralEffluent


# Register your models here.
@admin.register(GeneralEffluent)
class GeneralEffluentAdmin(admin.ModelAdmin):
    list_display = ('id', 'record_date', 'location', 'effluent_nature', 'actual_quantity')
    list_filter = ('location', 'effluent_nature', 'record_date')
    search_fields = ('location', 'effluent_nature')
    ordering = ('-record_date',)