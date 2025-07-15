# products/models.py

from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils import timezone
from django.db.models import Max


class Product(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, blank=True)
    item_type = models.CharField(max_length=100, blank=True)
    appearance_options = models.ManyToManyField('AppearanceOption', blank=True, related_name='products')
    stages = models.CharField(max_length=200, blank=True, help_text="Comma-separated list of stages")
    
    class Meta:
        db_table = 'qc_product'

    def __str__(self):
        return self.name


class Spec(models.Model):
    TYPE_NUMERIC = 'numeric'
    TYPE_CHOICE  = 'choice'
    TYPE_TEXT    = 'text'

    SPEC_TYPE_CHOICES = [
        (TYPE_NUMERIC, 'Numeric Range'),
        (TYPE_CHOICE,  'Choice List'),
        (TYPE_TEXT,    'Free‐Text'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='specs')
    group   = models.CharField(max_length=100,blank=True,null=True,help_text="Heading for this spec batch, e.g. '8 hr', '15 hr', etc.")
    name = models.CharField(max_length=100)
    spec_type = models.CharField(max_length=10, choices=SPEC_TYPE_CHOICES, default=TYPE_NUMERIC, help_text="Choose whether this spec uses a numeric range, a set of choices, or free text.")
    min_val = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    max_val = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    allowed_choices = models.TextField(blank=True, help_text="(Choice type only) Comma‐separate the allowed text values, e.g. “Brown liquid,Clear liquid,White powder”")

    class Meta:
        db_table = 'qc_spec'
        unique_together = ('product', 'group', 'name')
        ordering        = ['product', 'group', 'name']

    def __str__(self):
        return f"{self.product.name} – {self.name}"

    def clean(self):
        """
        Enforce:
          - If spec_type is numeric → min_val and max_val must both be provided and min_val ≤ max_val.
          - If spec_type is choice  → allowed_choices must be a non‐empty comma‐separated list.
          - If spec_type is text    → neither min/max nor allowed_choices are required.
        """
        super().clean()

        if self.spec_type == self.TYPE_NUMERIC:
            if self.min_val is None or self.max_val is None:
                raise ValidationError({
                    'min_val': "Numeric spec requires both a minimum and a maximum value.",
                    'max_val': "Numeric spec requires both a minimum and a maximum value."
                })
            if self.min_val > self.max_val:
                raise ValidationError("Minimum value must be less than or equal to maximum value.")

        elif self.spec_type == self.TYPE_CHOICE:
            if not self.allowed_choices.strip():
                raise ValidationError({
                    'allowed_choices': "Choice spec requires at least one allowed choice (comma‐separated)."
                })

        else:  # TYPE_TEXT
            # Free‐text specs do not need min_val/max_val or allowed_choices.
            pass

class AppearanceOption(models.Model):
    """
    A master table to store “Appearance” choices for specs. 
    You will upload your Excel sheet once, populating this table.
    """
    name = models.CharField(max_length=200, unique=True)

    class Meta:
        db_table = 'qc_appearance_option'
        verbose_name = "Appearance Option"
        verbose_name_plural = "Appearance Options"
        ordering = ["name"]

    def __str__(self):
        return self.name



class QCEntry(models.Model):
    STAGE_CHOICES = [
        ('raw',      'Raw Material'),
        ('inproc_1', 'In-Process Stage 1'),
        ('inproc_2', 'In-Process Stage 2'),
        ('finished', 'Finished Goods'),
    ]

    STATUS_CHOICES = [
        ('draft',        'Draft (Production)'),
        ('pending_qc',   'Pending QC'),
        ('qc_completed', 'QC Completed'),
        ('cancelled',    'Cancelled'),
    ]

    DECISION_CHOICES = [
        ('approved',                 'Approved'),
        ('approved_under_deviation', 'Approved under deviation'),
        ('rejected',                 'Rejected'),
    ]

    # ─── New fields ──────────────────────────────────────
    decision_status = models.CharField(max_length=30, choices=DECISION_CHOICES, blank=True, null=True, help_text="QC decision: approved, approved under deviation, or rejected")
    entry_no = models.PositiveIntegerField(unique=True, editable=False, null=True, help_text="Automatically assigned sequential entry number.")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, help_text="Select the product for which you’re generating this QC entry.")
    block = models.CharField(max_length=50, blank=True, help_text="Auto-populated when an equipment is chosen.")
    equipment_id = models.CharField(max_length=50, blank=True, help_text="Select which equipment/batch line this QC pertains to.")
    test_required_for = models.CharField("Test Required For", max_length=100, blank=True, help_text="Why this QC is being performed.")
    stage = models.CharField(max_length=100, choices=STAGE_CHOICES, help_text="At which stage of production this sample was taken.")
    group   = models.CharField("Specification Group",max_length=100,blank=True, help_text="Which specs group was used when entering QC results.")
    selected_group     = models.CharField(max_length=200,blank=True,help_text="Which specification group was selected when entering QC results.")
    general_remarks    = models.TextField(blank=True, max_length=250,help_text="General remarks entered by QC (up to 250 characters).")
    prod_sign_date = models.DateField(null=True, blank=True, help_text="Date when Production signed off on this batch.")
    batch_no = models.CharField(max_length=100, blank=True, help_text="Batch number (pulled from ERP BMR).")
    sample_received_at = models.DateTimeField("Sample received at QC", null=True, blank=True, help_text="When Production delivered the sample to QC.")
    entry_date = models.DateTimeField(default=timezone.now, help_text="Date/time when this QC entry was created.")
    ar_no = models.CharField("AR No.", max_length=100, blank=True, help_text="Analysis Request number assigned by Production.")
    sample_sent_at = models.DateTimeField(null=True, blank=True, help_text="Date/time when sample was sent for analysis.")
    sample_description = models.TextField("Sample Description", blank=True, help_text="Short description or notes about the sample.")
    release_by_qc_at = models.DateTimeField("Sample Released from QC", null=True, blank=True, help_text="When QC officially released the batch.")
    created = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', help_text="draft → pending_qc → qc_completed/cancelled")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='qc_created_entries', null=True, blank=True, on_delete=models.SET_NULL, help_text="Production user who created this entry.")
    qc_completed_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='qc_entries_completed', null=True, blank=True, on_delete=models.SET_NULL, help_text="QC user who completed the results.")


    class Meta:
        db_table = 'qc_entry'
        ordering = ['-created']

    def save(self, *args, **kwargs):
        # Assign sequential entry_no on first save
        if self.entry_no is None:
            last = QCEntry.objects.aggregate(max_no=Max('entry_no'))['max_no'] or 0
            self.entry_no = last + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Entry No. {self.entry_no} – {self.product.name} (Batch: {self.batch_no}) [{self.get_status_display()}]"

