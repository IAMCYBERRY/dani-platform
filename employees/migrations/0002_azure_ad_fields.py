# Generated manually for Azure AD integration in employee profiles

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='employeeprofile',
            name='azure_ad_group_memberships',
            field=models.TextField(blank=True, help_text='JSON list of Azure AD group memberships for this employee'),
        ),
        migrations.AddField(
            model_name='employeeprofile',
            name='azure_ad_manager_sync_status',
            field=models.CharField(choices=[('pending', 'Pending'), ('synced', 'Synced'), ('failed', 'Failed'), ('not_applicable', 'Not Applicable')], default='pending', help_text='Status of manager relationship sync with Azure AD', max_length=20),
        ),
        migrations.AddField(
            model_name='employeeprofile',
            name='azure_ad_department_sync_status',
            field=models.CharField(choices=[('pending', 'Pending'), ('synced', 'Synced'), ('failed', 'Failed'), ('not_applicable', 'Not Applicable')], default='pending', help_text='Status of department sync with Azure AD', max_length=20),
        ),
    ]