
from django import forms
from django.forms import inlineformset_factory
from .models import *
from django.utils import timezone
from django.forms import DateInput, DateTimeInput
from django.forms.models import construct_instance
from django.core.exceptions import ValidationError


# ─── S P E C    F O R M ─────────────────────────────────────────────────────────────
class SpecForm(forms.ModelForm):
    """
    A Specification can be one of three types:
      1. Numeric Range    (requires min_val and max_val)
      2. Choice List      (requires allowed_choices)
      3. Free‐Text        (no extra fields required)
    """
    # OVERRIDE FIELD to accept list from Select2 and join it
    group = forms.CharField(widget=forms.HiddenInput(), required=False)
    allowed_choices = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control choices-select',
            'rows': 2,
            'placeholder': 'Comma‐separate choices (e.g. Brown liquid,Clear liquid,...)'
        })
    )

    class Meta:
        model = Spec
        fields = ('group', 'name', 'spec_type', 'min_val', 'max_val', 'allowed_choices')

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Spec name'
            }),
            'spec_type': forms.Select(attrs={
                'class': 'form-control spec-type-select',
            }),
            'min_val': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'e.g. 0.00'
            }),
            'max_val': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'e.g. 100.00'
            }),
        }

    def clean(self):
        data = super().clean()
        stype = data.get('spec_type')
        minv, maxv = data.get('min_val'), data.get('max_val')
        choices = data.get('allowed_choices')

        print("DEBUG: choices raw value:", choices, "type:", type(choices))

        if stype == Spec.TYPE_NUMERIC:
            if minv is None or maxv is None:
                raise forms.ValidationError("Numeric specs require both Min and Max.")
            if minv > maxv:
                raise forms.ValidationError("Min must be ≤ Max.")

        elif stype == Spec.TYPE_CHOICE:
            if not choices:
                raise forms.ValidationError("Choice specs require at least one option.")

            # Handle list from Select2
            if isinstance(choices, list):
                joined = ",".join(choices)
                data['allowed_choices'] = joined
                self.instance.allowed_choices = joined

        return data

SpecFormSetCreate = inlineformset_factory(
    Product, Spec, form=SpecForm,
    fields=('group', 'name', 'spec_type', 'min_val', 'max_val', 'allowed_choices'),
    extra=1,
    can_delete=True,
)

SpecFormSetUpdate = inlineformset_factory(
    Product, Spec, form=SpecForm,
    fields=('group', 'name', 'spec_type', 'min_val', 'max_val', 'allowed_choices'),
    extra=0,
    can_delete=True,
)


# ─── P R O D U C T    F O R M ───────────────────────────────────────────────────────

class ProductForm(forms.ModelForm):
    """
    We present a 'stage' dropdown (pulled from LocalBOMDetail.item_name),
    but we don't store it to a non-existent Product.stage attribute. Instead
    we copy it into the existing Product.stages field on save. We also default
    the Product.name from FG Name when the user hasn't typed one.
    """
    name = forms.CharField(
        required=False,   # make optional so we can default it
        label="Product Name",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter a product name'
        })
    )

    stage = forms.ChoiceField(
        required=True,
        label="Stage",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_stage'
        }),
    )

    code = forms.CharField(
        label="BOM Code",
        required=False,
        widget=forms.TextInput(attrs={
            'readonly': 'readonly',
            'class': 'form-control',
            'id': 'id_code',
        })
    )

    item_type = forms.CharField(
        label="Item Type",
        required=False,
        widget=forms.TextInput(attrs={
            'readonly': 'readonly',
            'class': 'form-control',
            'id': 'id_item_type',
        })
    )

    stages = forms.CharField(
        label="Stages (free text)",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. Cutting,Assembling,Finishing'
        })
    )

    class Meta:
        model = Product
        fields = ['name', 'code', 'item_type', 'stages']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ─── Build the stage dropdown ──────────────────────────────────────
        # 1) Pull *all* item_name values, ordered:
        raw_names = LocalBOMDetail.objects\
            .values_list('item_name', flat=True)\
            .order_by('item_name')

        # 2) De-duplicate in Python while preserving order:
        unique_names = list(dict.fromkeys(raw_names))

        # 3) Build choices:
        self.fields['stage'].choices = [
            ('', '-- Select Stage --')
        ] + [(n, n) for n in unique_names]

        # ─── If editing an existing Product, pre-fill fields ──────────────
        if self.instance and self.instance.pk:
            # free-text name & stages
            self.fields['name'].initial   = self.instance.name
            self.fields['stages'].initial = self.instance.stages

            # dropdown stage → code & item_type
            prev = self.instance.stages or ''
            self.fields['stage'].initial = prev

            detail = LocalBOMDetail.objects.filter(item_name=prev).first()
            if detail:
                self.fields['code'].initial      = detail.bom_code
                self.fields['item_type'].initial = detail.itm_type

    def clean(self):
        data      = super().clean()
        sel_stage = data.get('stage')
        name      = data.get('name', '').strip()
        detail    = None

        if sel_stage:
            # copy dropdown → both cleaned_data and model.stages
            data['stages']          = sel_stage
            self.instance.stages    = sel_stage

            detail = LocalBOMDetail.objects.filter(item_name=sel_stage).first()
            if detail:
                data['code']            = detail.bom_code
                data['item_type']       = detail.itm_type
                self.instance.code      = detail.bom_code
                self.instance.item_type = detail.itm_type

        # If the user didn’t supply a name, default to FG Name
        if not name and detail:
            data['name']        = detail.fg_name
            self.instance.name  = detail.fg_name
        elif name:
            self.instance.name  = name

        return data
    
