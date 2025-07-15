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


