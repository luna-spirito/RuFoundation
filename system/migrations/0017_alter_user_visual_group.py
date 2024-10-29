# Generated by Django 5.0.6 on 2024-10-24 01:43

import auto_prefetch
import django.db.models.deletion
from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('system', '0016_visualusergroup_index'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='visual_group',
            field=auto_prefetch.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='system.visualusergroup', verbose_name='Визуальная группа'),
        ),
    ]