# ─── I M P O R T    A P P E A R A N C E    F O R M ───────────────────────────────
class ImportAppearanceForm(forms.Form):
    file = forms.FileField(
        label="Select Excel file (.xlsx)",
        help_text="Upload the 'In Process Specs.xlsx'"
    )

class SpecUploadForm(forms.Form):
    excel_file = forms.FileField(
        label="Upload specs Excel",
        help_text="Must have columns: Name, Type, Choices, Min Value, Max Value"
    )





# ────────────────────────────────────────────────────────────────────────────
#  Base form (Production & QC share most widgets / labels)
# ────────────────────────────────────────────────────────────────────────────
class QCEntryForm(forms.ModelForm):
    # --------------------
    # Product (unchanged)
    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        empty_label="— Select a product —",
        widget=forms.Select(attrs={"id": "id_product", "class": "form-select"}),
    )

    # --------------------
    # Stage **no longer** uses model choices
    stage = forms.CharField(
        required=False,
        label="Stage",
        widget=forms.Select(attrs={"id": "id_stage", "class": "form-select"}),
    )

    # --------------------
    # Sample description
    sample_description = forms.CharField(
        required=False,
        label="Sample Description",
        widget=forms.TextInput(
            attrs={"id": "id_sample_description", "class": "form-control"}
        ),
    )

    # ----------------------------------------------------------------------
    # Constructor
    # ----------------------------------------------------------------------
    def __init__(self, *args, stage_choices=None, **kwargs):
        """
        `stage_choices` is supplied by the view (a list of dicts coming
        from the Stage → Product mapping query).  It replaces the widget’s
        <option> list *without* triggering model-level choice validation.
        """
        super().__init__(*args, **kwargs)

        # Inject run-time <option> list ⇢ widget.choices
        if stage_choices:
            widget_choices = [("", "— Select a stage —")] + [
                (opt["stages"], opt["stages"])
                for opt in stage_choices
                if opt.get("stages")
            ]
            self.fields["stage"].widget.choices = widget_choices

        # ------------------------------------------------------------------
        # Cosmetic tweaks (bootstrap classes, nice labels, defaults)
        # ------------------------------------------------------------------
        self.label_suffix = ""
        for fld in self.fields.values():
            cls = fld.widget.attrs.get("class", "")
            if (
                "form-control" not in cls
                and isinstance(
                    fld.widget,
                    (forms.TextInput, forms.Textarea, forms.DateInput, forms.DateTimeInput),
                )
            ):
                fld.widget.attrs["class"] = (cls + " form-control").strip()

        # Default “now” for entry_date on “new” forms
        if not (self.instance and self.instance.pk):
            self.fields["entry_date"].initial = timezone.localtime().strftime(
                "%Y-%m-%dT%H:%M"
            )

        # Friendly labels
        self.fields["sample_received_at"].label = "Sample received at QC"
        self.fields["ar_no"].label = "AR No."
        self.fields["release_by_qc_at"].label = "Sample released from QC"

        # Pre-select Stage when editing
        if self.instance and self.instance.pk:
            self.fields["stage"].initial = self.instance.stage

    # ----------------------------------------------------------------------
    # OVERRIDE  _post_clean  →  skip model-level “choice” check for `stage`
    # ----------------------------------------------------------------------
    def _post_clean(self) -> None:
        """
        Replicates `ModelForm._post_clean()` but tells the model-instance
        to skip validation on the *stage* field.  All other field / unique
        checks remain active.
        """
        opts = self._meta
        # 1) copy cleaned_data → instance (Django’s helper)
        self.instance = construct_instance(
            self, self.instance, opts.fields, opts.exclude
        )

        # 2) model validation  (skip `stage`)
        try:
            self.instance.full_clean(exclude=["stage"])
        except ValidationError as exc:
            self._update_errors(exc)

    # ----------------------------------------------------------------------
    # Cross-field check kept from original code
    # ----------------------------------------------------------------------
    def clean(self):
        cleaned = super().clean()
        psd = cleaned.get("prod_sign_date")
        ed = cleaned.get("entry_date")
        if psd and ed and psd > ed:
            self.add_error(
                "entry_date",
                "Entry date must be on or after production sign date.",
            )
        return cleaned

    # ----------------------------------------------------------------------
    # Meta
    # ----------------------------------------------------------------------
    class Meta:
        model = QCEntry
        fields = [
            "product",
            "block",
            "equipment_id",
            "test_required_for",
            "stage",
            "prod_sign_date",
            "batch_no",
            "sample_received_at",
            "entry_date",
            "ar_no",
            "sample_sent_at",
            "release_by_qc_at",
            "sample_description",
        ]
        widgets = {
            "block": forms.TextInput(attrs={"id": "id_block", "class": "form-control"}),
            "equipment_id": forms.TextInput(
                attrs={"id": "id_equipment_id", "class": "form-control"}
            ),
            "test_required_for": forms.TextInput(
                attrs={"id": "id_test_required_for", "class": "form-control"}
            ),
            "prod_sign_date": DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "batch_no": forms.TextInput(
                attrs={"id": "id_batch_no", "class": "form-control"}
            ),
            "sample_received_at": DateTimeInput(
                attrs={"type": "datetime-local", "class": "form-control"}
            ),
            "entry_date": DateTimeInput(
                attrs={"type": "datetime-local", "class": "form-control"}
            ),
            "ar_no": forms.TextInput(
                attrs={"id": "id_ar_no", "class": "form-control"}
            ),
            "sample_sent_at": DateTimeInput(
                attrs={"type": "datetime-local", "class": "form-control"}
            ),
            "release_by_qc_at": DateTimeInput(
                attrs={"type": "datetime-local", "class": "form-control"}
            ),
        }