class SpecEntry(models.Model):
    qc_entry = models.ForeignKey(QCEntry, on_delete=models.CASCADE, related_name='values', help_text="The QCEntry to which this particular specification result belongs.")
    spec = models.ForeignKey(Spec, on_delete=models.CASCADE, help_text="Which specification (test parameter) this result is for.")
    value = models.CharField(max_length=200, blank=True, null=True, help_text="Result for this spec: numeric or free-text (e.g. appearance).")
    remark = models.TextField(blank=True, help_text="Automatically set to 'Pass' or 'Fail' based on min/max, or left blank.")


    class Meta:
        db_table = 'qc_spec_entry'
        unique_together = ('qc_entry', 'spec')
        ordering = ['qc_entry', 'spec']

    def __str__(self):
        return f"{self.qc_entry.id} – {self.spec.name}: {self.value}"

class LocalItemMaster(models.Model):
    """
    A local copy of the ERP Item Master.
    We will sync this table with the ERP view periodically.
    """
    product_id = models.CharField(max_length=50, primary_key=True, help_text="ERP’s unique product ID.")
    product_name = models.CharField(max_length=200, help_text="ERP’s product description/name.")
    item_type = models.CharField(max_length=100, help_text="ERP’s item type/category.")


    class Meta:
        db_table = 'qc_localitemmaster'
        ordering = ['product_name']
        verbose_name = "Local Item Master"
        verbose_name_plural = "Local Item Masters"

    def __str__(self):
        return f"{self.product_name} ({self.product_id})"


