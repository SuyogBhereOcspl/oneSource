from django import forms
from .models import R_and_D_Moisture,KFFactorEntry, KFFactorEntryLine
from django.forms import inlineformset_factory

class RAndDMoistureForm(forms.ModelForm):
    class Meta:
        model = R_and_D_Moisture
        fields = '__all__'
        widgets = {
            'entry_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full p-2 border border-gray-300 rounded-lg'
            }),
            'entry_time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'w-full p-2 border border-gray-300 rounded-lg'
            }),
            'eln_id': forms.TextInput(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg'
            }),
            'product_name': forms.TextInput(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg'
            }),
            'batch_no': forms.TextInput(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg'
            }),
            'sample_description': forms.Textarea(attrs={    # <-- CHANGE HERE!
                'class': 'w-full p-2 border border-gray-300 rounded-lg',
                'rows': 2,
                'placeholder': 'Enter sample description...'
            }),
            'unit': forms.Select(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg'
            }),
            'instrument': forms.Select(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg'
            }),
            'factor_mg_per_ml': forms.NumberInput(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg'
            }),
            'sample_weight_gm': forms.NumberInput(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg'
            }),
            'burette_reading_ml': forms.NumberInput(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg'
            }),
            'moisture_percent': forms.NumberInput(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg'
            }),
            'analysed_by': forms.Select(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg'
            }),
            'completed_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full p-2 border border-gray-300 rounded-lg'
            }),
            'completed_time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'w-full p-2 border border-gray-300 rounded-lg'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only display 'name' in dropdowns
        for field in ['product_name', 'unit', 'instrument', 'analysed_by']:
            self.fields[field].label_from_instance = lambda obj: obj.name




class KFFactorEntryForm(forms.ModelForm):
    class Meta:
        model = KFFactorEntry
        fields = ['instrument', 'analysed_by']
        widgets = {
            'instrument': forms.Select(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg'}),
            'analysed_by': forms.Select(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg'}),
        }

class KFFactorEntryLineForm(forms.ModelForm):
    class Meta:
        model = KFFactorEntryLine
        fields = ['sample_weight_mg', 'burette_reading_ml']
        widgets = {
            'sample_weight_mg': forms.NumberInput(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg',
                'placeholder': 'Sample Weight (mg)'
            }),
            'burette_reading_ml': forms.NumberInput(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg',
                'placeholder': 'Burette Reading (mL)'
            }),
        }

KFFactorEntryLineFormSet = inlineformset_factory(
    KFFactorEntry, KFFactorEntryLine,
    form=KFFactorEntryLineForm,
    extra=3,  # You can make this dynamic
    can_delete=False
)