# ────────────────────────────────────────────────────────────────────────────
#  Phase-1 form (Production)
# ────────────────────────────────────────────────────────────────────────────
class ProductionQCEntryForm(QCEntryForm):
    """
    • Adds readonly ‘block’ field
    • Disables all widgets if status ≠ draft
    """

    def __init__(self, *args, stage_choices=None, **kwargs):
        super().__init__(*args, stage_choices=stage_choices, **kwargs)

        # block is always readonly for production
        self.fields["block"].widget.attrs["readonly"] = True

        # If entry already left “draft” → lock entire form
        if self.instance and self.instance.pk and self.instance.status != "draft":
            for fld in self.fields.values():
                fld.widget.attrs["disabled"] = True


# ────────────────────────────────────────────────────────────────────────────
#  Phase-2 form (QC results)  – untouched logic
# ────────────────────────────────────────────────────────────────────────────
class QCResultsForm(forms.ModelForm):
    """QC team fills in results & decision."""
    # Add a hidden field to carry the JS‐selected group
    selected_group = forms.CharField(
        widget=forms.HiddenInput(),
        required=False,
        help_text="Which specification group was selected at QC time."
    )

    class Meta:
        model = QCEntry
        fields = (
            "batch_no",
            "sample_received_at",
            "ar_no",
            "release_by_qc_at",
            "group", 
            "general_remarks", 
            "status",
            "decision_status",
            "selected_group",
        )
        widgets = {
            "batch_no": forms.TextInput(
                attrs={"class": "form-control", "readonly": True}
            ),
            "sample_received_at": DateTimeInput(
                attrs={"type": "datetime-local", "class": "form-control"}
            ),
            "ar_no": forms.TextInput(attrs={"class": "form-control"}),
            "release_by_qc_at": DateTimeInput(
                attrs={"type": "datetime-local", "class": "form-control"}
            ),
            "group": forms.Select(attrs={"class":"form-select"}, choices=[]),
              "general_remarks": forms.Textarea(
                attrs={
                  "class": "form-control",
                  "rows": 3,
                  "maxlength": 250,
                  "placeholder": "Up to 250 characters…"
                }
            ),
            "status": forms.HiddenInput(),
            "decision_status": forms.Select(
                choices=QCEntry.DECISION_CHOICES, attrs={"class": "form-select"}
            ),
        }
        labels = {
            "sample_received_at": "Sample received at QC",
            "ar_no": "AR No.",
            "release_by_qc_at": "Sample released from QC",
            "decision_status": "QC Decision",
            "group": "Specification Group",
            "general_remarks": "General Remarks",
        }

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # If we're editing an existing entry, prefill the hidden field
            if self.instance and self.instance.pk:
                self.fields["selected_group"].initial = self.instance.selected_group
                self.fields["general_remarks"].initial = self.instance.general_remarks or ""

        def save(self, commit=True):
            # grab the selected_group from cleaned_data and store it
            self.instance.selected_group = self.cleaned_data.get("selected_group", "")
            self.instance.general_remarks = self.cleaned_data.get("general_remarks", "")
            return super().save(commit=commit)


