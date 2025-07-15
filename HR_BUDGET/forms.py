from django import forms
from .models import ( ContractorWages,SecurityWages,HrBudgetWelfare,HrBudgetCanteen,HrBudgetMedical,HrBudgetVehicle,
    HrBudgetTravellingLodging,HRBudgetGuestHouse,HRBudgetGeneralAdmin,HRBudgetCommunication,InsuranceMediclaim,HRBudgetAMC,
    HRBudgetTraining,HRBudgetLegal)

class DateInput(forms.DateInput):
    input_type = 'date'
    template_name = 'django/forms/widgets/date.html'

    def __init__(self, **kwargs):
        super().__init__(attrs={
            'class': 'w-full p-2 border border-gray-300 rounded-lg',
            **kwargs.pop('attrs', {})
        }, **kwargs)

class BaseBudgetForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            # Set common Tailwind CSS classes for all fields
            field.widget.attrs['class'] = 'w-full p-2 border border-gray-300 rounded-lg'
            if isinstance(field.widget, forms.widgets.Textarea):
                field.widget.attrs['rows'] = 2

class ContractorWagesForm(BaseBudgetForm):
    class Meta:
        model = ContractorWages
        fields = '__all__'
        widgets = {
            'invoice_date': DateInput(),
            'description': forms.Textarea(attrs={
                'placeholder': 'Enter description (optional)'
            }),
        }



