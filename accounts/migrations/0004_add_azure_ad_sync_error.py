# Generated manually for Azure AD sync error field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_rename_users_azure_ad_object_id_idx_users_azure_a_45f756_idx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='azure_ad_sync_error',
            field=models.TextField(blank=True, help_text='Last sync error message for troubleshooting'),
        ),
    ]