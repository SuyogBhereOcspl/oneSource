from django import forms
from .models import EffluentRecord, EffluentQty, GeneralEffluent
from django_select2.forms import Select2Widget
from django.utils.timezone import now
from datetime import date
from django.forms import HiddenInput


BLOCK_CHOICES = [
    ('', '–– Select Block ––'),   # first empty placeholder
    ('BLOCK-A', 'BLOCK-A'),
    ('BLOCK-B', 'BLOCK-B'),
    ('BLOCK-C', 'BLOCK-C'),
    ('BLOCK-D', 'BLOCK-D'),
    ('BLOCK-E', 'BLOCK-E'),
]

# pick-list that the user will see
CATEGORY_CHOICES = [
    ("", "–– Select Category ––"),
    ("Process",   "Process"),
    ("Unprocess", "Unprocess"),
]

NATURE_MAP = {
    "Process": [
        "Acidic", "Basic", "Neutral", "Sodium Cyanide Effluent", "3CHP effluent",
        "Ammonium Chloride effluent", "Spent Sulphuric Acid", "Residue",
    ],
    "Unprocess": [
        "Scrubber HCl 30-32%", "Scrubber Basic Effluent", "Scrubber Acidic Effluent",
        "QC effluent", "Outside Drainage Water", "Dyke Effluent",
        "PCO Cleaning / cleaning Effluent", "Ejector effluent",
        "Scrubber Nox effluent",
    ],
}

class EffluentRecordForm(forms.ModelForm):
    product_name = forms.CharField(
        label="Product Name",
        widget=Select2Widget(
            attrs={
                'data-url': '/get_products/',
                'data-placeholder': 'Search Product Name',
                'class': 'w-full p-2 border border-gray-300 rounded-lg'
            }
        )
    )
    stage_name = forms.CharField(
        label="Stage Name",
        widget=Select2Widget(
            attrs={
                'data-url': '/get_stage_names/',
                'data-placeholder': 'Search Stage Name',
                'class': 'w-full p-2 border border-gray-300 rounded-lg'
            }
        )
    )
    batch_no = forms.CharField(
        label="Batch No",
        widget=Select2Widget(
            attrs={
                'data-url': '/get_batch_nos/',
                'data-placeholder': 'Search Batch No',
                'class': 'w-full p-2 border border-gray-300 rounded-lg'
            }
        )
    )
    block = forms.ChoiceField(
        label="Block",
        choices=BLOCK_CHOICES,
        widget=forms.Select(attrs={
            "class": "w-full p-2 border border-gray-300 rounded-lg",
        }),
        required=True,          # or False if you really want it optional
    )
    record_date = forms.DateField(
        initial=date.today,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full p-2 border border-gray-300 rounded-lg'
        }) )
    voucher_no = forms.CharField(
        required=False,
        widget=HiddenInput(attrs={
            'id': 'id_voucher_no',})  )    # so your JS $('#id_voucher_no') still works
        
   
    class Meta:
        model = EffluentRecord
        fields = ['record_date','product_name', 'stage_name', 'batch_no', 'voucher_no', 'block']
       



class EffluentQtyForm(forms.ModelForm):
    CATEGORY_CHOICES = [
        ("", "–– Select Category ––"),
        ("Process",   "Process"),
        ("Unprocess", "Unprocess"),
        ]
    category = forms.ChoiceField(choices=CATEGORY_CHOICES, required=True)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # If this is a blank form (newly added via JS), allow selection
        if not self.instance.pk:
            self.fields['category'].widget.attrs.update({
                'class': 'w-full p-2 border rounded category-select',
            })
            self.fields['effluent_nature'].widget.attrs.update({
                'class': 'w-full p-2 border rounded nature-select',
            })
        else:
            # Old prefilled rows - keep as readonly input
            self.fields['category'].widget.attrs.update({
                'readonly': 'readonly',
                'class': 'w-full p-2 border border-gray-300 rounded-lg bg-gray-50'
            })
            self.fields['effluent_nature'].widget.attrs.update({
                'readonly': 'readonly',
                'class': 'w-full p-2 border border-gray-300 rounded-lg bg-gray-50'
            })

    class Meta:
        model = EffluentQty
        fields = ['category', 'effluent_nature', 'plan_quantity', 'actual_quantity','quantity_kg']
        widgets = {
            'plan_quantity': forms.NumberInput(attrs={
                'readonly': 'readonly',
                'class': 'w-full p-2 border border-gray-300 rounded-lg bg-gray-50'
            }),
            'actual_quantity': forms.NumberInput(attrs={
                'class': 'w-full p-2 border border-gray-300 rounded-lg'
            }),
            'quantity_kg': forms.NumberInput(attrs={
                'readonly': 'readonly',
                'class': 'w-full p-2 border border-gray-300 rounded-lg bg-gray-50'
            }),
        }




class GeneralEffluentForm(forms.ModelForm):
    LOCATION_CHOICES = [
        ('', '–– Select Location ––'),
        ('BLOCK-A', 'BLOCK-A'),
        ('BLOCK-B', 'BLOCK-B'),
        ('BLOCK-C', 'BLOCK-C'),
        ('BLOCK-D', 'BLOCK-D'),
        ('BLOCK-E', 'BLOCK-E'),
        ('ETP', 'ETP'),
        ('QC', 'QC'),
    ]

    EFFLUENT_CHOICES = [
        ('', '–– Select Effluent Nature ––'),
        ('Scrubber HCl 30-32', 'Scrubber HCl 30-32'),
        ('Scrubber Basic Effluent', 'Scrubber Basic Effluent'),
        ('Scrubber Acidic Effluent', 'Scrubber Acidic Effluent'),
        ('QC effluent', 'QC effluent'),
        ('Outside Drainage Water', 'Outside Drainage Water'),
        ('Dyke Effluent', 'Dyke Effluent'),
        ('PCO Cleaning / cleaning Effluent', 'PCO Cleaning / cleaning Effluent'),
        ('Ejector effluent', 'Ejector effluent'),
        ('Scrubber Nox effluent', 'Scrubber Nox effluent'),
    ]

    record_date = forms.DateField(
        initial=date.today,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full p-2 border border-gray-300 rounded-lg'
        })
    )

    location = forms.ChoiceField(
        choices=LOCATION_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full p-2 border border-gray-300 rounded-lg'
        })
    )

    effluent_nature = forms.ChoiceField(
        choices=EFFLUENT_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full p-2 border border-gray-300 rounded-lg'
        }),
        required=False
    )

    actual_quantity = forms.FloatField(
        widget=forms.NumberInput(attrs={
            'class': 'w-full p-2 border border-gray-300 rounded-lg',
            'step': 'any',
            'placeholder': 'Enter quantity'
        }),
        required=False
    )

    class Meta:
        model = GeneralEffluent
        fields = ['record_date', 'location', 'effluent_nature', 'actual_quantity']