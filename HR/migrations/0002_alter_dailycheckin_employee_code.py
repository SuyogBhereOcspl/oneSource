# Generated by Django 5.0.11 on 2025-04-16 12:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('HR', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dailycheckin',
            name='employee_code',
            field=models.CharField(max_length=10),
        ),
    ]
