from django.db import models


# Create your models here.

class HR(models.Model):
    date = models.DateField()
    permanent_employees = models.IntegerField()
    contract_labour_production = models.IntegerField()
    contract_labour_others = models.IntegerField()
    total_employee = models.IntegerField()
    hrs = models.IntegerField(default=0)
    total_no_of_hrs = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'HR'

        
    def __str__(self):
        return f"HR Record on {self.date}"


class DailyAttendance(models.Model):
    employee_code = models.CharField(max_length=10)
    full_name = models.CharField(max_length=100)
    employment_status = models.CharField(max_length=50)
    company = models.CharField(max_length=100)
    business_unit = models.CharField(max_length=100, null=True, blank=True)
    department = models.CharField(max_length=50)
    designation = models.CharField(max_length=100, null=True, blank=True)
    branch = models.CharField(max_length=50)
    sub_branch = models.CharField(max_length=50)
    attendance_date = models.DateField()
    punch_in_punch_out_time = models.CharField(max_length=20,null=True)
    status_in_out = models.CharField(max_length=20)
    shift_code = models.CharField(max_length=50)
    shift_timing = models.CharField(max_length=20)
    Late_or_early = models.CharField(max_length=50,null=True)
    working_hours = models.CharField(max_length=10,null=True)
    total_office_hours = models.CharField(max_length=10, null=True, blank=True)
    source = models.CharField(max_length=100, null=True, blank=True)
    date_of_joining = models.DateField(null=True, blank=True)
    employment_type = models.CharField(max_length=50, null=True, blank=True)
    grade = models.CharField(max_length=20, null=True, blank=True)
    lattitude_longitude = models.CharField(max_length=200, null=True, blank=True)
    level = models.CharField(max_length=50, null=True, blank=True)
    location = models.CharField(max_length=500, null=True, blank=True)
    mobile = models.CharField(max_length=10, null=True, blank=True)
    region = models.CharField(max_length=20, null=True, blank=True)
    reporting_manager = models.CharField(max_length=100, null=True, blank=True)
    work_email = models.EmailField(null=True, blank=True)

    class Meta:
        db_table = 'daily_attendance'

    # def __str__(self):
        # return f"{self.full_name} ({self.attendance_date})"


class AttendanceRegulation(models.Model):
    employee_code = models.CharField(max_length=10)
    full_name = models.CharField(max_length=100)
    employment_status = models.CharField(max_length=50)
    company = models.CharField(max_length=100)
    business_unit = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)
    branch = models.CharField(max_length=50)
    sub_branch = models.CharField(max_length=50)
    request_type = models.CharField(max_length=50)
    attendance_date = models.DateField()
    attendance_day = models.CharField(max_length=20)
    reason = models.CharField(max_length=200)
    shift_code = models.CharField(max_length=50)
    shift_timings = models.CharField(max_length=20)
    actual_punch_in_out = models.CharField(max_length=100, null=True, blank=True)
    punch_in_date = models.DateField(null=True, blank=True)
    punch_in_time = models.CharField(max_length=10, null=True, blank=True)
    punch_out_date = models.DateField(null=True, blank=True)
    punch_out_time = models.CharField(max_length=10, null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)
    request_status = models.CharField(max_length=20)
    requested_by = models.CharField(max_length=100)
    requested_on = models.DateField()
    approved_by = models.CharField(max_length=100, null=True, blank=True)
    approved_on = models.DateField(null=True, blank=True)
    approver_remark = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'attendance_regulation'

    def __str__(self):
        return f"{self.full_name} - {self.attendance_date} ({self.request_status})"


class DailyCheckIn(models.Model):
    employee_code = models.CharField(max_length=10)
    full_name = models.CharField(max_length=100)
    employment_status = models.CharField(max_length=50)
    company = models.CharField(max_length=100)
    business_unit = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)
    branch = models.CharField(max_length=100)
    sub_branch = models.CharField(max_length=100)
    attendance_date = models.DateField()
    shift = models.CharField(max_length=100, null=True, blank=True)
    check_in = models.CharField(max_length=10, null=True, blank=True)
    source = models.CharField(max_length=150, null=True, blank=True)
    first_punch = models.TimeField(max_length=10, null=True, blank=True)
    last_punch = models.TimeField(max_length=10, null=True, blank=True)
    raw_punch = models.CharField(max_length=255,null=True,blank=True)  # Assuming multiple punch times could be stored as a comma-separated string

    class Meta:
        db_table = 'daily_check_in'

    def __str__(self):
        return f"{self.full_name} ({self.employee_code})"



class Late_Early_Go(models.Model):
    employee_code = models.CharField(max_length=10)
    full_name = models.CharField(max_length=100)
    employment_status = models.CharField(max_length=50)
    company = models.CharField(max_length=100)
    business_unit = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)
    branch = models.CharField(max_length=50)
    sub_branch = models.CharField(max_length=50)
    late_early = models.CharField(max_length=50)
    attendance_date = models.DateField()
    late_early_by_min = models.IntegerField()
    shift_code = models.CharField(max_length=50)
    shift_timings = models.CharField(max_length=50)

    class Meta:
        db_table = 'late_early_go'

    def __str__(self):
        return f"{self.full_name} ({self.employee_code})"
    

