from django.db import models

# Create your models here.

class DepartmentManpowerRequirement(models.Model):
    department_name = models.CharField(max_length=50, unique=True)
    required_manpower = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'department_manpower_requirement'

    def __str__(self):
        return f"{self.department_name} - {self.required_manpower}"


CONTRACT_NAME_CHOICES = [
    ("Aldar", "Aldar"),
    ("Yash", "Yash"),
    ("ACP", "ACP"),
    ("HE", "HE"),
]


SHIFT_CHOICES = [('A', 'A'), ('G', 'G'), ('B', 'B'), ('C', 'C')]

class ContractorManpowerAttendance(models.Model):
    date = models.DateField()
    contractor = models.CharField(max_length=20, choices=CONTRACT_NAME_CHOICES)
    shift = models.CharField(max_length=1, choices=SHIFT_CHOICES)
    # Department-wise manpower (actual)
    a_block = models.DecimalField(max_digits=5, decimal_places=3, default=0.00, blank=True, null=True)
    b_block = models.DecimalField(max_digits=5, decimal_places=3, default=0.00, blank=True, null=True)
    c_block = models.DecimalField(max_digits=5, decimal_places=3, default=0.00, blank=True, null=True)
    d_block = models.DecimalField(max_digits=5, decimal_places=3, default=0.00, blank=True, null=True)
    pkg = models.DecimalField(max_digits=5, decimal_places=3, default=0.00, blank=True, null=True)
    pilot = models.DecimalField(max_digits=5, decimal_places=3, default=0.00, blank=True, null=True)
    e_block_17_production = models.DecimalField(max_digits=5, decimal_places=3, default=0.00, blank=True, null=True)
    mee_etp = models.DecimalField(max_digits=5, decimal_places=3, default=0.00, blank=True, null=True)
    ro_plant = models.DecimalField(max_digits=5, decimal_places=3, default=0.00, blank=True, null=True)
    mnts = models.DecimalField(max_digits=5, decimal_places=3, default=0.00, blank=True, null=True)
    ele = models.DecimalField(max_digits=5, decimal_places=3, default=0.00, blank=True, null=True)
    inst = models.DecimalField(max_digits=5, decimal_places=3, default=0.00, blank=True, null=True)
    rm_engg_16_17_18 = models.DecimalField(max_digits=5, decimal_places=3, default=0.00, blank=True, null=True)
    qc_pd = models.DecimalField(max_digits=5, decimal_places=3, default=0.00, blank=True, null=True)
    boiler = models.DecimalField(max_digits=5, decimal_places=3, default=0.00, blank=True, null=True)
    dozer_driver = models.DecimalField(max_digits=5, decimal_places=3, default=0.00, blank=True, null=True)
    housekeeping_16_17_18 = models.DecimalField(max_digits=5, decimal_places=3, default=0.00, blank=True, null=True)
    office_boy = models.DecimalField(max_digits=5, decimal_places=3, default=0.00, blank=True, null=True)
    gardenar = models.DecimalField(max_digits=5, decimal_places=3, default=0.00, blank=True, null=True)
    ohc = models.DecimalField(max_digits=5, decimal_places=3, default=0.00, blank=True, null=True)
    painting = models.DecimalField(max_digits=5, decimal_places=3, default=0.00, blank=True, null=True)
    mnts_e17 = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, blank=True, null=True)
    ele_e17 = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, blank=True, null=True)
    inst_e17 = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, blank=True, null=True)

    class Meta:
        db_table = 'contractor_manpower_attendance'

    def __str__(self):
        return f"{self.date} - {self.contractor} - {self.shift}"


class ContractorReqActManpower(models.Model):
    attendance = models.ForeignKey(ContractorManpowerAttendance, related_name="details", on_delete=models.CASCADE)
    department = models.ForeignKey(DepartmentManpowerRequirement,on_delete=models.CASCADE) 
    required = models.PositiveIntegerField(default=0, blank=True, null=True)
    actual = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, blank=True, null=True)

    class Meta:
        db_table = "contractor_req_act_manpower"


    def __str__(self):
        return f"{self.attendance} - {self.department} ({self.required} / {self.actual})"
        
        
 #=====================================================================================================       