class SecurityWagesForm(BaseBudgetForm):
    contractor_name = forms.ChoiceField(
        choices=[('', 'Select Contractor')] + [
            ('Badalapur Enterprises', 'Badalapur Enterprises'),
            ('Other', 'Other'),
        ],
        widget=forms.Select(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg'})
    )

    custom_contractor_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full p-2 border border-gray-300 rounded-lg',
            'placeholder': 'Enter Custom Contractor Name',
        })
    )

    class Meta:
        model = SecurityWages
        fields = '__all__'
        widgets = {
            'invoice_date': DateInput(),
            'invoice_no': forms.TextInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg'}),
            'bill_amount': forms.NumberInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg'}),
            'gst': forms.NumberInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg'}),
            'description': forms.Textarea(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg',
                'placeholder': 'Enter description (optional)',
                'rows': 2,
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        contractor = cleaned_data.get('contractor_name')
        custom_name = cleaned_data.get('custom_contractor_name')

        if contractor == 'Other' and not custom_name:
            self.add_error('custom_contractor_name', "Please enter a contractor name for 'Other'.")
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.cleaned_data.get('contractor_name') == 'Other':
            instance.contractor_name = self.cleaned_data.get('custom_contractor_name')
        else:
            instance.contractor_name = self.cleaned_data.get('contractor_name')
        if commit:
            instance.save()
        return instance
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Check instance contractor_name value
        instance = kwargs.get('instance')
        if instance and instance.contractor_name not in dict(self.fields['contractor_name'].choices):
            # The stored contractor_name is a custom name not in fixed choices
            # So, set contractor_name field to 'Other' and put the actual name in custom field
            self.initial['contractor_name'] = 'Other'
            self.initial['custom_contractor_name'] = instance.contractor_name


class HrBudgetWelfareForm(BaseBudgetForm):
    class Meta:
        model = HrBudgetWelfare
        fields = '__all__'
        widgets = {
            'invoice_date': DateInput(),
            'description': forms.Textarea(attrs={
                'placeholder': 'Enter description (optional)'
            }),
        }

class HrBudgetCanteenForm(BaseBudgetForm):
    class Meta:
        model = HrBudgetCanteen
        fields = '__all__'
        widgets = {
            'invoice_date': DateInput(),
            'description': forms.Textarea(attrs={
                'placeholder': 'Enter description (optional)'
            }),
        }

class HrBudgetMedicalForm(BaseBudgetForm):
    class Meta:
        model = HrBudgetMedical
        fields = '__all__'
        widgets = {
            'invoice_date': DateInput(),
            'description': forms.Textarea(attrs={
                'placeholder': 'Enter description (optional)'
            }),
        }


class HrBudgetVehicleForm(forms.ModelForm):
    class Meta:
        model = HrBudgetVehicle
        fields = '__all__'
        widgets = {
            'invoice_date': DateInput(),
            'vehicle_name': forms.TextInput(attrs={'class': 'hidden'}),  # Will be filled by JS
            'vehicle_number': forms.TextInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg'}),
            'category': forms.Select(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg'}),
            'gst': forms.NumberInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg'}),
            'bill_amount': forms.NumberInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg'}),
            'description': forms.Textarea(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg',
                'placeholder': 'Enter description (optional)',
                'rows': 2,
            }),
            'invoice_no': forms.TextInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        vehicle_name = self.data.get('vehicle_name') or cleaned_data.get('vehicle_name')
        vehicle_number = cleaned_data.get('vehicle_number')
        if not vehicle_name:
            self.add_error('vehicle_name', "Please select or enter a vehicle name.")
        if not vehicle_number:
            self.add_error('vehicle_number', "Please enter vehicle number for selected vehicle.")
        cleaned_data['vehicle_name'] = vehicle_name
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.vehicle_name = self.cleaned_data.get('vehicle_name')
        if commit:
            instance.save()
        return instance




class HrBudgetTravellingForm(forms.ModelForm):
    name = forms.ChoiceField(
        choices=[('', 'Select Name')] + HrBudgetTravellingLodging.TRAVELLING_CHOICES,
        widget=forms.Select(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg'})
    )
    custom_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full p-2 border border-gray-300 rounded-lg',
            'placeholder': 'Enter Custom Name',
        })
    )
    class Meta:
        model = HrBudgetTravellingLodging
        fields = '__all__'
        widgets = {
            'invoice_date': DateInput(),
            'invoice_no': forms.TextInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg'}),
            'bill_amount': forms.NumberInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg'}),
            'gst': forms.NumberInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg'}),
            'description': forms.Textarea(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg',
                'placeholder': 'Enter description (optional)',
                'rows': 2,
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        custom_name = cleaned_data.get('custom_name')
        if name == "Other":
            if not custom_name:
                self.add_error('custom_name', "Please enter name for 'Other'.")
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.cleaned_data.get('name') == 'Other':
            instance.name = self.cleaned_data.get('custom_name')
        else:
            instance.name = self.cleaned_data.get('name')
        if commit:
            instance.save()
        return instance




class HRBudgetGuestHouseForm(forms.ModelForm):
    name = forms.ChoiceField(
        choices=[('', 'Select Name')] + HRBudgetGuestHouse.NAME_CHOICES,
        widget=forms.Select(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg'})
    )
    category = forms.ChoiceField(
        choices=[('', 'Select Category')] + HRBudgetGuestHouse.CATEGORY_CHOICES,
        widget=forms.Select(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg'})
    )

    class Meta:
        model = HRBudgetGuestHouse
        fields = '__all__'
        widgets = {
            'invoice_date': DateInput(),
            'invoice_no': forms.TextInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg'}),
            'gst': forms.NumberInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg'}),
            'bill_amount': forms.NumberInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg'}),
            'description': forms.Textarea(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg',
                'placeholder': 'Enter description (optional)',
                'rows': 2,
            }),
        }


class HRBudgetGeneralAdminForm(forms.ModelForm):
    category = forms.ChoiceField(
        choices=[('', 'Select Category')] + HRBudgetGeneralAdmin.CATEGORY_CHOICES,
        widget=forms.Select(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg'})
    )

    class Meta:
        model = HRBudgetGeneralAdmin
        fields = '__all__'
        widgets = {
            'invoice_date': DateInput(),
            'invoice_no': forms.TextInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg'}),
            'gst': forms.NumberInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg'}),
            'bill_amount': forms.NumberInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg'}),
            'description': forms.Textarea(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg',
                'placeholder': 'Enter description (optional)',
                'rows': 2,
            }),
        }


class HRBudgetCommunicationForm(forms.ModelForm):
    invoice_name = forms.ChoiceField(
        choices=[('', 'Select Invoice Name')] + HRBudgetCommunication.NAME_CHOICES,
        widget=forms.Select(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg'})
    )
    custom_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full p-2 border border-gray-300 rounded-lg',
            'placeholder': 'Enter Custom Name',
        })
    )

    class Meta:
        model = HRBudgetCommunication
        fields = '__all__'
        widgets = {
            'invoice_date': DateInput(),
            'invoice_no': forms.TextInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg'}),
            'gst': forms.NumberInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg'}),
            'bill_amount': forms.NumberInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg'}),
            'description': forms.Textarea(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg',
                'placeholder': 'Enter description (optional)',
                'rows': 2,
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        invoice_name = cleaned_data.get('invoice_name')
        custom_name = cleaned_data.get('custom_name')
        if invoice_name == "Other":
            if not custom_name:
                self.add_error('custom_name', "Please enter name for 'Other'.")
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.cleaned_data.get('invoice_name') == 'Other':
            instance.invoice_name = self.cleaned_data.get('custom_name')
        else:
            instance.invoice_name = self.cleaned_data.get('invoice_name')
        if commit:
            instance.save()
        return instance




class InsuranceMediclaimForm(forms.ModelForm):
    category = forms.ChoiceField(
        choices=[('', 'Select Category')] + InsuranceMediclaim.CATEGORY_CHOICES,
        widget=forms.Select(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg'})
    )

    class Meta:
        model = InsuranceMediclaim
        fields = '__all__'
        widgets = {
            'invoice_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full p-2 border border-gray-300 rounded-lg'
            }),
            'invoice_no': forms.TextInput(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg'
            }),
            'gst': forms.NumberInput(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg'
            }),
            'bill_amount': forms.NumberInput(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg',
                'rows': 3,
                'placeholder': 'Enter description (optional)',
            }),
        }


