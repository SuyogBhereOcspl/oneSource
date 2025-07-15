from django.db import models
from datetime import date

class EffluentRecord(models.Model):
    id = models.AutoField(primary_key=True)
    record_date = models.DateField(default=date.today)
    product_name = models.CharField(max_length=50, null=True, blank=True)
    stage_name = models.CharField(max_length=255, null=True, blank=True)  # New field
    batch_no = models.CharField(max_length=50, null=True, blank=True)  # New field (nullable)
    voucher_no = models.CharField(max_length=50, null=True, blank=True)
    block = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = 'effluent_records'

class EffluentQty(models.Model):
    id = models.AutoField(primary_key=True)
    effluent_record = models.ForeignKey(EffluentRecord, on_delete=models.CASCADE, related_name="qty_units")
    category = models.CharField(max_length=20)
    effluent_nature = models.CharField(max_length=100, null=True, blank=True)
    plan_quantity = models.FloatField(default=0.0,null=True, blank=True)
    actual_quantity = models.FloatField(default=0.0,null=True, blank=True)
    quantity_kg  = models.FloatField(default=0.0,null=True, blank=True)

    class Meta:
        db_table = 'effluent_qty'

class GeneralEffluent(models.Model):
    id = models.AutoField(primary_key=True)
    record_date = models.DateField(default=date.today)
    location = models.CharField(max_length=50, null=True, blank=True)
    effluent_nature = models.CharField(max_length=100, null=True, blank=True)
    actual_quantity = models.FloatField(default=0.0)

    class Meta:
        db_table = 'general_effluent'




class ProductionSchedule(models.Model):
    id                  = models.AutoField(primary_key=True)
    doc_no              = models.CharField(max_length=50, unique=True)
    type                = models.CharField(max_length=50, blank=True, null=True)
    bom_id              = models.CharField(max_length=50, blank=True, null=True)
    product_id          = models.CharField(max_length=255)  # FK to your Product master
    stage_name          = models.CharField(max_length=100, blank=True, null=True)
    block               = models.CharField(max_length=50, blank=True, null=True)
    production_quantity = models.DecimalField(max_digits=18, decimal_places=2)
    equipment_id        = models.CharField(max_length=50, blank=True, null=True)
    equipment_capacity  = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    bct_in_hrs          = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    no_of_batches       = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    batch_size          = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    start_date          = models.DateTimeField()
    end_date            = models.DateTimeField()
    wait_time           = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    batch_number        = models.CharField(max_length=50, blank=True, null=True)
    scheduling_approach = models.IntegerField(default=0)
    bom_name            = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        db_table = "production_schedule"
        managed = False  # because you’re using an external DB/router

class ProductionScheduleLine(models.Model):
    id                = models.AutoField(primary_key=True)
    schedule          = models.ForeignKey(
        ProductionSchedule,
        on_delete=models.CASCADE,
        db_column="schedule_id",
        related_name="lines"
    )
    line_type         = models.CharField(max_length=20)   # 'input'/'output'/'waste'/'equipment'
    material_category = models.CharField(max_length=50, blank=True, null=True)
    material_name     = models.CharField(max_length=100, blank=True, null=True)
    quantity          = models.FloatField(default=0.0)
    ratio             = models.FloatField(default=1.0)
    density           = models.FloatField(default=0.0)
    litre             = models.FloatField(default=0.0)
    include_in_total  = models.BooleanField(default=True)
    closed            = models.BooleanField(default=False)
    closed_date       = models.DateTimeField(blank=True, null=True)

    equipment_id      = models.CharField(max_length=50, blank=True, null=True)
    std_bct           = models.FloatField(default=0.0)
    wait_time         = models.FloatField(default=0.0)
    equipment_type    = models.CharField(max_length=50, blank=True, null=True)
    capacity_size     = models.CharField(max_length=50, blank=True, null=True)
    moc_equipment     = models.CharField(max_length=50, blank=True, null=True)
    star              = models.BooleanField(default=False)

    class Meta:
        db_table = "production_schedule_lines"
        managed = False
