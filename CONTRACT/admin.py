
from django.contrib import admin
from .models import (
    DepartmentManpowerRequirement,
    ContractorManpowerAttendance,
    ContractorWorker
)
from import_export.admin import ImportExportModelAdmin
from import_export import resources


@admin.register(DepartmentManpowerRequirement)
class DepartmentManpowerRequirementAdmin(admin.ModelAdmin):
    list_display = ("department_name", "required_manpower")
    search_fields = ("department_name",)
    list_editable = ("required_manpower",)
    ordering = ("department_name",)





class ContractorWorkerResource(resources.ModelResource):
    class Meta:
        model = ContractorWorker
        # Optionally specify fields to import/export, or exclude fields
        # fields = ('id', 'date', 'contractor_name', 'shift', 'location', 'department', 'emp_count')
        # import_id_fields = ('id',)  # If you want to match on 'id' for updates

@admin.register(ContractorWorker)
class ContractorWorkerAdmin(ImportExportModelAdmin):
    resource_class = ContractorWorkerResource
    list_display = ('date', 'contractor_name', 'shift', 'location', 'department', 'emp_count')
    list_filter = ('date', 'contractor_name', 'shift', 'location', 'department')
    search_fields = ('contractor_name', 'location', 'department')
    date_hierarchy = 'date'




#==================================================================================



from .models import ContractEmpDepartment, ContractEmployee



@admin.register(ContractEmpDepartment)
class ContractDepartmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)
    ordering = ('name',)

class ContractEmployeeResource(resources.ModelResource):
    class Meta:
        model = ContractEmployee
        import_id_fields = ['id']  # Use ID for updates
        fields = ('id', 'name', 'employee_type', 'department')


@admin.register(ContractEmployee)
class ContractEmployeeAdmin(ImportExportModelAdmin):
    resource_class = ContractEmployeeResource
    list_display = ('id', 'name', 'employee_type', 'department')
    list_filter = ('department', 'employee_type')
    search_fields = ('id', 'name')
