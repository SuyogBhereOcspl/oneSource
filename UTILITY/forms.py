from django import forms
from .models import UtilityRecord

TYPE_CHOICES = [
    ("STEAM GENERATION READING", "STEAM GENERATION READING"),
    ("STEAM CONSUMPTION READING", "STEAM CONSUMPTION READING"),
    ("Boiler Water meter Reading", "Boiler Water meter Reading"),
    ("MIDC reading", "MIDC reading"),
    ("BRIQUETTE", "BRIQUETTE"),
    ("DM Water consumed for boiler", "DM Water consumed for boiler"),
]

COMMON_INPUT_CLASSES = (
    "w-full px-3 py-2.5 text-sm text-slate-700 "
    "border border-slate-300 rounded-lg shadow-sm "
    "focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 "
    "placeholder-slate-400 transition"
)

class UtilityRecordForm(forms.ModelForm):
    reading_type = forms.ChoiceField(
        choices=TYPE_CHOICES,
        widget=forms.HiddenInput()
    )

    class Meta:
        model = UtilityRecord
        fields = [
            "reading_type",
            "sb_3_e_22_main_fm_fv",
            "sb_3_sub_fm_oc",
            "block_a_reading",
            "block_b_reading",
            "mee_total_reading",
            "stripper_reading",
            "old_atfd",
            "mps_d_block_reading",
            "lps_e_17",
            "mps_e_17",
            "jet_ejector_atfd_c",
            "deareator",
            "new_atfd",
            "boiler_water_meter",
            "midc_water_e_18",
            "midc_water_e_17",
            "midc_water_e_22",
            "midc_water_e_16",
            "midc_water_e_20",
            "briquette_sb_3",
            "dm_water_for_boiler",
        ]
        widgets = {
            field: forms.NumberInput(attrs={
                "class": COMMON_INPUT_CLASSES,
                "placeholder": "0.00",
                "step": "any",
            })
            for field in fields if field != "reading_type"
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for fname, f in self.fields.items():
            if fname != "reading_type":
                f.required = False