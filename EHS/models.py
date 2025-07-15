# Create your models here.
from django.db import models
from django.utils import timezone

class Physical_Location(models.Model):
    name = models.CharField(max_length=128)

    class Meta:
        db_table = 'physical_location'

    def __str__(self):
        return self.name



class LeadingRecords(models.Model):
    observation_date = models.DateField(default=timezone.now)
    department = models.CharField(max_length=50,blank=True, null=True)
    physical_location = models.ForeignKey(Physical_Location, on_delete=models.DO_NOTHING, null=True, blank=True)
    leading_abnormality = models.CharField(max_length=30)
    initiated_by = models.CharField(max_length=64,blank=True, null=True)
    severity = models.IntegerField(blank=True, null=True)
    likelihood = models.IntegerField(blank=True, null=True)
    risk_factor = models.CharField(max_length=10, blank=True, null=True)
    observation_description = models.TextField(blank=True, null=True)
    corrective_action = models.TextField(blank=True, null=True)
    psl_member_name = models.CharField(max_length=64, blank=True, null=True)
    responsible_person = models.CharField(max_length=64, blank=True, null=True)
    root_cause = models.TextField(blank=True, null=True)
    preventive_action = models.TextField(blank=True, null=True)
    target_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=10, blank=True, null=True)
    remark = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'leading_records'

    def __str__(self):
        return f"Leading Record {self.id} on {self.observation_date}"




SEVERITY_CHOICES = [
    (1, '1- Negligible (Can lead to First Aid Injury)'),
    (2, '2- Marginal (Can lead to MTC or RWC injury)'),
    (3, '3- Critical (Can lead to LTI Injury)'),
    (4, '4- Catastrophic (Multiple LTI or Fatalities)'),
]

LIKELIHOOD_CHOICES = [
    (1, '1- Unlikely (Very Rare - Once in a Lifetime)'),
    (2, '2- Remote (Once in 10 Years)'),
    (3, '3- Occasional (Once in 2 Years)'),
    (4, '4- Frequent (Once or more in a year)'),
]



def current_date():
    return timezone.now().date()


class Lagging_Indicator(models.Model):
    record_date = models.DateField(default=current_date)
    incident_date = models.DateField(null=True, blank=True)
    incident_time = models.TimeField(null=True, blank=True)
    employee_type = models.CharField(max_length=64, null=True, blank=True)
    Contractor_name =models.CharField(max_length=100,blank=True,null=True)
    department = models.CharField(max_length=50, null=True, blank=True)
    physical_location = models.ForeignKey(Physical_Location, on_delete=models.DO_NOTHING, null=True,blank=True)
    hse_lag_indicator = models.CharField(max_length=64, null=True, blank=True)
    type_of_injury = models.CharField(max_length=64, null=True, blank=True)
    injured_body_part = models.CharField(max_length=64, null=True, blank=True)
    name_of_injured_person = models.CharField(max_length=64, null=True, blank=True)
    severity = models.IntegerField(null=True, blank=True,choices=[(k, v) for k, v in SEVERITY_CHOICES])
    likelihood = models.IntegerField(null=True, blank=True,choices=[(k, v) for k, v in LIKELIHOOD_CHOICES])
    risk_factor = models.CharField(max_length=20, null=True, blank=True)
    incident = models.TextField(null=True, blank=True)
    immediate_action = models.TextField(null=True, blank=True)
    investigation_method =  models.CharField(max_length=64,null=True, blank=True)
    fact_about_men = models.TextField(null=True, blank=True)
    fact_about_machine = models.TextField(null=True, blank=True)
    fact_about_mother_nature = models.TextField(null=True, blank=True)
    fact_about_measurement = models.TextField(null=True, blank=True)
    fact_about_method = models.TextField(null=True, blank=True)
    fact_about_material = models.TextField(null=True, blank=True)
    fact_about_history = models.TextField(null=True, blank=True)
    why_one = models.TextField(null=True, blank=True)
    why_two = models.TextField(null=True, blank=True)
    why_three = models.TextField(null=True, blank=True)
    why_four = models.TextField(null=True, blank=True)
    why_five = models.TextField(null=True, blank=True)
    direct_root_cause = models.TextField(null=True, blank=True)
    indirect_root_cause = models.TextField(null=True, blank=True)
    psm_failure = models.TextField(null=True, blank=True)
    date_resume_duty = models.DateField(null=True, blank=True)
    mandays_lost = models.IntegerField(null=True, blank=True)
    complience_status = models.CharField(max_length=64, null=True, blank=True)
    complience_status_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'lagging_indicator'

    def update_compliance_status(self):
        """
        Update the compliance status based on related CAPA entries.
        """
        capa_entries = self.lagging_capa_entry.all()

        if not capa_entries.exists():
            self.complience_status = None
            self.complience_status_date = None
        else:
            # If any entry is "Overdue", set to Overdue
            if any(entry.compliance_status == "Overdue" for entry in capa_entries):
                self.complience_status = "Overdue"
                self.complience_status_date = None
            # Else if any entry is "Open/Due", set to Open/Due
            elif any(entry.compliance_status == "Open/Due" for entry in capa_entries):
                self.complience_status = "Open/Due"
                self.complience_status_date = None
            else:
                # All entries are closed: mark as Closed and set the date to today
                self.complience_status = "Closed"
                self.complience_status_date = timezone.now().date()

        # Save only the necessary fields to avoid recursion
        self.save(update_fields=['complience_status', 'complience_status_date'], skip_compliance_update=True)

    def save(self, *args, **kwargs):
        """
        Custom save method to calculate the risk factor and mandays lost before saving the model.
        """
        # Avoid recursion: If 'skip_compliance_update' flag is set, do not call update_compliance_status
        skip_compliance_update = kwargs.pop('skip_compliance_update', False)

        # Calculate risk_factor
        if self.severity and self.likelihood:
            # Only assign risk_factor if it's empty or if you want to always recalculate:
            risk_num = self.severity * self.likelihood
            if " - " not in str(self.risk_factor):
                # Calculate label just like frontend
                if risk_num <= 2:
                    label = "Low"
                elif risk_num <= 6:
                    label = "Medium"
                else:
                    label = "High"
                self.risk_factor = f"{risk_num} - {label}"
            # else: preserve the user-entered value
        else:
            self.risk_factor = None
        
        # Calculate mandays_lost
        if self.incident_date and self.date_resume_duty:
            self.mandays_lost = (self.date_resume_duty - self.incident_date).days
        else:
            self.mandays_lost = None
        
        # Call the parent save method
        super().save(*args, **kwargs)

        # Call update_compliance_status after saving, but only if not skipped
        if not skip_compliance_update:
            self.update_compliance_status()
    