class On_Duty_Request(models.Model):
    employee_code = models.CharField(max_length=20)
    full_name = models.CharField(max_length=100)
    employment_status = models.CharField(max_length=50)
    company = models.CharField(max_length=100)
    business_unit = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)
    branch = models.CharField(max_length=50)
    sub_branch = models.CharField(max_length=50)
    request_type = models.CharField(max_length=50)
    attendance_date = models.DateField()
    attendance_day = models.CharField(max_length=15)
    on_duty_type = models.CharField(max_length=50, blank=True, null=True)
    shift_code = models.CharField(max_length=50)
    shift_timings = models.CharField(max_length=50)
    actual_punch_in_out = models.CharField(max_length=50, blank=True, null=True)
    punch_in_date = models.DateField(blank=True, null=True)
    punch_out_date = models.DateField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    request_status = models.CharField(max_length=50)
    request_by = models.CharField(max_length=100)
    request_on = models.DateTimeField()
    pending_with = models.CharField(max_length=100, blank=True, null=True)
    approved_by = models.CharField(max_length=100, blank=True, null=True)
    approved_on = models.DateTimeField(blank=True, null=True)
    approver_remark = models.TextField(blank=True, null=True)
    billable_type = models.CharField(max_length=50, blank=True, null=True)
    punch_in_timing = models.CharField(max_length=20, blank=True, null=True)
    punch_out_timing = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        db_table = 'on_duty_request'


    def __str__(self):
        return f"{self.employee_code} - {self.attendance_date}"




class OvertimeReport(models.Model):
    employee_code = models.CharField(max_length=20)
    full_name = models.CharField(max_length=100)
    employment_status = models.CharField(max_length=50)
    company = models.CharField(max_length=100)
    business_unit = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)
    branch = models.CharField(max_length=50)
    sub_branch = models.CharField(max_length=50)
    attendance_date = models.DateField()
    attendance_day = models.CharField(max_length=15)
    shift_code = models.CharField(max_length=50)
    shift = models.CharField(max_length=100)
    shift_timings = models.CharField(max_length=50)
    punch_in_time = models.CharField(max_length=10)
    punch_out_time = models.CharField(max_length=10)
    working_hours = models.CharField(max_length=10)
    overtime_hours = models.CharField(max_length=10)
    request_status = models.CharField(max_length=50)
    request_by = models.CharField(max_length=100)
    request_on = models.DateTimeField(blank=True, null=True)
    pending_with = models.CharField(max_length=200, blank=True, null=True)
    approved_by = models.CharField(max_length=100, blank=True, null=True)
    approved_on = models.DateTimeField(blank=True, null=True)
    approver_remark = models.TextField(blank=True, null=True)
    overtime_minutes = models.IntegerField()

    class Meta:
        db_table = 'overtime_report'

    def __str__(self):
        return f"{self.employee_code} - {self.full_name}"



class ShortLeave(models.Model):
    employee_code = models.CharField(max_length=20)
    full_name = models.CharField(max_length=100)
    employment_status = models.CharField(max_length=50)
    company = models.CharField(max_length=100)
    business_unit = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)
    branch = models.CharField(max_length=50)
    sub_branch = models.CharField(max_length=50)
    request_type = models.CharField(max_length=50)
    attendance_date = models.DateField()
    attendance_day = models.CharField(max_length=15)
    shift_code = models.CharField(max_length=50)
    shift_timings = models.CharField(max_length=50)
    actual_punch_in_out = models.CharField(max_length=50, blank=True, null=True)
    punch_in_date = models.DateField()
    punch_in_timing = models.CharField(max_length=10)
    punch_out_date = models.DateField()
    punch_out_timing = models.CharField(max_length=10)
    remarks = models.TextField(blank=True, null=True)
    request_status = models.CharField(max_length=50)
    request_by = models.CharField(max_length=100)
    request_on = models.DateField()
    pending_with = models.CharField(max_length=100, blank=True, null=True)
    approved_by = models.CharField(max_length=100, blank=True, null=True)
    approved_on = models.DateField(blank=True, null=True)
    approver_remark = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'short_leave'

    def __str__(self):
        return f"{self.employee_code} - {self.full_name}"




class Helpdesk_Ticket(models.Model):
    employee_code = models.CharField(max_length=20)
    full_name = models.CharField(max_length=100)
    employment_status = models.CharField(max_length=50)
    company = models.CharField(max_length=100)
    business_unit = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)
    branch = models.CharField(max_length=50)
    sub_branch = models.CharField(max_length=50)
    ticket_id = models.CharField(max_length=100)
    ticket_details = models.TextField()
    category = models.CharField(max_length=100)
    sub_category = models.CharField(max_length=100)
    priority = models.CharField(max_length=20)
    status = models.CharField(max_length=20)
    raised_on = models.DateTimeField()
    assigned_to = models.CharField(max_length=100)
    pending_with = models.CharField(max_length=100, blank=True, null=True)
    closed_by = models.CharField(max_length=100, blank=True, null=True)
    closed_on = models.DateTimeField(blank=True, null=True)
    is_closed_on_time = models.CharField(max_length=10,blank=True, null=True)
    feedback_rating = models.CharField(max_length=50,blank=True, null=True)
    was_ticket_escalated = models.CharField(max_length=10)
    escalated_to = models.CharField(max_length=100, blank=True, null=True)
    rca = models.TextField(blank=True, null=True)
    time_to_close = models.CharField(max_length=100,blank=True, null=True)

    class Meta:
        db_table = 'helpdesk_ticket'

    def __str__(self):
        return f"{self.ticket_id} - {self.full_name}"