from django import forms
from .models import (
    ContractorManpowerAttendance,
    DepartmentManpowerRequirement,
    CONTRACT_NAME_CHOICES,
    SHIFT_CHOICES
)

class DepartmentManpowerRequirementForm(forms.ModelForm):
    class Meta:
        model = DepartmentManpowerRequirement
        fields = '__all__'



class ContractorManpowerAttendanceForm(forms.ModelForm):
    class Meta:
        model = ContractorManpowerAttendance
        exclude = []  # Or use: fields = '__all__'
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'contractor': forms.Select(attrs={'class': 'border rounded px-2 py-2 w-36'}),
            'shift': forms.Select(attrs={'class': 'border rounded px-2 py-2 w-20'}),
        }


from django.forms import modelformset_factory

ContractorAttendanceFormSet = modelformset_factory(
    ContractorManpowerAttendance, form=ContractorManpowerAttendanceForm, extra=0, can_delete=False
)






#=============================================================================================================
from .models import ContractorWorker
from django.forms import HiddenInput
from django.forms import modelformset_factory



class ContractorWorkerEntryForm(forms.ModelForm):
    class Meta:
        model = ContractorWorker
        # 'date' excluded as handled separately
        fields = ['contractor_name', 'shift', 'location', 'department', 'emp_count']
        widgets = {
            'contractor_name': forms.Select(attrs={'class': 'border rounded px-4 py-2'}),
            'shift': forms.Select(attrs={'class': 'border rounded px-4 py-2'}),
            'location': forms.Select(attrs={'class': 'border rounded px-4 py-2'}),
            'department': forms.Select(attrs={'class': 'border rounded px-4 py-2'}),
            'emp_count': forms.NumberInput(attrs={'min': 0, 'step': '0.001','class': 'border rounded px-4 py-2'}),
        }

ContractorWorkerEntryFormSet = modelformset_factory(
    ContractorWorker,
    form=ContractorWorkerEntryForm,
    extra=1,
    can_delete=True
)

# Example instantiation (in your views you pass your own queryset)
formset = ContractorWorkerEntryFormSet(queryset=ContractorWorker.objects.none())

for form in formset:
    form.fields['DELETE'].widget = HiddenInput()