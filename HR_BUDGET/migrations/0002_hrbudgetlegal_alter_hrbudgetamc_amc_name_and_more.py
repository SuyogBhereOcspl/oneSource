# Generated by Django 5.0.11 on 2025-07-12 08:05

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("HR_BUDGET", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="HRBudgetLegal",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("invoice_date", models.DateField()),
                ("invoice_no", models.CharField(blank=True, max_length=50, null=True)),
                ("name", models.CharField(blank=True, max_length=50, null=True)),
                (
                    "gst",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=12, null=True
                    ),
                ),
                (
                    "bill_amount",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=12, null=True
                    ),
                ),
                ("description", models.TextField(blank=True, null=True)),
            ],
            options={
                "db_table": "hrbudget_legal",
            },
        ),
        migrations.AlterField(
            model_name="hrbudgetamc",
            name="amc_name",
            field=models.CharField(
                blank=True,
                choices=[
                    ("UNITY  SERVICE", "UNITY  SERVICE"),
                    ("BADAMIKAR & SON", "BADAMIKAR & SON"),
                    ("Other", "Other"),
                ],
                max_length=50,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="hrbudgetcanteen",
            name="name",
            field=models.CharField(
                choices=[
                    ("Balaji Tea Corner", "Balaji Tea Corner"),
                    ("Dayanand Mhetre", "Dayanand Mhetre"),
                    ("Ambika Pure Wage", "Ambika Pure Wage"),
                    ("Tea & Biscuit", "Tea & Biscuit"),
                ],
                max_length=100,
            ),
        ),
        migrations.AlterField(
            model_name="hrbudgetgeneraladmin",
            name="category",
            field=models.CharField(
                choices=[
                    ("Printing", "Printing"),
                    ("Stationary", "Stationary"),
                    ("Cleaning Material", "Cleaning Material"),
                    ("Harshada Courier Services", "Harshada Courier Services"),
                    ("Courier (Sample to Vasai)", "Courier (Sample to Vasai)"),
                    ("Pest Control", "Pest Control"),
                    (
                        "Sunshine Services Xerox Conon E-16 Admin",
                        "Sunshine Services Xerox Conon E-16 Admin",
                    ),
                    (
                        "Sunshine Services Xerox Conon QC Lab",
                        "Sunshine Services Xerox Conon QC Lab",
                    ),
                    (
                        "Sunshine Services Xerox Conon E-18 Admin",
                        "Sunshine Services Xerox Conon E-18 Admin",
                    ),
                    (
                        "Sunshine Services Xerox Conon E-17 Admin",
                        "Sunshine Services Xerox Conon E-17 Admin",
                    ),
                    ("Fridge repairing", "Fridge repairing"),
                    ("Water bottle", "Water bottle"),
                    ("Aquaguard/RO", "Aquaguard/RO"),
                    (
                        "Balanand Kirana / Shri Datta Kirana (Jagerry)",
                        "Balanand Kirana / Shri Datta Kirana (Jagerry)",
                    ),
                    ("Pantry", "Pantry"),
                    ("Conveyance", "Conveyance"),
                    ("Post Office", "Post Office"),
                    ("Night round police", "Night round police"),
                    ("Air Conditioner - Services", "Air Conditioner - Services"),
                    ("Furniture", "Furniture"),
                    ("Mahi Jal", "Mahi Jal"),
                    ("Other", "Other"),
                ],
                max_length=100,
            ),
        ),
        migrations.AlterField(
            model_name="hrbudgetmedical",
            name="doctor_hospital_name",
            field=models.CharField(
                choices=[
                    ("Dr. Ganesh Atwade(FMO)", "Dr. Ganesh Atwade(FMO)"),
                    ("Baladava Hospital", "Baladava Hospital"),
                    ("Dr. Chidgupkar Hospital", "Dr. Chidgupkar Hospital"),
                    ("Shilpakaya Hospital", "Shilpakaya Hospital"),
                    ("Doctor Ukarande", "Doctor Ukarande"),
                    ("Medicines for OHC", "Medicines for OHC"),
                    ("New joinee health check up", "New joinee health check up"),
                    ("Annual Health Check up", "Annual Health Check up"),
                ],
                max_length=150,
            ),
        ),
    ]