CONTRACTOR_CHOICES = [
    ('Aldar', 'Aldar'),
    ('Yash', 'Yash'),
    ('ACP', 'ACP'),
    ('HE', 'HE'),
]


SHIFT_CHOICES = [
    ('A', 'A'),
    ('G', 'G'),
    ('B', 'B'),
    ('C', 'C'),
]

LOCATION_CHOICES = [
    ('A Block', 'A Block'),
    ('B Block', 'B Block'),
    ('C Block', 'C Block'),
    ('D Block', 'D Block'),
    ('E Block- 17 Production', 'E Block- 17 Production'),
    ('PKG', 'PKG'),
    ('Pilot', 'Pilot'),
    ('MEE/ETP', 'MEE/ETP'),
    ('RO Plant', 'RO Plant'),
    ('MNTS', 'MNTS'),
    ('ELE', 'ELE'),
    ('INST', 'INST'),
    ('RM/ENGG 16 - 17 & 18', 'RM/ENGG 16 - 17 & 18'),
    ('QC & PD', 'QC & PD'),
    ('Boiler', 'Boiler'),
    ('Dozer Driver', 'Dozer Driver'),
    ('HouseKeeping 16 - 17 & 18', 'HouseKeeping 16 - 17 & 18'),
    ('Office Boy', 'Office Boy'),
    ('Gardenar', 'Gardenar'),
    ('OHC', 'OHC'),
    ('Painting', 'Painting'),
    ('MNTS-E 17', 'MNTS-E 17'),
    ('ELE- E-17', 'ELE- E-17'),
    ('INST-E-17', 'INST-E-17'),
]


# Static dropdown options for Department
DEPARTMENT_CHOICES = [
    ('ACCOUNTS', 'ACCOUNTS'),
    ('BOILER UTILITY', 'BOILER UTILITY'),
    ('ELECTRICAL', 'ELECTRICAL'),
    ('EHS', 'EHS'),
    ('HR ADMIN', 'HR ADMIN'),
    ('INSTRUMENT', 'INSTRUMENT'),
    ('IT', 'IT'),
    ('MAINTENANCE', 'MAINTENANCE'),
    ('OPERATION', 'OPERATION'),
    ('PRODUCTION', 'PRODUCTION'),
    ('QA/QC', 'QA/QC'),
    ('SECURITY', 'SECURITY'),
    ('STORE', 'STORE'),
    ('ETP', 'ETP'),
]



class ContractorWorker(models.Model):
    date = models.DateField()
    contractor_name = models.CharField(max_length=20, choices=CONTRACTOR_CHOICES)
    shift = models.CharField(max_length=1, choices=SHIFT_CHOICES)
    location = models.CharField(max_length=50, choices=LOCATION_CHOICES)
    emp_count = models.DecimalField(max_digits=10, decimal_places=3)
    department = models.CharField(max_length=50,choices=DEPARTMENT_CHOICES,blank=True,null=True)

    class Meta:
        db_table = "contractor_worker"

    def __str__(self):
        return f"{self.date} - {self.contractor_name} - Shift {self.shift} - Location {self.location} - Emp Count: {self.emp_count}"



#======================================Below model for cantract punch in attendance  ======================================================



# Create your models here.
class ContractEmpDepartment(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = 'contract_employee_dept'
    def __str__(self):
        return self.name

class ContractEmployee(models.Model):
    id = models.CharField(max_length=50, primary_key=True)  # Employee ID from device/excel
    name = models.CharField(max_length=100)
    employee_type = models.CharField(max_length=50)
    department = models.ForeignKey(ContractEmpDepartment, on_delete=models.CASCADE, related_name='employees')
    
    class Meta:
        db_table = 'contract_employee'
    def __str__(self):
        return self.name