class LocalEquipmentMaster(models.Model):
    """
    A local copy of the ERP Equipment Master.
    We will sync this table with the ERP view periodically.
    """
    eqp_code = models.CharField(max_length=50, primary_key=True, help_text="ERP’s unique equipment ID.")
    eqp_name = models.CharField(max_length=200, help_text="ERP’s equipment name/description.")
    eqp_remarks = models.CharField(max_length=500, blank=True, null=True, help_text="Optional remarks or notes from ERP.")
    unit_code = models.CharField(max_length=50, blank=True, null=True, help_text="Optional unit code (e.g. department or plant).")
    tag_no = models.CharField(max_length=100, blank=True, null=True, help_text="Optional tag number for this equipment.")
    block_name = models.CharField(max_length=100, blank=True, null=True, help_text="If applicable, the block or area name this equipment is in.")


    class Meta:
        db_table = 'qc_localequipmentmaster'
        ordering = ['eqp_name']
        verbose_name = "Local Equipment Master"
        verbose_name_plural = "Local Equipment Masters"

    def __str__(self):
        return f"{self.eqp_name} ({self.eqp_code})"


class BmrIssue(models.Model):
    """
    Holds a synced copy of “BMR Issue” rows from the ERP database.
    We only populate this once (in qc_create), then read from it locally for any dropdowns or filters.
    """
    bmr_issue_type = models.CharField(max_length=100, help_text="ERP’s BMR Issue Type (e.g. Fresh Batch, Cleaning, etc.).")
    bmr_issue_no = models.CharField(max_length=100, help_text="ERP’s document number for the BMR Issue.")
    bmr_issue_date = models.DateField(help_text="Date of the BMR Issue in ERP.")
    fg_name = models.CharField(max_length=200, help_text="Finished Goods name.")
    op_batch_no = models.CharField(max_length=100, help_text="ERP’s “Output Batch Number” to filter on.")
    product_name = models.CharField(max_length=200, blank=True, null=True, help_text="ERP’s Product Name if available.")
    block = models.CharField(max_length=200, blank=True, null=True, help_text="ERP’s Block value if available.")
    line_no = models.IntegerField(help_text="Line number within the BMR Issue (ERP detail row).")
    item_type = models.CharField(max_length=100, help_text="ERP’s item type description.")
    item_code = models.CharField(max_length=100, help_text="ERP’s item code.")
    item_name = models.CharField(max_length=200, help_text="ERP’s item name.")
    item_narration = models.TextField(blank=True, null=True, help_text="Optional narration/remarks from ERP.")
    uom = models.CharField(max_length=50, help_text="Unit of measure code.")
    batch_quantity = models.DecimalField(max_digits=18, decimal_places=3, help_text="Quantity (in ERP) for this line.")


    class Meta:
        db_table = 'qc_bmr_issue'
        unique_together = ('bmr_issue_no', 'line_no')
        ordering = ['bmr_issue_no', 'line_no']
        verbose_name = "BMR Issue"
        verbose_name_plural = "BMR Issues"

    def __str__(self):
        return f"{self.bmr_issue_no} – Line {self.line_no}"
    

class LocalBOMDetail(models.Model):
    sr_no         = models.IntegerField()
    itm_type      = models.CharField(max_length=200)
    item_name     = models.CharField(max_length=200)
    fg_name       = models.CharField(max_length=200, blank=True, null=True)
    item_code     = models.CharField(max_length=50)
    quantity      = models.DecimalField(max_digits=18, decimal_places=6)
    bom_code      = models.CharField(max_length=50)
    bom_name      = models.CharField(max_length=200)
    type          = models.CharField(max_length=200)
    bom_item_code = models.CharField(max_length=50)
    name          = models.CharField(max_length=200)
    unit          = models.CharField(max_length=100)
    bom_qty       = models.DecimalField(max_digits=18, decimal_places=6)
    cflag         = models.CharField(max_length=5)

class Meta:
        db_table = 'qc_localbomdetail'
        verbose_name = "Local BOM Detail"
        verbose_name_plural = "Local BOM Details"
        ordering = ['sr_no']

def __str__(self):
        return f"{self.sr_no}: {self.item_name} ({self.bom_code})"

