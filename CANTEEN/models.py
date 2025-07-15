from django.db import models
from django.utils import timezone
import pytz

# Replace with your actual timezone
LOCAL_TIMEZONE = pytz.timezone('Asia/Kolkata')  # or any relevant timezone


class Department(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        db_table = 'canteen_employee_dept'

    def __str__(self):
        return self.name

class Employee(models.Model):
    id = models.CharField(primary_key=True,max_length=50)
    name = models.CharField(max_length=100)
    employee_type = models.CharField(max_length=20,null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='employees')
    location = models.CharField(max_length=100, blank=True, null=True) 

    class Meta:
        db_table = 'canteen_employee'

    def __str__(self):
        return self.name
    

class Shift(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=50)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        db_table = 'canteen_shift'

    def __str__(self):
        return self.name

    @property
    def crosses_midnight(self):
        return self.end_time < self.start_time
    

class Attendance(models.Model):
    employee = models.ForeignKey(
        'Employee', on_delete=models.CASCADE, related_name='attendances'
    )
    punched_at = models.DateTimeField(default=timezone.now)
    shift = models.ForeignKey(
        'Shift', on_delete=models.SET_NULL, null=True, blank=True, related_name='attendances'
    )
    meal_type = models.CharField(max_length=50, blank=True, null=True)  # e.g., Breakfast, Lunch
    

    class Meta:
        db_table = 'canteen_attendance'

    def __str__(self):
        return f"{self.employee.name} - {self.punched_at.strftime('%Y-%m-%d %H:%M')}"

    @property
    def punched_at_local(self):
        return self.punched_at.astimezone(LOCAL_TIMEZONE)
    