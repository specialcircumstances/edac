# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-09-10 10:53
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('edacapi', '0003_auto_20160910_1108'),
    ]

    operations = [
        migrations.AddField(
            model_name='system',
            name='allegiance',
            field=models.CharField(blank=True, default='', max_length=16),
        ),
        migrations.AddField(
            model_name='system',
            name='eddbdate',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='system',
            name='eddbid',
            field=models.IntegerField(blank=True, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='system',
            name='faction',
            field=models.CharField(blank=True, db_index=True, default='', max_length=64),
        ),
        migrations.AddField(
            model_name='system',
            name='government',
            field=models.CharField(blank=True, default='', max_length=16),
        ),
        migrations.AddField(
            model_name='system',
            name='is_populated',
            field=models.NullBooleanField(),
        ),
        migrations.AddField(
            model_name='system',
            name='needs_permit',
            field=models.NullBooleanField(),
        ),
        migrations.AddField(
            model_name='system',
            name='population',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='system',
            name='power',
            field=models.CharField(blank=True, default='', max_length=32),
        ),
        migrations.AddField(
            model_name='system',
            name='power_state',
            field=models.CharField(blank=True, default='', max_length=16),
        ),
        migrations.AddField(
            model_name='system',
            name='reserve_type',
            field=models.CharField(blank=True, default='', max_length=32),
        ),
        migrations.AddField(
            model_name='system',
            name='security',
            field=models.CharField(blank=True, default='', max_length=8),
        ),
        migrations.AddField(
            model_name='system',
            name='simbad_ref',
            field=models.CharField(blank=True, db_index=True, default='', max_length=64),
        ),
        migrations.AddField(
            model_name='system',
            name='state',
            field=models.CharField(blank=True, default='', max_length=16),
        ),
        migrations.AlterField(
            model_name='system',
            name='edsmid',
            field=models.IntegerField(blank=True, null=True, unique=True),
        ),
    ]
