from django import forms
from .models import HR

class HRForm(forms.ModelForm):
    class Meta:
        model = HR
        fields = [
            'date',
            'permanent_employees',
            'contract_labour_production',
            'contract_labour_others',
            'total_employee',
            'hrs',
            'total_no_of_hrs'
        ]
        widgets = {
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full p-2 border border-gray-300 rounded-lg'
            }),
            'permanent_employees': forms.NumberInput(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg'
            }),
            'contract_labour_production': forms.NumberInput(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg'
            }),
            'contract_labour_others': forms.NumberInput(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg'
            }),
            'total_employee': forms.NumberInput(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg bg-gray-50',
                'readonly': 'readonly'
            }),
            'hrs': forms.NumberInput(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg bg-gray-50',
                'readonly': 'readonly'
            }),
            'total_no_of_hrs': forms.NumberInput(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg bg-gray-50',
                'readonly': 'readonly'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        # Retrieve values and default to 0 if missing
        permanent_employees = cleaned_data.get('permanent_employees') or 0
        contract_labour_production = cleaned_data.get('contract_labour_production') or 0
        contract_labour_others = cleaned_data.get('contract_labour_others') or 0
        
        # Compute total_employee as the sum of employee types
        total_employee = permanent_employees + contract_labour_production + contract_labour_others
        cleaned_data['total_employee'] = total_employee
        
        # Set hrs to 8
        hrs = 8
        cleaned_data['hrs'] = hrs
        
        # Compute total_no_of_hrs as hrs * total_employee
        cleaned_data['total_no_of_hrs'] = hrs * total_employee
        
        return cleaned_data
