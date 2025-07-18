# Generated by Django 5.0.11 on 2025-06-17 12:10

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AppearanceOption",
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
                ("name", models.CharField(max_length=200, unique=True)),
            ],
            options={
                "verbose_name": "Appearance Option",
                "verbose_name_plural": "Appearance Options",
                "db_table": "qc_appearance_option",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="LocalBOMDetail",
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
                ("sr_no", models.IntegerField()),
                ("itm_type", models.CharField(max_length=200)),
                ("item_name", models.CharField(max_length=200)),
                ("fg_name", models.CharField(blank=True, max_length=200, null=True)),
                ("item_code", models.CharField(max_length=50)),
                ("quantity", models.DecimalField(decimal_places=6, max_digits=18)),
                ("bom_code", models.CharField(max_length=50)),
                ("bom_name", models.CharField(max_length=200)),
                ("type", models.CharField(max_length=200)),
                ("bom_item_code", models.CharField(max_length=50)),
                ("name", models.CharField(max_length=200)),
                ("unit", models.CharField(max_length=100)),
                ("bom_qty", models.DecimalField(decimal_places=6, max_digits=18)),
                ("cflag", models.CharField(max_length=5)),
            ],
        ),
        migrations.CreateModel(
            name="LocalEquipmentMaster",
            fields=[
                (
                    "eqp_code",
                    models.CharField(
                        help_text="ERP’s unique equipment ID.",
                        max_length=50,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "eqp_name",
                    models.CharField(
                        help_text="ERP’s equipment name/description.", max_length=200
                    ),
                ),
                (
                    "eqp_remarks",
                    models.CharField(
                        blank=True,
                        help_text="Optional remarks or notes from ERP.",
                        max_length=500,
                        null=True,
                    ),
                ),
                (
                    "unit_code",
                    models.CharField(
                        blank=True,
                        help_text="Optional unit code (e.g. department or plant).",
                        max_length=50,
                        null=True,
                    ),
                ),
                (
                    "tag_no",
                    models.CharField(
                        blank=True,
                        help_text="Optional tag number for this equipment.",
                        max_length=100,
                        null=True,
                    ),
                ),
                (
                    "block_name",
                    models.CharField(
                        blank=True,
                        help_text="If applicable, the block or area name this equipment is in.",
                        max_length=100,
                        null=True,
                    ),
                ),
            ],
            options={
                "verbose_name": "Local Equipment Master",
                "verbose_name_plural": "Local Equipment Masters",
                "db_table": "qc_localequipmentmaster",
                "ordering": ["eqp_name"],
            },
        ),
        migrations.CreateModel(
            name="LocalItemMaster",
            fields=[
                (
                    "product_id",
                    models.CharField(
                        help_text="ERP’s unique product ID.",
                        max_length=50,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "product_name",
                    models.CharField(
                        help_text="ERP’s product description/name.", max_length=200
                    ),
                ),
                (
                    "item_type",
                    models.CharField(
                        help_text="ERP’s item type/category.", max_length=100
                    ),
                ),
            ],
            options={
                "verbose_name": "Local Item Master",
                "verbose_name_plural": "Local Item Masters",
                "db_table": "qc_localitemmaster",
                "ordering": ["product_name"],
            },
        ),
        migrations.CreateModel(
            name="BmrIssue",
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
                (
                    "bmr_issue_type",
                    models.CharField(
                        help_text="ERP’s BMR Issue Type (e.g. Fresh Batch, Cleaning, etc.).",
                        max_length=100,
                    ),
                ),
                (
                    "bmr_issue_no",
                    models.CharField(
                        help_text="ERP’s document number for the BMR Issue.",
                        max_length=100,
                    ),
                ),
                (
                    "bmr_issue_date",
                    models.DateField(help_text="Date of the BMR Issue in ERP."),
                ),
                (
                    "fg_name",
                    models.CharField(help_text="Finished Goods name.", max_length=200),
                ),
                (
                    "op_batch_no",
                    models.CharField(
                        help_text="ERP’s “Output Batch Number” to filter on.",
                        max_length=100,
                    ),
                ),
                (
                    "product_name",
                    models.CharField(
                        blank=True,
                        help_text="ERP’s Product Name if available.",
                        max_length=200,
                        null=True,
                    ),
                ),
                (
                    "block",
                    models.CharField(
                        blank=True,
                        help_text="ERP’s Block value if available.",
                        max_length=200,
                        null=True,
                    ),
                ),
                (
                    "line_no",
                    models.IntegerField(
                        help_text="Line number within the BMR Issue (ERP detail row)."
                    ),
                ),
                (
                    "item_type",
                    models.CharField(
                        help_text="ERP’s item type description.", max_length=100
                    ),
                ),
                (
                    "item_code",
                    models.CharField(help_text="ERP’s item code.", max_length=100),
                ),
                (
                    "item_name",
                    models.CharField(help_text="ERP’s item name.", max_length=200),
                ),
                (
                    "item_narration",
                    models.TextField(
                        blank=True,
                        help_text="Optional narration/remarks from ERP.",
                        null=True,
                    ),
                ),
                (
                    "uom",
                    models.CharField(help_text="Unit of measure code.", max_length=50),
                ),
                (
                    "batch_quantity",
                    models.DecimalField(
                        decimal_places=3,
                        help_text="Quantity (in ERP) for this line.",
                        max_digits=18,
                    ),
                ),
            ],
            options={
                "verbose_name": "BMR Issue",
                "verbose_name_plural": "BMR Issues",
                "db_table": "qc_bmr_issue",
                "ordering": ["bmr_issue_no", "line_no"],
                "unique_together": {("bmr_issue_no", "line_no")},
            },
        ),
        migrations.CreateModel(
            name="Product",
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
                ("name", models.CharField(max_length=200)),
                ("code", models.CharField(blank=True, max_length=50)),
                ("item_type", models.CharField(blank=True, max_length=100)),
                (
                    "stages",
                    models.CharField(
                        blank=True,
                        help_text="Comma-separated list of stages",
                        max_length=200,
                    ),
                ),
                (
                    "appearance_options",
                    models.ManyToManyField(
                        blank=True, related_name="products", to="QC.appearanceoption"
                    ),
                ),
            ],
            options={
                "db_table": "qc_product",
            },
        ),
        migrations.CreateModel(
            name="QCEntry",
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
                (
                    "decision_status",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("approved", "Approved"),
                            ("approved_under_deviation", "Approved under deviation"),
                            ("rejected", "Rejected"),
                        ],
                        help_text="QC decision: approved, approved under deviation, or rejected",
                        max_length=30,
                        null=True,
                    ),
                ),
                (
                    "entry_no",
                    models.PositiveIntegerField(
                        editable=False,
                        help_text="Automatically assigned sequential entry number.",
                        null=True,
                        unique=True,
                    ),
                ),
                (
                    "block",
                    models.CharField(
                        blank=True,
                        help_text="Auto-populated when an equipment is chosen.",
                        max_length=50,
                    ),
                ),
                (
                    "equipment_id",
                    models.CharField(
                        blank=True,
                        help_text="Select which equipment/batch line this QC pertains to.",
                        max_length=50,
                    ),
                ),
                (
                    "test_required_for",
                    models.CharField(
                        blank=True,
                        help_text="Why this QC is being performed.",
                        max_length=100,
                        verbose_name="Test Required For",
                    ),
                ),
                (
                    "stage",
                    models.CharField(
                        choices=[
                            ("raw", "Raw Material"),
                            ("inproc_1", "In-Process Stage 1"),
                            ("inproc_2", "In-Process Stage 2"),
                            ("finished", "Finished Goods"),
                        ],
                        help_text="At which stage of production this sample was taken.",
                        max_length=100,
                    ),
                ),
                (
                    "prod_sign_date",
                    models.DateField(
                        blank=True,
                        help_text="Date when Production signed off on this batch.",
                        null=True,
                    ),
                ),
                (
                    "batch_no",
                    models.CharField(
                        blank=True,
                        help_text="Batch number (pulled from ERP BMR).",
                        max_length=100,
                    ),
                ),
                (
                    "sample_received_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="When Production delivered the sample to QC.",
                        null=True,
                        verbose_name="Sample received at QC",
                    ),
                ),
                (
                    "entry_date",
                    models.DateTimeField(
                        default=django.utils.timezone.now,
                        help_text="Date/time when this QC entry was created.",
                    ),
                ),
                (
                    "ar_no",
                    models.CharField(
                        blank=True,
                        help_text="Analysis Request number assigned by Production.",
                        max_length=100,
                        verbose_name="AR No.",
                    ),
                ),
                (
                    "sample_sent_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="Date/time when sample was sent for analysis.",
                        null=True,
                    ),
                ),
                (
                    "sample_description",
                    models.TextField(
                        blank=True,
                        help_text="Short description or notes about the sample.",
                        verbose_name="Sample Description",
                    ),
                ),
                (
                    "release_by_qc_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="When QC officially released the batch.",
                        null=True,
                        verbose_name="Sample Released from QC",
                    ),
                ),
                ("created", models.DateTimeField(auto_now_add=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft (Production)"),
                            ("pending_qc", "Pending QC"),
                            ("qc_completed", "QC Completed"),
                            ("cancelled", "Cancelled"),
                        ],
                        default="draft",
                        help_text="draft → pending_qc → qc_completed/cancelled",
                        max_length=20,
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        help_text="Production user who created this entry.",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="qc_created_entries",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        help_text="Select the product for which you’re generating this QC entry.",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="QC.product",
                    ),
                ),
                (
                    "qc_completed_by",
                    models.ForeignKey(
                        blank=True,
                        help_text="QC user who completed the results.",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="qc_entries_completed",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "qc_entry",
                "ordering": ["-created"],
            },
        ),
        migrations.CreateModel(
            name="Spec",
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
                ("name", models.CharField(max_length=100)),
                (
                    "spec_type",
                    models.CharField(
                        choices=[
                            ("numeric", "Numeric Range"),
                            ("choice", "Choice List"),
                            ("text", "Free‐Text"),
                        ],
                        default="numeric",
                        help_text="Choose whether this spec uses a numeric range, a set of choices, or free text.",
                        max_length=10,
                    ),
                ),
                (
                    "min_val",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=8, null=True
                    ),
                ),
                (
                    "max_val",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=8, null=True
                    ),
                ),
                (
                    "allowed_choices",
                    models.TextField(
                        blank=True,
                        help_text="(Choice type only) Comma‐separate the allowed text values, e.g. “Brown liquid,Clear liquid,White powder”",
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="specs",
                        to="QC.product",
                    ),
                ),
            ],
            options={
                "db_table": "qc_spec",
                "unique_together": {("product", "name")},
            },
        ),
        migrations.CreateModel(
            name="SpecEntry",
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
                (
                    "value",
                    models.CharField(
                        blank=True,
                        help_text="Result for this spec: numeric or free-text (e.g. appearance).",
                        max_length=200,
                        null=True,
                    ),
                ),
                (
                    "remark",
                    models.TextField(
                        blank=True,
                        help_text="Automatically set to 'Pass' or 'Fail' based on min/max, or left blank.",
                    ),
                ),
                (
                    "qc_entry",
                    models.ForeignKey(
                        help_text="The QCEntry to which this particular specification result belongs.",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="values",
                        to="QC.qcentry",
                    ),
                ),
                (
                    "spec",
                    models.ForeignKey(
                        help_text="Which specification (test parameter) this result is for.",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="QC.spec",
                    ),
                ),
            ],
            options={
                "db_table": "qc_spec_entry",
                "ordering": ["qc_entry", "spec"],
                "unique_together": {("qc_entry", "spec")},
            },
        ),
    ]
