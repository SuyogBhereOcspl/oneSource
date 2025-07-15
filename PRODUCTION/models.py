from django.db import models

class Downtime(models.Model):
    date = models.DateField(null=True)
    idle = models.CharField(max_length=5, default="No",null=True, blank=True)
    eqpt_id = models.CharField(max_length=50,null=True)
    eqpt_name = models.CharField(max_length=100,null=True)
    product_name = models.CharField(max_length=255,blank=True,null=True)
    stage_name = models.CharField(max_length=255,blank=True,null=True)
    product_code = models.CharField(max_length=100,blank=True,null=True)
    batch_no = models.CharField(max_length=50,blank=True,null=True)
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)
    start_time = models.TimeField(null=True)
    end_time = models.TimeField(null=True)
    total_duration = models.FloatField(null=True)
    block = models.CharField(max_length=50,null=True)
    downtime_dept = models.CharField(max_length=255,null=True)
    downtime_category = models.CharField(max_length=100, null=True, blank=True)
    reason = models.TextField(null=True)
    bom_qty = models.FloatField(null=True, blank=True)
    bct = models.FloatField(null=True, blank=True)
    loss = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = 'downtime'
