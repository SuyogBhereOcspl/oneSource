from django.db import models

class UtilityRecord(models.Model):
    reading_date       = models.DateField(db_column='reading_date')
    reading_type       = models.CharField(max_length=100, db_column='reading_type')
    sb_3_e_22_main_fm_fv  = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sb_3_sub_fm_oc      = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    block_a_reading     = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    block_b_reading     = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    mee_total_reading   = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stripper_reading    = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    old_atfd            = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    mps_d_block_reading = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    lps_e_17            = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    mps_e_17            = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    jet_ejector_atfd_c  = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    deareator           = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True) #new field 
    new_atfd            = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    boiler_water_meter  = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    midc_water_e_18     = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    midc_water_e_17     = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    midc_water_e_22     = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    midc_water_e_16     = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    midc_water_e_20     = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    briquette_sb_3      = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True) # BRIQUETTE
    dm_water_for_boiler = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)   #"Boiler Water meter Reading"
 
    class Meta:
        db_table = 'utility_records'

    def __str__(self):
        return f"{self.reading_date} | {self.reading_type}"