class LaggingCapaEntry(models.Model):
    lagging_indicator = models.ForeignKey(
        Lagging_Indicator,
        related_name='lagging_capa_entry',
         on_delete=models.CASCADE, null=True, blank=True
    )
    capa = models.CharField(max_length=1000, null=True, blank=True)
    department = models.CharField(max_length=50, null=True, blank=True)
    frp = models.CharField(max_length=64, null=True, blank=True)
    target_date = models.DateField(null=True, blank=True)
    compliance_status = models.CharField(max_length=64, null=True, blank=True)

    class Meta:
        db_table = 'lagging_capa_entry'

    def close_capa(self):
        self.compliance_status = "Closed"
        self.save()
        self.lagging_indicator.update_compliance_status()






class PSSRJobRecord(models.Model):
    date = models.DateField(verbose_name="Date")
    moc_no = models.CharField(max_length=50, verbose_name="MOC No",blank=True,null=True)
    job_description = models.TextField(verbose_name="Job Description", blank=True, null=True)

    class Meta:
        db_table = 'pssr_job_record'
        verbose_name = 'PSSR Job Record'
        verbose_name_plural = 'PSSR Job Records'

    def __str__(self):
        return f"{self.date} | {self.moc_no}"


class PSSRObservation(models.Model):
    COMPLIANCE_CHOICES = [
        ('Completed', 'Completed'),
        ('Pending', 'Pending'),
        ('Omitted', 'Omitted'),
    ]

    RPN_CATEGORY_CHOICES = [
        ('A', 'A'),
        ('B', 'B'),
    ]

    job_record = models.ForeignKey(PSSRJobRecord, on_delete=models.CASCADE, related_name='observations')
    observar = models.CharField(max_length=50, verbose_name="FPR", blank=True,null=True)
    observation = models.TextField(verbose_name="Observation", blank=True,null=True)
    fpr = models.CharField(max_length=50, verbose_name="FPR", blank=True,null=True)
    target_date = models.DateField(null=True, blank=True, verbose_name="Target Date")
    rpn_category = models.CharField(max_length=1, blank=True,null=True, choices=RPN_CATEGORY_CHOICES, verbose_name="RPN Category")
    compliance_status = models.CharField(max_length=20, blank=True,null=True, choices=COMPLIANCE_CHOICES, verbose_name="Compliance Status")
    compliance_date = models.DateField(verbose_name="Compliance Date", blank=True,null=True)

    class Meta:
        db_table = 'pssr_observation'
        verbose_name = 'PSSR Observation'
        verbose_name_plural = 'PSSR Observations'

    def __str__(self):
        return f"{self.job_record} - Obs. {self.observation_no}"