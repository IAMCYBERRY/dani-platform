# Generated manually for Azure AD integration

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='azure_ad_object_id',
            field=models.CharField(blank=True, help_text='Azure AD Object ID for Microsoft Graph API integration', max_length=36, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='user',
            name='azure_ad_sync_enabled',
            field=models.BooleanField(default=True, help_text='Enable automatic sync with Azure AD'),
        ),
        migrations.AddField(
            model_name='user',
            name='azure_ad_last_sync',
            field=models.DateTimeField(blank=True, help_text='Last successful sync with Azure AD', null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='azure_ad_sync_status',
            field=models.CharField(choices=[('pending', 'Pending'), ('synced', 'Synced'), ('failed', 'Failed'), ('disabled', 'Disabled')], default='pending', help_text='Current Azure AD sync status', max_length=20),
        ),
        migrations.CreateModel(
            name='AzureADSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('enabled', models.BooleanField(default=False, help_text='Enable Azure AD integration')),
                ('tenant_id', models.CharField(blank=True, help_text='Azure AD Tenant ID (Directory ID)', max_length=100)),
                ('client_id', models.CharField(blank=True, help_text='Azure AD Application (Client) ID', max_length=100)),
                ('client_secret', models.CharField(blank=True, help_text='Azure AD Client Secret', max_length=500)),
                ('sync_enabled', models.BooleanField(default=False, help_text='Enable automatic user synchronization')),
                ('sync_on_user_create', models.BooleanField(default=True, help_text='Automatically sync new users to Azure AD')),
                ('sync_on_user_update', models.BooleanField(default=True, help_text='Automatically sync user updates to Azure AD')),
                ('sync_on_user_disable', models.BooleanField(default=True, help_text='Automatically disable users in Azure AD when deactivated')),
                ('authority', models.URLField(default='https://login.microsoftonline.com/', help_text='Azure AD Authority URL')),
                ('scope', models.CharField(default='https://graph.microsoft.com/.default', help_text='Microsoft Graph API scope', max_length=200)),
                ('default_password_length', models.PositiveIntegerField(default=12, help_text='Default password length for new Azure AD users')),
                ('connection_status', models.CharField(choices=[('unknown', 'Unknown'), ('connected', 'Connected'), ('failed', 'Failed'), ('testing', 'Testing')], default='unknown', help_text='Last connection test result', max_length=20)),
                ('last_test_date', models.DateTimeField(blank=True, help_text='Last time connection was tested', null=True)),
                ('test_error_message', models.TextField(blank=True, help_text='Error message from last failed test')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('updated_by', models.ForeignKey(blank=True, help_text='User who last updated these settings', null=True, on_delete=django.db.models.deletion.SET_NULL, to='accounts.user')),
            ],
            options={
                'verbose_name': 'Azure AD Settings',
                'verbose_name_plural': 'Azure AD Settings',
                'db_table': 'azure_ad_settings',
            },
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['azure_ad_object_id'], name='users_azure_ad_object_id_idx'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['azure_ad_sync_status'], name='users_azure_ad_sync_status_idx'),
        ),
    ]