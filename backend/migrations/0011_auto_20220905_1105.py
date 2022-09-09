# Generated by Django 2.2.15 on 2022-09-05 11:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0010_smartsolardata_device_type'),
    ]

    operations = [
        migrations.RenameField(
            model_name='smartsolardata',
            old_name='energy_meter_log_time',
            new_name='energy_time_log',
        ),
        migrations.RenameField(
            model_name='smartsolardata',
            old_name='inverter_log_time',
            new_name='inv_time_log',
        ),
        migrations.AddField(
            model_name='smartsolardata',
            name='location',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
    ]
