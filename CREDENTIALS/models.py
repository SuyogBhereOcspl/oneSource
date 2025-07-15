from django.db import models
from django.utils import timezone

class Credentials(models.Model):
    LOCATION_CHOICES = [
        ('head_office', 'Head Office'),
        ('solapur', 'Solapur'),
    ]

    location = models.CharField(max_length=50, choices=LOCATION_CHOICES, blank=True, null=True)
    device = models.CharField(max_length=255, blank=True, null=True)
    lan_ip = models.GenericIPAddressField(blank=True, null=True)
    wan_ip = models.GenericIPAddressField(blank=True, null=True)
    port_no = models.PositiveIntegerField(blank=True, null=True)
    frwd_to = models.CharField(max_length=255, blank=True, null=True)
    url = models.URLField(blank=True, null=True)
    user_name = models.CharField(max_length=150, blank=True, null=True)
    old_password = models.CharField(max_length=255, blank=True, null=True)
    new_password = models.CharField(max_length=255, blank=True, null=True)

    status_CHOICES = [
        ('reset', 'Reset'),
        ('created', 'Created'),
    ]
    status = models.CharField(max_length=20, choices=status_CHOICES, blank=True, null=True)
    action_date = models.DateTimeField(blank=True, null=True)
    expiry_on = models.DateField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.pk:
            orig = Credentials.objects.filter(pk=self.pk).first()
            if orig and orig.status != self.status:
                self.action_date = timezone.now()
        else:
            if self.status and not self.action_date:
                self.action_date = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.location} - {self.device} - {self.user_name}"

    class Meta:
        db_table = 'credentials'