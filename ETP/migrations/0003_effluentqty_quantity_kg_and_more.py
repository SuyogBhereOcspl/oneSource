# Generated by Django 5.0.11 on 2025-05-20 16:05

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ETP", "0002_remove_generaleffluent_category_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="effluentqty",
            name="quantity_kg",
            field=models.FloatField(blank=True, default=0.0, null=True),
        ),
        migrations.AlterField(
            model_name="effluentqty",
            name="actual_quantity",
            field=models.FloatField(blank=True, default=0.0, null=True),
        ),
        migrations.AlterField(
            model_name="effluentqty",
            name="plan_quantity",
            field=models.FloatField(blank=True, default=0.0, null=True),
        ),
        migrations.AlterField(
            model_name="effluentrecord",
            name="record_date",
            field=models.DateField(default=datetime.date.today),
        ),
    ]
