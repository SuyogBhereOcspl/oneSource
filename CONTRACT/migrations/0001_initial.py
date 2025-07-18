# Generated by Django 5.0.11 on 2025-06-24 05:48

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ContractorManpowerAttendance",
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
                ("date", models.DateField()),
                (
                    "contractor",
                    models.CharField(
                        choices=[
                            ("Aldar", "Aldar"),
                            ("Yash", "Yash"),
                            ("ACP", "ACP"),
                            ("HE", "HE"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "shift",
                    models.CharField(
                        choices=[("A", "A"), ("G", "G"), ("B", "B"), ("C", "C")],
                        max_length=1,
                    ),
                ),
                (
                    "a_block",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        default=0.0,
                        max_digits=5,
                        null=True,
                    ),
                ),
                (
                    "b_block",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        default=0.0,
                        max_digits=5,
                        null=True,
                    ),
                ),
                (
                    "c_block",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        default=0.0,
                        max_digits=5,
                        null=True,
                    ),
                ),
                (
                    "d_block",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        default=0.0,
                        max_digits=5,
                        null=True,
                    ),
                ),
                (
                    "pkg",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        default=0.0,
                        max_digits=5,
                        null=True,
                    ),
                ),
                (
                    "pilot",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        default=0.0,
                        max_digits=5,
                        null=True,
                    ),
                ),
                (
                    "e_bolck_17_production",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        default=0.0,
                        max_digits=5,
                        null=True,
                    ),
                ),
                (
                    "mee_etp",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        default=0.0,
                        max_digits=5,
                        null=True,
                    ),
                ),
                (
                    "ro_plant",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        default=0.0,
                        max_digits=5,
                        null=True,
                    ),
                ),
                (
                    "mnts",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        default=0.0,
                        max_digits=5,
                        null=True,
                    ),
                ),
                (
                    "ele",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        default=0.0,
                        max_digits=5,
                        null=True,
                    ),
                ),
                (
                    "inst",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        default=0.0,
                        max_digits=5,
                        null=True,
                    ),
                ),
                (
                    "rm_engg_16_17_18",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        default=0.0,
                        max_digits=5,
                        null=True,
                    ),
                ),
                (
                    "qc_pd",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        default=0.0,
                        max_digits=5,
                        null=True,
                    ),
                ),
                (
                    "boiler",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        default=0.0,
                        max_digits=5,
                        null=True,
                    ),
                ),
                (
                    "dozer_driver",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        default=0.0,
                        max_digits=5,
                        null=True,
                    ),
                ),
                (
                    "housekeeping_16_17_18",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        default=0.0,
                        max_digits=5,
                        null=True,
                    ),
                ),
                (
                    "office_boy",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        default=0.0,
                        max_digits=5,
                        null=True,
                    ),
                ),
                (
                    "gardenar",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        default=0.0,
                        max_digits=5,
                        null=True,
                    ),
                ),
                (
                    "ohc",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        default=0.0,
                        max_digits=5,
                        null=True,
                    ),
                ),
                (
                    "painting",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        default=0.0,
                        max_digits=5,
                        null=True,
                    ),
                ),
                (
                    "mnts_e17",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        default=0.0,
                        max_digits=5,
                        null=True,
                    ),
                ),
                (
                    "ele_e17",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        default=0.0,
                        max_digits=5,
                        null=True,
                    ),
                ),
                (
                    "inst_e17",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        default=0.0,
                        max_digits=5,
                        null=True,
                    ),
                ),
            ],
            options={
                "db_table": "contractor_manpower_attendance",
            },
        ),
        migrations.CreateModel(
            name="DepartmentManpowerRequirement",
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
                ("department_name", models.CharField(max_length=50, unique=True)),
                ("required_manpower", models.PositiveIntegerField(default=0)),
            ],
            options={
                "db_table": "department_manpower_requirement",
            },
        ),
        migrations.CreateModel(
            name="ContractorDailyRequirement",
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
                ("date", models.DateField()),
                (
                    "contractor",
                    models.CharField(
                        choices=[
                            ("Aldar", "Aldar"),
                            ("Yash", "Yash"),
                            ("ACP", "ACP"),
                            ("HE", "HE"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "contractor_required_total",
                    models.PositiveIntegerField(blank=True, default=0, null=True),
                ),
            ],
            options={
                "db_table": "contractor_daily_requirement",
                "unique_together": {("date", "contractor")},
            },
        ),
    ]