class HRBudgetAMCForm(forms.ModelForm):
    amc_name = forms.ChoiceField(
        choices=[('', 'Select AMC Name')] + HRBudgetAMC.AMC_CHOICES,
        widget=forms.Select(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg'})
    )
    custom_amc_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full p-2 border border-gray-300 rounded-lg',
            'placeholder': 'Enter Custom AMC Name',
        })
    )

    class Meta:
        model = HRBudgetAMC
        fields = '__all__'
        widgets = {
            'invoice_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full p-2 border border-gray-300 rounded-lg'
            }),
            'invoice_no': forms.TextInput(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg'
            }),
            'gst': forms.NumberInput(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg'
            }),
            'bill_amount': forms.NumberInput(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg',
                'rows': 3,
                'placeholder': 'Enter description (optional)',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            amc_choices = [choice[0] for choice in HRBudgetAMC.AMC_CHOICES]
            amc_name_value = self.instance.amc_name if self.instance and self.instance.pk else None
            if amc_name_value and amc_name_value not in amc_choices:
                self.initial['amc_name'] = 'Other'
                self.initial['custom_amc_name'] = amc_name_value
                self.fields['amc_name'].initial = 'Other'
                self.fields['custom_amc_name'].initial = amc_name_value
                self.instance.amc_name = 'Other'   # <<------ Important!
            else:
                self.initial['amc_name'] = amc_name_value
                self.fields['amc_name'].initial = amc_name_value

    def clean(self):
        cleaned_data = super().clean()
        amc_name = cleaned_data.get('amc_name')
        custom_amc_name = cleaned_data.get('custom_amc_name')
        if amc_name == "Other" and not custom_amc_name:
            self.add_error('custom_amc_name', "Please enter AMC Name for 'Other'.")
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.cleaned_data.get('amc_name') == 'Other':
            instance.amc_name = self.cleaned_data.get('custom_amc_name')
        else:
            instance.amc_name = self.cleaned_data.get('amc_name')
        if commit:
            instance.save()
        return instance


class HRBudgetTrainingForm(forms.ModelForm):
    class Meta:
        model = HRBudgetTraining
        fields = '__all__'
        widgets = {
            'invoice_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full p-2 border border-gray-300 rounded-lg'
            }),
            'invoice_no': forms.TextInput(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg'
            }),
            'name': forms.TextInput(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg'
            }),
            'gst': forms.NumberInput(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg'
            }),
            'bill_amount': forms.NumberInput(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg',
                'rows': 3,
                'placeholder': 'Enter description (optional)',
            }),
        }



class HRBudgetLegalForm(forms.ModelForm):
    class Meta:
        model = HRBudgetLegal
        fields = '__all__'
        widgets = {
            'invoice_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full p-2 border border-gray-300 rounded-lg'
            }),
            'invoice_no': forms.TextInput(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg'
            }),
            'name': forms.TextInput(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg'
            }),
            'gst': forms.NumberInput(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg'
            }),
            'bill_amount': forms.NumberInput(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg',
                'rows': 3,
                'placeholder': 'Enter description (optional)',
            }),
        }