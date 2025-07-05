# Step 1: Add fields without unique constraint

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_add_azure_ad_sync_error'),
        ('employees', '0002_azure_ad_fields'),
    ]

    operations = [
        # Add new user fields (without unique constraint on employee_id)
        migrations.AddField(
            model_name='user',
            name='company_name',
            field=models.CharField(blank=True, help_text='Company name for Azure AD sync', max_length=100),
        ),
        migrations.AddField(
            model_name='user',
            name='employee_id',
            field=models.CharField(blank=True, help_text='Unique employee identifier', max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='employee_type',
            field=models.CharField(blank=True, choices=[('full_time', 'Full Time'), ('part_time', 'Part Time'), ('contract', 'Contract'), ('temporary', 'Temporary'), ('intern', 'Intern')], help_text='Employment type (synced with Azure AD)', max_length=20),
        ),
        migrations.AddField(
            model_name='user',
            name='end_date',
            field=models.DateField(blank=True, help_text='End date (when applicable)', null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='hire_date',
            field=models.DateField(blank=True, help_text='Date of hire', null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='manager',
            field=models.ForeignKey(blank=True, help_text='Direct manager (synced with Azure AD)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='user_direct_reports', to='accounts.user'),
        ),
        migrations.AddField(
            model_name='user',
            name='office_location',
            field=models.CharField(blank=True, help_text='Office location (synced with Azure AD)', max_length=200),
        ),
        migrations.AddField(
            model_name='user',
            name='start_date',
            field=models.DateField(blank=True, help_text='Start date for current position', null=True),
        ),
        # Update job_title to add help text
        migrations.AlterField(
            model_name='user',
            name='job_title',
            field=models.CharField(blank=True, help_text='Job title (synced with Azure AD)', max_length=100),
        ),
    ]