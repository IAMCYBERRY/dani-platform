# Step 2: Update department field to ForeignKey and add unique constraint to employee_id

from django.db import migrations, models
import django.db.models.deletion


def clear_empty_employee_ids(apps, schema_editor):
    """Set empty employee_id strings to NULL before adding unique constraint"""
    User = apps.get_model('accounts', 'User')
    User.objects.filter(employee_id='').update(employee_id=None)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_add_user_fields_step1'),
        ('employees', '0002_azure_ad_fields'),
    ]

    operations = [
        # Clear empty employee_id values
        migrations.RunPython(clear_empty_employee_ids, migrations.RunPython.noop),
        
        # Change department from CharField to ForeignKey
        migrations.RemoveField(
            model_name='user',
            name='department',
        ),
        migrations.AddField(
            model_name='user',
            name='department',
            field=models.ForeignKey(blank=True, help_text='Department (synced with Azure AD)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='users', to='employees.department'),
        ),
        
        # Now add unique constraint to employee_id (after cleaning empty values)
        migrations.AlterField(
            model_name='user',
            name='employee_id',
            field=models.CharField(blank=True, help_text='Unique employee identifier', max_length=20, null=True, unique=True),
        ),
    ]