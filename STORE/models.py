from django.db import models
from datetime import date, time

class Vehicle(models.Model):
    record_date = models.DateField(default=date.today, null=True)  # Record Date column
    invoice = models.CharField(max_length=100, null=True)
    name_of_supplier = models.CharField(max_length=100)
    material = models.CharField(max_length=100)
    unit = models.CharField(max_length=20)
    qty = models.FloatField()
    reporting_date = models.DateField()
    report_time = models.TimeField()
    unloading_date = models.DateField(blank=True, null=True)
    unloading_time = models.TimeField(blank=True, null=True)
    unloading_days = models.IntegerField(default=0,blank=True, null=True)
    vehicle_no = models.CharField(max_length=100)
    name_of_transporter = models.CharField(max_length=100)
    status = models.CharField(max_length=50)
    manufacture = models.CharField(max_length=255, blank=True, null=True)
    remark = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        db_table = 'vehicle'


class MaterialRequest(models.Model):
    """One row for each material request / plan."""
    DOMESTIC = "DOM"
    EXPORT   = "EXP"

    TYPE_CHOICES = [
        (DOMESTIC, "Domestic"),
        (EXPORT,   "Export"),
    ]

    type            = models.CharField(
        max_length=3,
        choices=TYPE_CHOICES,
        default=DOMESTIC,
    )
    material_name   = models.CharField(max_length=150)
    trade_name      = models.CharField(max_length=150, blank=True)
    unit            = models.CharField(max_length=30, help_text="e.g. Kg / Litre / Nos")
    qty             = models.DecimalField("Quantity", max_digits=12, decimal_places=3)
    tentative_date  = models.DateField("Tentative Needed Date")

    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        db_table = 'dispatch'

    def __str__(self):
        return f"{self.get_type_display()} – {self.material_name} ({self.qty} {self.unit})"

    def get_absolute_url(self):
        return reverse("store:material-detail", args=[self.pk])
