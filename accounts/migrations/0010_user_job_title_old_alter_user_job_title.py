# Generated by Django 4.2.7 on 2025-07-18 02:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0004_employeeprofile_job_title_old_jobtitle_and_more'),
        ('accounts', '0009_add_automatic_sync_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='job_title_old',
            field=models.CharField(blank=True, help_text='Temporary field for migration', max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='job_title',
            field=models.ForeignKey(blank=True, help_text='User job title/position', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='users', to='employees.jobtitle'),
        ),
    ]
