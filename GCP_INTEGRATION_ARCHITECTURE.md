# GCP Integration Architecture for DANI HRIS Platform

## Table of Contents
- [Overview](#overview)
- [Architecture Design](#architecture-design)
- [GCP Services Integration](#gcp-services-integration)
- [Implementation Plan](#implementation-plan)
- [Security Architecture](#security-architecture)
- [Risk Assessment](#risk-assessment)
- [Data Flow & Synchronization](#data-flow--synchronization)
- [Monitoring & Compliance](#monitoring--compliance)
- [Cost Optimization](#cost-optimization)
- [Disaster Recovery](#disaster-recovery)

---

## Overview

### **Purpose**
Integrate Google Cloud Platform (GCP) services with the DANI HRIS platform to provide comprehensive cloud-based HR management, enhanced collaboration, automated workflows, and enterprise-grade infrastructure capabilities.

### **Scope**
- **Google Workspace Integration**: User provisioning, calendar, email, drive
- **Google Cloud Identity**: SSO and identity management
- **Cloud Storage**: Document management and file storage
- **Cloud Functions**: Serverless automation and webhooks
- **Cloud SQL**: Backup database replication
- **BigQuery**: Analytics and reporting data warehouse
- **Cloud Monitoring**: Infrastructure and application monitoring
- **Cloud Security**: IAM, audit logging, and compliance

### **Business Benefits**
- Seamless Google Workspace user management
- Automated onboarding/offboarding workflows
- Enhanced document collaboration and storage
- Real-time HR analytics and insights
- Scalable cloud infrastructure
- Reduced operational overhead
- Improved compliance and audit capabilities

---

## Architecture Design

### **High-Level Architecture**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   DANI HRIS     │    │   GCP Services  │    │   Google        │
│   Platform      │    │   Layer         │    │   Workspace     │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • User Mgmt     │◄──►│ • Cloud IAM     │◄──►│ • Gmail         │
│ • Employee Data │    │ • Cloud Storage │    │ • Calendar      │
│ • HR Analytics  │    │ • Cloud SQL     │    │ • Drive         │
│ • Document Mgmt │    │ • BigQuery      │    │ • Meet          │
│ • Workflows     │    │ • Functions     │    │ • Groups        │
│ • Audit Logs    │    │ • Monitoring    │    │ • Admin API     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                    ┌─────────────────┐
                    │   External      │
                    │   Integrations  │
                    ├─────────────────┤
                    │ • Pub/Sub       │
                    │ • Cloud Tasks   │
                    │ • Cloud Build   │
                    │ • Secret Mgr    │
                    │ • Cloud KMS     │
                    └─────────────────┘
```

### **Component Architecture**

#### **1. GCP Integration Layer**
```python
# New Django app: gcp_integration/
├── models.py              # GCP service configurations
├── services/
│   ├── workspace_service.py    # Google Workspace API
│   ├── storage_service.py      # Cloud Storage operations
│   ├── identity_service.py     # Cloud Identity management
│   ├── analytics_service.py    # BigQuery integration
│   ├── monitoring_service.py   # Cloud Monitoring
│   └── functions_service.py    # Cloud Functions deployment
├── tasks.py               # Celery tasks for async operations
├── webhooks.py            # GCP webhook handlers
├── admin.py               # Admin interface for GCP configs
└── utils/
    ├── auth.py                 # GCP authentication
    ├── encryption.py           # Data encryption utilities
    └── validators.py           # Input validation
```

#### **2. Data Synchronization Architecture**

```
DANI HRIS ←→ Cloud Functions ←→ Google Workspace
    ↓              ↓                    ↓
Cloud Storage  Pub/Sub Topics    Admin SDK API
    ↓              ↓                    ↓
BigQuery   ←→  Event Router  ←→   Calendar API
    ↓              ↓                    ↓
Analytics  ←→  Cloud Tasks   ←→    Drive API
```

---

## GCP Services Integration

### **1. Google Workspace Integration**

#### **Google Admin SDK Integration**
```python
class GoogleWorkspaceService:
    """Google Workspace Admin SDK integration"""
    
    def __init__(self):
        self.admin_service = self._build_admin_service()
        self.directory_service = self._build_directory_service()
        self.calendar_service = self._build_calendar_service()
        self.drive_service = self._build_drive_service()
    
    def create_user_account(self, user_data):
        """Create Google Workspace user account"""
        user_body = {
            'primaryEmail': user_data['email'],
            'name': {
                'givenName': user_data['first_name'],
                'familyName': user_data['last_name']
            },
            'password': self._generate_temp_password(),
            'orgUnitPath': self._get_org_unit(user_data['department']),
            'suspended': False,
            'changePasswordAtNextLogin': True
        }
        
        return self.directory_service.users().insert(body=user_body).execute()
    
    def provision_user_resources(self, user_email, role):
        """Provision user resources based on role"""
        # Create calendar resources
        # Assign to appropriate groups
        # Set up shared drives access
        # Configure email aliases
        
    def deprovision_user(self, user_email):
        """Safely deprovision user account"""
        # Suspend account
        # Transfer drive ownership
        # Remove from groups
        # Archive calendar events
        # Export user data (if required)
```

#### **Calendar Integration**
```python
class GoogleCalendarService:
    """Google Calendar integration for HR events"""
    
    def create_onboarding_calendar(self, new_employee):
        """Create onboarding calendar for new employee"""
        calendar_body = {
            'summary': f'{new_employee.get_full_name()} - Onboarding',
            'description': 'New employee onboarding schedule',
            'timeZone': 'America/New_York'
        }
        
        calendar = self.service.calendars().insert(body=calendar_body).execute()
        
        # Create onboarding events
        self._create_onboarding_events(calendar['id'], new_employee)
        
        return calendar
    
    def schedule_performance_reviews(self, employees, review_period):
        """Automatically schedule performance reviews"""
        for employee in employees:
            if employee.manager:
                self._create_review_event(employee, employee.manager, review_period)
    
    def sync_time_off_requests(self, time_off_request):
        """Sync approved time off to Google Calendar"""
        event_body = {
            'summary': f'{time_off_request.user.get_full_name()} - Time Off',
            'start': {'date': time_off_request.start_date.isoformat()},
            'end': {'date': time_off_request.end_date.isoformat()},
            'description': f'Time off type: {time_off_request.get_type_display()}'
        }
        
        return self.service.events().insert(
            calendarId='primary',
            body=event_body
        ).execute()
```

### **2. Cloud Storage Integration**

#### **Document Management**
```python
class GoogleCloudStorageService:
    """Cloud Storage for HR documents and files"""
    
    def __init__(self):
        self.client = storage.Client()
        self.bucket_name = settings.GCP_STORAGE_BUCKET
        self.bucket = self.client.bucket(self.bucket_name)
    
    def upload_employee_document(self, employee, file_obj, document_type):
        """Upload employee documents with proper organization"""
        # Organize by employee ID and document type
        blob_name = f"employees/{employee.employee_id}/{document_type}/{file_obj.name}"
        
        blob = self.bucket.blob(blob_name)
        blob.upload_from_file(file_obj)
        
        # Set metadata
        blob.metadata = {
            'employee_id': str(employee.employee_id),
            'document_type': document_type,
            'uploaded_by': employee.email,
            'upload_date': timezone.now().isoformat()
        }
        blob.patch()
        
        # Set appropriate access controls
        self._set_document_permissions(blob, employee, document_type)
        
        return blob.public_url
    
    def create_employee_folder_structure(self, employee):
        """Create organized folder structure for new employee"""
        folders = [
            f"employees/{employee.employee_id}/personal/",
            f"employees/{employee.employee_id}/contracts/",
            f"employees/{employee.employee_id}/performance/",
            f"employees/{employee.employee_id}/benefits/",
            f"employees/{employee.employee_id}/training/"
        ]
        
        for folder in folders:
            # Create empty folder structure
            blob = self.bucket.blob(folder + '.gitkeep')
            blob.upload_from_string('')
    
    def backup_hr_data(self, backup_type='incremental'):
        """Backup HR data to Cloud Storage"""
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"backups/{backup_type}/{timestamp}/"
        
        # Backup database dump
        # Backup media files
        # Backup configuration files
        # Create manifest file
```

### **3. BigQuery Analytics Integration**

#### **HR Data Warehouse**
```python
class BigQueryAnalyticsService:
    """BigQuery integration for HR analytics"""
    
    def __init__(self):
        self.client = bigquery.Client()
        self.dataset_id = settings.GCP_BIGQUERY_DATASET
        self.dataset_ref = self.client.dataset(self.dataset_id)
    
    def sync_employee_data(self):
        """Sync employee data to BigQuery for analytics"""
        table_id = 'employees'
        table_ref = self.dataset_ref.table(table_id)
        
        # Extract employee data
        employees = User.objects.filter(role__in=['employee', 'manager', 'hr_manager'])
        
        rows_to_insert = []
        for employee in employees:
            row = {
                'employee_id': employee.employee_id,
                'email': employee.email,
                'department': employee.department.name if employee.department else None,
                'role': employee.role,
                'hire_date': employee.hire_date.isoformat() if employee.hire_date else None,
                'is_active': employee.is_active,
                'manager_id': employee.manager.employee_id if employee.manager else None,
                'last_updated': timezone.now().isoformat()
            }
            rows_to_insert.append(row)
        
        # Insert data into BigQuery
        errors = self.client.insert_rows_json(table_ref, rows_to_insert)
        if errors:
            logger.error(f"BigQuery insert errors: {errors}")
    
    def generate_hr_insights(self):
        """Generate HR analytics and insights"""
        queries = {
            'department_headcount': """
                SELECT department, COUNT(*) as headcount
                FROM `{}.{}.employees`
                WHERE is_active = true
                GROUP BY department
            """,
            'turnover_rate': """
                SELECT 
                    department,
                    COUNT(*) as total_employees,
                    COUNTIF(termination_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 12 MONTH)) as terminated_last_year,
                    SAFE_DIVIDE(
                        COUNTIF(termination_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 12 MONTH)),
                        COUNT(*)
                    ) * 100 as turnover_rate_percent
                FROM `{}.{}.employees`
                GROUP BY department
            """,
            'performance_metrics': """
                SELECT 
                    e.department,
                    AVG(pr.overall_rating) as avg_performance_rating,
                    COUNT(pr.id) as total_reviews
                FROM `{}.{}.employees` e
                LEFT JOIN `{}.{}.performance_reviews` pr ON e.employee_id = pr.employee_id
                WHERE pr.review_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 12 MONTH)
                GROUP BY e.department
            """
        }
        
        insights = {}
        for query_name, query_sql in queries.items():
            formatted_query = query_sql.format(
                self.client.project, self.dataset_id, self.client.project, self.dataset_id
            )
            
            query_job = self.client.query(formatted_query)
            insights[query_name] = [dict(row) for row in query_job]
        
        return insights
```

### **4. Cloud Functions for Automation**

#### **Serverless HR Workflows**
```python
# Cloud Function: Employee Onboarding
def employee_onboarding_workflow(request):
    """Cloud Function triggered when new employee is created"""
    
    employee_data = request.get_json()
    
    try:
        # Create Google Workspace account
        workspace_service = GoogleWorkspaceService()
        gcp_user = workspace_service.create_user_account(employee_data)
        
        # Create folder structure in Cloud Storage
        storage_service = GoogleCloudStorageService()
        storage_service.create_employee_folder_structure(employee_data)
        
        # Schedule onboarding calendar events
        calendar_service = GoogleCalendarService()
        calendar_service.create_onboarding_calendar(employee_data)
        
        # Send welcome email with credentials
        send_welcome_email(employee_data, gcp_user['password'])
        
        # Update DANI with GCP integration status
        update_employee_gcp_status(employee_data['employee_id'], 'provisioned')
        
        return {'status': 'success', 'gcp_user_id': gcp_user['id']}
        
    except Exception as e:
        logger.error(f"Onboarding workflow failed: {str(e)}")
        return {'status': 'error', 'message': str(e)}, 500

# Cloud Function: Employee Offboarding
def employee_offboarding_workflow(request):
    """Cloud Function triggered when employee is deactivated"""
    
    employee_data = request.get_json()
    
    try:
        workspace_service = GoogleWorkspaceService()
        
        # Suspend Google Workspace account
        workspace_service.suspend_user(employee_data['email'])
        
        # Transfer drive ownership to manager
        if employee_data.get('manager_email'):
            workspace_service.transfer_drive_ownership(
                employee_data['email'], 
                employee_data['manager_email']
            )
        
        # Archive employee data
        storage_service = GoogleCloudStorageService()
        storage_service.archive_employee_data(employee_data['employee_id'])
        
        # Remove from groups and calendars
        workspace_service.remove_from_all_groups(employee_data['email'])
        
        # Update DANI with offboarding status
        update_employee_gcp_status(employee_data['employee_id'], 'deprovisioned')
        
        return {'status': 'success', 'message': 'Offboarding completed'}
        
    except Exception as e:
        logger.error(f"Offboarding workflow failed: {str(e)}")
        return {'status': 'error', 'message': str(e)}, 500
```

### **5. Cloud Identity Integration**

#### **Identity and Access Management**
```python
class GoogleCloudIdentityService:
    """Google Cloud Identity integration"""
    
    def __init__(self):
        self.identity_service = self._build_identity_service()
        self.iam_service = self._build_iam_service()
    
    def sync_organizational_structure(self):
        """Sync DANI org structure to Google Cloud Identity"""
        
        # Create organizational units for departments
        departments = Department.objects.all()
        
        for dept in departments:
            org_unit = {
                'name': f"departments/{dept.name}",
                'displayName': dept.name,
                'description': f"{dept.name} Department"
            }
            
            try:
                self.identity_service.orgunits().insert(
                    customerId='my_customer',
                    body=org_unit
                ).execute()
            except Exception as e:
                if 'already exists' not in str(e):
                    logger.error(f"Failed to create org unit {dept.name}: {e}")
    
    def manage_group_memberships(self, employee, action='add'):
        """Manage Google Groups based on DANI roles and departments"""
        
        groups_to_manage = []
        
        # Department-based groups
        if employee.department:
            groups_to_manage.append(f"{employee.department.name.lower()}@company.com")
        
        # Role-based groups
        role_group_mapping = {
            'hr_manager': 'hr-managers@company.com',
            'hiring_manager': 'hiring-managers@company.com',
            'admin': 'admins@company.com'
        }
        
        if employee.role in role_group_mapping:
            groups_to_manage.append(role_group_mapping[employee.role])
        
        # Manager groups
        if employee.is_manager:
            groups_to_manage.append('managers@company.com')
        
        # Execute group membership changes
        for group_email in groups_to_manage:
            try:
                if action == 'add':
                    self._add_to_group(employee.email, group_email)
                elif action == 'remove':
                    self._remove_from_group(employee.email, group_email)
            except Exception as e:
                logger.error(f"Group membership error for {employee.email}: {e}")
```

---

## Implementation Plan

### **Phase 1: Core GCP Infrastructure (Weeks 1-2)**

#### **Database Models**
```python
class GCPConfiguration(models.Model):
    """GCP integration configuration"""
    service_name = models.CharField(max_length=50, choices=[
        ('workspace', 'Google Workspace'),
        ('storage', 'Cloud Storage'),
        ('bigquery', 'BigQuery'),
        ('functions', 'Cloud Functions'),
        ('monitoring', 'Cloud Monitoring'),
    ])
    enabled = models.BooleanField(default=False)
    
    # Service-specific configurations stored as JSON
    configuration = models.JSONField(default=dict)
    
    # Credentials and authentication
    service_account_key = models.TextField(blank=True)
    project_id = models.CharField(max_length=100)
    
    # Status and monitoring
    last_sync = models.DateTimeField(null=True, blank=True)
    sync_status = models.CharField(max_length=20, default='pending')
    error_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class GCPUserMapping(models.Model):
    """Map DANI users to GCP identities"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='gcp_mapping')
    workspace_user_id = models.CharField(max_length=255, blank=True)
    workspace_email = models.EmailField(blank=True)
    cloud_identity_id = models.CharField(max_length=255, blank=True)
    
    # Provisioning status
    workspace_provisioned = models.BooleanField(default=False)
    storage_provisioned = models.BooleanField(default=False)
    calendar_provisioned = models.BooleanField(default=False)
    
    # Sync tracking
    last_workspace_sync = models.DateTimeField(null=True, blank=True)
    sync_errors = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class GCPAuditLog(models.Model):
    """Audit log for GCP operations"""
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=100)
    service = models.CharField(max_length=50)
    resource_id = models.CharField(max_length=255, blank=True)
    
    # Request and response data
    request_data = models.JSONField(default=dict)
    response_data = models.JSONField(default=dict)
    
    # Status and error tracking
    status = models.CharField(max_length=20, choices=[
        ('success', 'Success'),
        ('error', 'Error'),
        ('pending', 'Pending'),
    ])
    error_message = models.TextField(blank=True)
    
    # Security and compliance
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.TextField(blank=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)
```

### **Phase 2: Google Workspace Integration (Weeks 3-4)**

#### **User Provisioning Service**
```python
class WorkspaceProvisioningService:
    """Handle Google Workspace user lifecycle"""
    
    def __init__(self):
        self.workspace_service = GoogleWorkspaceService()
        self.storage_service = GoogleCloudStorageService()
        self.calendar_service = GoogleCalendarService()
    
    def provision_new_employee(self, employee):
        """Complete provisioning workflow for new employee"""
        
        provisioning_steps = [
            ('create_workspace_account', self._create_workspace_account),
            ('setup_storage_access', self._setup_storage_access),
            ('create_calendar_resources', self._create_calendar_resources),
            ('assign_to_groups', self._assign_to_groups),
            ('setup_email_aliases', self._setup_email_aliases),
            ('configure_security_settings', self._configure_security_settings),
        ]
        
        results = {}
        
        for step_name, step_function in provisioning_steps:
            try:
                result = step_function(employee)
                results[step_name] = {'status': 'success', 'data': result}
                
                # Log successful step
                self._log_provisioning_step(employee, step_name, 'success', result)
                
            except Exception as e:
                results[step_name] = {'status': 'error', 'error': str(e)}
                
                # Log failed step
                self._log_provisioning_step(employee, step_name, 'error', str(e))
                
                # Continue with other steps even if one fails
                continue
        
        # Update employee GCP mapping
        self._update_gcp_mapping(employee, results)
        
        return results
    
    def deprovision_employee(self, employee):
        """Complete deprovisioning workflow for departing employee"""
        
        deprovisioning_steps = [
            ('suspend_workspace_account', self._suspend_workspace_account),
            ('transfer_drive_ownership', self._transfer_drive_ownership),
            ('archive_calendar_events', self._archive_calendar_events),
            ('remove_from_groups', self._remove_from_groups),
            ('backup_user_data', self._backup_user_data),
            ('revoke_access_tokens', self._revoke_access_tokens),
        ]
        
        results = {}
        
        for step_name, step_function in deprovisioning_steps:
            try:
                result = step_function(employee)
                results[step_name] = {'status': 'success', 'data': result}
            except Exception as e:
                results[step_name] = {'status': 'error', 'error': str(e)}
        
        return results
```

### **Phase 3: Cloud Storage & Document Management (Week 5)**

#### **Document Management Integration**
```python
class HRDocumentManager:
    """Manage HR documents in Cloud Storage"""
    
    def __init__(self):
        self.storage_service = GoogleCloudStorageService()
        self.encryption_service = DocumentEncryptionService()
    
    def upload_sensitive_document(self, employee, document, document_type):
        """Upload and encrypt sensitive HR documents"""
        
        # Encrypt document before upload
        encrypted_content = self.encryption_service.encrypt_document(
            document.read(),
            employee.employee_id
        )
        
        # Generate secure filename
        filename = f"{document_type}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.enc"
        blob_path = f"employees/{employee.employee_id}/confidential/{filename}"
        
        # Upload to Cloud Storage
        blob = self.storage_service.upload_encrypted_document(
            blob_path,
            encrypted_content,
            {
                'employee_id': str(employee.employee_id),
                'document_type': document_type,
                'encryption_key_id': self.encryption_service.get_key_id(),
                'content_type': document.content_type,
                'original_filename': document.name
            }
        )
        
        # Create document record in DANI
        document_record = EmployeeDocument.objects.create(
            employee=employee,
            document_type=document_type,
            gcp_blob_path=blob_path,
            encrypted=True,
            uploaded_by=employee,
            file_size=len(encrypted_content)
        )
        
        return document_record
    
    def setup_shared_drives(self, department):
        """Create and configure shared drives for departments"""
        
        drive_config = {
            'name': f"{department.name} - HR Documents",
            'colorRgb': '#1f4e79',  # Professional blue
            'backgroundImageFile': {
                'id': 'department_template_background'
            },
            'capabilities': {
                'canAddChildren': True,
                'canComment': True,
                'canCopy': False,
                'canDeleteChildren': True,
                'canDownload': True,
                'canEdit': True,
                'canListChildren': True,
                'canManageMembers': False,  # Only HR can manage
                'canReadRevisions': True,
                'canRename': False,
                'canShare': False,
                'canTrash': True
            }
        }
        
        # Create shared drive
        shared_drive = self.drive_service.drives().create(
            requestId=f"dept_{department.id}_{timezone.now().timestamp()}",
            body=drive_config
        ).execute()
        
        # Set up folder structure
        folder_structure = [
            'Policies & Procedures',
            'Templates',
            'Training Materials',
            'Department Meetings',
            'Project Documents'
        ]
        
        for folder_name in folder_structure:
            self._create_drive_folder(shared_drive['id'], folder_name)
        
        return shared_drive
```

### **Phase 4: Analytics & Reporting (Week 6)**

#### **BigQuery Data Pipeline**
```python
class HRAnalyticsPipeline:
    """ETL pipeline for HR analytics in BigQuery"""
    
    def __init__(self):
        self.bigquery_service = BigQueryAnalyticsService()
        self.storage_service = GoogleCloudStorageService()
    
    def create_data_warehouse_schema(self):
        """Create BigQuery dataset and tables for HR analytics"""
        
        # Create dataset
        dataset = bigquery.Dataset(self.bigquery_service.dataset_ref)
        dataset.location = "US"
        dataset.description = "DANI HRIS Analytics Data Warehouse"
        
        self.bigquery_service.client.create_dataset(dataset, exists_ok=True)
        
        # Define table schemas
        table_schemas = {
            'employees': [
                bigquery.SchemaField("employee_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("email", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("first_name", "STRING"),
                bigquery.SchemaField("last_name", "STRING"),
                bigquery.SchemaField("department", "STRING"),
                bigquery.SchemaField("role", "STRING"),
                bigquery.SchemaField("manager_id", "STRING"),
                bigquery.SchemaField("hire_date", "DATE"),
                bigquery.SchemaField("termination_date", "DATE"),
                bigquery.SchemaField("is_active", "BOOLEAN"),
                bigquery.SchemaField("salary", "NUMERIC"),
                bigquery.SchemaField("location", "STRING"),
                bigquery.SchemaField("last_updated", "TIMESTAMP"),
            ],
            'performance_reviews': [
                bigquery.SchemaField("review_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("employee_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("reviewer_id", "STRING"),
                bigquery.SchemaField("review_period", "STRING"),
                bigquery.SchemaField("overall_rating", "NUMERIC"),
                bigquery.SchemaField("goals_rating", "NUMERIC"),
                bigquery.SchemaField("skills_rating", "NUMERIC"),
                bigquery.SchemaField("review_date", "DATE"),
                bigquery.SchemaField("next_review_date", "DATE"),
                bigquery.SchemaField("comments", "STRING"),
            ],
            'time_off': [
                bigquery.SchemaField("request_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("employee_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("request_type", "STRING"),
                bigquery.SchemaField("start_date", "DATE"),
                bigquery.SchemaField("end_date", "DATE"),
                bigquery.SchemaField("days_requested", "NUMERIC"),
                bigquery.SchemaField("status", "STRING"),
                bigquery.SchemaField("approved_by", "STRING"),
                bigquery.SchemaField("request_date", "TIMESTAMP"),
                bigquery.SchemaField("approval_date", "TIMESTAMP"),
            ]
        }
        
        # Create tables
        for table_name, schema in table_schemas.items():
            table_ref = self.bigquery_service.dataset_ref.table(table_name)
            table = bigquery.Table(table_ref, schema=schema)
            
            # Configure table for time-based partitioning
            if table_name in ['performance_reviews', 'time_off']:
                table.time_partitioning = bigquery.TimePartitioning(
                    type_=bigquery.TimePartitioningType.DAY,
                    field="request_date" if table_name == "time_off" else "review_date"
                )
            
            self.bigquery_service.client.create_table(table, exists_ok=True)
    
    def run_daily_etl(self):
        """Daily ETL process to update BigQuery with latest data"""
        
        # Extract data from DANI database
        employees_data = self._extract_employees_data()
        performance_data = self._extract_performance_data()
        timeoff_data = self._extract_timeoff_data()
        
        # Transform data for BigQuery
        transformed_data = {
            'employees': self._transform_employees_data(employees_data),
            'performance_reviews': self._transform_performance_data(performance_data),
            'time_off': self._transform_timeoff_data(timeoff_data)
        }
        
        # Load data into BigQuery
        for table_name, data in transformed_data.items():
            if data:  # Only load if there's data
                self._load_data_to_bigquery(table_name, data)
        
        # Update last sync timestamp
        self._update_sync_status('daily_etl', 'completed')
```

### **Phase 5: Monitoring & Security (Week 7)**

#### **Cloud Monitoring Integration**
```python
class GCPMonitoringService:
    """Google Cloud Monitoring integration"""
    
    def __init__(self):
        self.monitoring_client = monitoring_v3.MetricServiceClient()
        self.project_name = f"projects/{settings.GCP_PROJECT_ID}"
    
    def create_custom_metrics(self):
        """Create custom metrics for DANI HRIS monitoring"""
        
        custom_metrics = [
            {
                'type': 'custom.googleapis.com/dani/user_login_count',
                'display_name': 'DANI User Logins',
                'description': 'Number of user logins to DANI HRIS',
                'metric_kind': monitoring_v3.MetricDescriptor.MetricKind.GAUGE,
                'value_type': monitoring_v3.MetricDescriptor.ValueType.INT64,
            },
            {
                'type': 'custom.googleapis.com/dani/gcp_sync_errors',
                'display_name': 'GCP Sync Errors',
                'description': 'Number of GCP synchronization errors',
                'metric_kind': monitoring_v3.MetricDescriptor.MetricKind.CUMULATIVE,
                'value_type': monitoring_v3.MetricDescriptor.ValueType.INT64,
            },
            {
                'type': 'custom.googleapis.com/dani/employee_provisioning_time',
                'display_name': 'Employee Provisioning Time',
                'description': 'Time taken to provision new employees in GCP',
                'metric_kind': monitoring_v3.MetricDescriptor.MetricKind.GAUGE,
                'value_type': monitoring_v3.MetricDescriptor.ValueType.DOUBLE,
            }
        ]
        
        for metric_config in custom_metrics:
            descriptor = monitoring_v3.MetricDescriptor(
                type=metric_config['type'],
                display_name=metric_config['display_name'],
                description=metric_config['description'],
                metric_kind=metric_config['metric_kind'],
                value_type=metric_config['value_type']
            )
            
            self.monitoring_client.create_metric_descriptor(
                name=self.project_name,
                metric_descriptor=descriptor
            )
    
    def setup_alerting_policies(self):
        """Create alerting policies for critical DANI operations"""
        
        alerting_client = monitoring_v3.AlertPolicyServiceClient()
        
        # Alert on high number of GCP sync errors
        sync_error_policy = monitoring_v3.AlertPolicy(
            display_name="DANI GCP Sync Errors",
            conditions=[
                monitoring_v3.AlertPolicy.Condition(
                    display_name="GCP sync errors > 10",
                    condition_threshold=monitoring_v3.AlertPolicy.Condition.MetricThreshold(
                        filter='metric.type="custom.googleapis.com/dani/gcp_sync_errors"',
                        comparison=monitoring_v3.ComparisonType.COMPARISON_GREATER_THAN,
                        threshold_value=10.0,
                        duration={"seconds": 300}  # 5 minutes
                    )
                )
            ],
            notification_channels=[],  # Configure notification channels
            alert_strategy=monitoring_v3.AlertPolicy.AlertStrategy(
                auto_close={"seconds": 86400}  # Auto-close after 24 hours
            )
        )
        
        alerting_client.create_alert_policy(
            name=self.project_name,
            alert_policy=sync_error_policy
        )
```

---

## Security Architecture

### **Authentication & Authorization**

#### **Service Account Management**
```python
class GCPSecurityManager:
    """Manage GCP security and access controls"""
    
    def __init__(self):
        self.iam_client = iam_v1.IAMClient()
        self.project_id = settings.GCP_PROJECT_ID
    
    def create_service_accounts(self):
        """Create dedicated service accounts for different functions"""
        
        service_accounts = [
            {
                'account_id': 'dani-workspace-sync',
                'display_name': 'DANI Workspace Synchronization',
                'description': 'Service account for Google Workspace user management',
                'roles': [
                    'roles/admin.directory.user',
                    'roles/admin.directory.group',
                    'roles/admin.directory.orgunit'
                ]
            },
            {
                'account_id': 'dani-storage-manager',
                'display_name': 'DANI Storage Manager',
                'description': 'Service account for Cloud Storage operations',
                'roles': [
                    'roles/storage.admin',
                    'roles/storage.objectAdmin'
                ]
            },
            {
                'account_id': 'dani-bigquery-analyst',
                'display_name': 'DANI BigQuery Analyst',
                'description': 'Service account for BigQuery analytics',
                'roles': [
                    'roles/bigquery.dataEditor',
                    'roles/bigquery.jobUser'
                ]
            }
        ]
        
        for sa_config in service_accounts:
            # Create service account
            service_account = self._create_service_account(sa_config)
            
            # Assign roles
            for role in sa_config['roles']:
                self._assign_role_to_service_account(service_account, role)
            
            # Generate and store key securely
            key = self._generate_service_account_key(service_account)
            self._store_key_securely(sa_config['account_id'], key)
    
    def implement_data_classification(self):
        """Implement data classification and access controls"""
        
        # Define data classification levels
        classification_levels = {
            'public': {
                'description': 'Public information, no access restrictions',
                'bucket_policy': 'allUsers:objectViewer'
            },
            'internal': {
                'description': 'Internal company information',
                'bucket_policy': 'domain:company.com:objectViewer'
            },
            'confidential': {
                'description': 'Confidential HR information',
                'bucket_policy': 'group:hr-team@company.com:objectViewer'
            },
            'restricted': {
                'description': 'Highly sensitive data, specific access only',
                'bucket_policy': 'serviceAccount:dani-hr-admin@project.iam.gserviceaccount.com:objectAdmin'
            }
        }
        
        # Apply classification to storage buckets
        for level, config in classification_levels.items():
            bucket_name = f"dani-hr-{level}-{settings.GCP_PROJECT_ID}"
            self._create_classified_bucket(bucket_name, config)
    
    def setup_audit_logging(self):
        """Configure comprehensive audit logging"""
        
        audit_config = {
            'auditConfigs': [
                {
                    'service': 'storage.googleapis.com',
                    'auditLogConfigs': [
                        {'logType': 'DATA_READ'},
                        {'logType': 'DATA_WRITE'},
                        {'logType': 'ADMIN_READ'}
                    ]
                },
                {
                    'service': 'admin.googleapis.com',
                    'auditLogConfigs': [
                        {'logType': 'DATA_READ'},
                        {'logType': 'DATA_WRITE'},
                        {'logType': 'ADMIN_READ'}
                    ]
                },
                {
                    'service': 'bigquery.googleapis.com',
                    'auditLogConfigs': [
                        {'logType': 'DATA_READ'},
                        {'logType': 'DATA_WRITE'},
                        {'logType': 'ADMIN_READ'}
                    ]
                }
            ]
        }
        
        # Apply audit configuration
        self._apply_audit_configuration(audit_config)
```

### **Data Encryption**

#### **End-to-End Encryption**
```python
class DataEncryptionService:
    """Handle encryption for sensitive HR data"""
    
    def __init__(self):
        self.kms_client = kms.KeyManagementServiceClient()
        self.key_ring_name = self._get_key_ring_name()
        self.crypto_key_name = self._get_crypto_key_name()
    
    def encrypt_sensitive_data(self, data, employee_id):
        """Encrypt sensitive employee data"""
        
        # Add metadata to plaintext
        metadata = {
            'employee_id': employee_id,
            'timestamp': timezone.now().isoformat(),
            'data_type': 'employee_data'
        }
        
        plaintext_with_metadata = json.dumps({
            'metadata': metadata,
            'data': data
        }).encode('utf-8')
        
        # Encrypt using Cloud KMS
        encrypt_response = self.kms_client.encrypt(
            request={
                'name': self.crypto_key_name,
                'plaintext': plaintext_with_metadata
            }
        )
        
        return encrypt_response.ciphertext
    
    def decrypt_sensitive_data(self, ciphertext):
        """Decrypt sensitive employee data"""
        
        # Decrypt using Cloud KMS
        decrypt_response = self.kms_client.decrypt(
            request={
                'name': self.crypto_key_name,
                'ciphertext': ciphertext
            }
        )
        
        # Parse decrypted data
        decrypted_json = json.loads(decrypt_response.plaintext.decode('utf-8'))
        
        return decrypted_json['data'], decrypted_json['metadata']
    
    def rotate_encryption_keys(self):
        """Rotate encryption keys for enhanced security"""
        
        # Create new key version
        new_key_version = self.kms_client.create_crypto_key_version(
            request={'parent': self.crypto_key_name}
        )
        
        # Schedule re-encryption of existing data
        self._schedule_data_re_encryption(new_key_version.name)
        
        return new_key_version
```

---

## Risk Assessment

### **High-Risk Areas**

#### **1. Data Exfiltration (Risk: HIGH)**
- **Description**: Unauthorized access to sensitive HR data in GCP
- **Mitigation**:
  - Implement data classification and access controls
  - Use Customer-Managed Encryption Keys (CMEK)
  - Enable Cloud DLP for sensitive data detection
  - Regular access reviews and automated privilege escalation detection
  - VPC Service Controls to prevent data exfiltration

#### **2. Service Account Compromise (Risk: HIGH)**
- **Description**: Service account credentials stolen or misused
- **Mitigation**:
  - Principle of least privilege for all service accounts
  - Regular service account key rotation (90 days)
  - Use workload identity where possible
  - Monitor service account usage patterns
  - Implement service account impersonation instead of key-based auth

#### **3. Workspace Admin Takeover (Risk: HIGH)**
- **Description**: Google Workspace admin account compromised
- **Mitigation**:
  - Enforce 2FA/MFA for all admin accounts
  - Use admin role delegation instead of super admin
  - Implement admin activity monitoring
  - Regular admin access reviews
  - Emergency admin account procedures

### **Medium-Risk Areas**

#### **1. Data Synchronization Failures (Risk: MEDIUM)**
- **Description**: Data inconsistency between DANI and GCP services
- **Mitigation**:
  - Implement robust retry mechanisms
  - Data validation checkpoints
  - Comprehensive monitoring and alerting
  - Regular data consistency audits
  - Automated rollback procedures

#### **2. API Rate Limiting (Risk: MEDIUM)**
- **Description**: GCP API rate limits affecting operations
- **Mitigation**:
  - Implement exponential backoff
  - Request rate monitoring and management
  - API quota monitoring and alerting
  - Distribute operations across multiple service accounts
  - Cache frequently accessed data

#### **3. Compliance Violations (Risk: MEDIUM)**
- **Description**: Non-compliance with data protection regulations
- **Mitigation**:
  - Implement comprehensive audit logging
  - Data residency controls
  - Automated compliance scanning
  - Regular compliance assessments
  - Data retention and deletion policies

### **Low-Risk Areas**

#### **1. Service Availability (Risk: LOW)**
- **Description**: GCP service outages affecting DANI operations
- **Mitigation**:
  - Multi-region deployments where possible
  - Graceful degradation for non-critical features
  - Clear communication during outages
  - SLA monitoring and alerting

---

## Data Flow & Synchronization

### **Real-time Synchronization**

#### **Event-Driven Architecture**
```python
class GCPEventHandler:
    """Handle real-time events for GCP synchronization"""
    
    def __init__(self):
        self.pub_sub_client = pubsub_v1.PublisherClient()
        self.topic_path = self.pub_sub_client.topic_path(
            settings.GCP_PROJECT_ID, 
            'dani-hr-events'
        )
    
    def handle_employee_created(self, employee):
        """Handle new employee creation event"""
        
        event_data = {
            'event_type': 'employee_created',
            'employee_id': employee.employee_id,
            'employee_data': {
                'email': employee.email,
                'first_name': employee.first_name,
                'last_name': employee.last_name,
                'department': employee.department.name if employee.department else None,
                'role': employee.role,
                'manager_email': employee.manager.email if employee.manager else None,
                'hire_date': employee.hire_date.isoformat() if employee.hire_date else None
            },
            'timestamp': timezone.now().isoformat()
        }
        
        # Publish to Pub/Sub topic
        self._publish_event(event_data)
        
        # Trigger Cloud Function for provisioning
        self._trigger_provisioning_workflow(employee)
    
    def handle_employee_updated(self, employee, changed_fields):
        """Handle employee update event"""
        
        event_data = {
            'event_type': 'employee_updated',
            'employee_id': employee.employee_id,
            'changed_fields': changed_fields,
            'updated_data': self._extract_changed_data(employee, changed_fields),
            'timestamp': timezone.now().isoformat()
        }
        
        self._publish_event(event_data)
        
        # Trigger selective sync based on changed fields
        if 'department' in changed_fields:
            self._update_workspace_org_unit(employee)
        
        if 'role' in changed_fields:
            self._update_group_memberships(employee)
        
        if 'is_active' in changed_fields and not employee.is_active:
            self._trigger_deprovisioning_workflow(employee)
    
    def _publish_event(self, event_data):
        """Publish event to Pub/Sub topic"""
        
        message_data = json.dumps(event_data).encode('utf-8')
        
        future = self.pub_sub_client.publish(
            self.topic_path, 
            message_data,
            source='dani-hris',
            event_type=event_data['event_type']
        )
        
        # Wait for publish confirmation
        message_id = future.result()
        logger.info(f"Published event {event_data['event_type']} with message ID: {message_id}")
```

### **Batch Synchronization**

#### **Scheduled Sync Operations**
```python
@shared_task(bind=True, max_retries=3)
def gcp_daily_sync(self):
    """Daily synchronization task for GCP services"""
    
    try:
        # Sync employee data to BigQuery
        analytics_service = BigQueryAnalyticsService()
        analytics_service.sync_employee_data()
        
        # Sync organizational structure
        identity_service = GoogleCloudIdentityService()
        identity_service.sync_organizational_structure()
        
        # Update Workspace groups based on current roles
        workspace_service = GoogleWorkspaceService()
        workspace_service.sync_all_group_memberships()
        
        # Backup HR data to Cloud Storage
        storage_service = GoogleCloudStorageService()
        storage_service.backup_hr_data('daily')
        
        # Update monitoring metrics
        monitoring_service = GCPMonitoringService()
        monitoring_service.update_daily_metrics()
        
        logger.info("GCP daily sync completed successfully")
        
    except Exception as e:
        logger.error(f"GCP daily sync failed: {str(e)}")
        
        # Retry with exponential backoff
        countdown = 2 ** self.request.retries * 60  # 1, 2, 4 minutes
        raise self.retry(countdown=countdown, exc=e)

@shared_task
def gcp_weekly_maintenance():
    """Weekly maintenance tasks for GCP integration"""
    
    # Rotate service account keys
    security_manager = GCPSecurityManager()
    security_manager.rotate_service_account_keys()
    
    # Clean up old audit logs
    audit_service = GCPAuditService()
    audit_service.cleanup_old_logs(days=90)
    
    # Generate compliance reports
    compliance_service = GCPComplianceService()
    compliance_service.generate_weekly_report()
    
    # Update data classification
    security_manager.review_data_classification()
```

---

## Cost Optimization

### **Resource Management**

#### **Cost Monitoring & Optimization**
```python
class GCPCostOptimizer:
    """Monitor and optimize GCP costs for DANI integration"""
    
    def __init__(self):
        self.billing_client = cloudbilling_v1.CloudBillingClient()
        self.monitoring_client = monitoring_v3.MetricServiceClient()
    
    def analyze_storage_costs(self):
        """Analyze and optimize Cloud Storage costs"""
        
        storage_analysis = {
            'total_storage_gb': 0,
            'storage_by_class': {},
            'recommendations': []
        }
        
        # Analyze storage usage patterns
        buckets = self.storage_client.list_buckets()
        
        for bucket in buckets:
            if bucket.name.startswith('dani-hr-'):
                # Get bucket size and access patterns
                bucket_info = self._analyze_bucket_usage(bucket)
                storage_analysis['storage_by_class'][bucket_info['storage_class']] = bucket_info
                
                # Generate optimization recommendations
                if bucket_info['last_access_days'] > 30:
                    storage_analysis['recommendations'].append({
                        'bucket': bucket.name,
                        'recommendation': 'Move to Nearline storage',
                        'potential_savings': bucket_info['size_gb'] * 0.01  # Approximate savings
                    })
                
                elif bucket_info['last_access_days'] > 90:
                    storage_analysis['recommendations'].append({
                        'bucket': bucket.name,
                        'recommendation': 'Move to Coldline storage',
                        'potential_savings': bucket_info['size_gb'] * 0.02
                    })
        
        return storage_analysis
    
    def optimize_bigquery_costs(self):
        """Optimize BigQuery costs through partitioning and clustering"""
        
        # Implement table partitioning for large datasets
        tables_to_optimize = [
            'employees',
            'performance_reviews',
            'time_off_requests',
            'audit_logs'
        ]
        
        for table_name in tables_to_optimize:
            table_ref = self.bigquery_client.dataset(self.dataset_id).table(table_name)
            table = self.bigquery_client.get_table(table_ref)
            
            # Check if partitioning would be beneficial
            if table.num_rows > 1000000:  # 1M rows
                self._implement_table_partitioning(table, table_name)
            
            # Implement clustering for frequently queried columns
            if table_name == 'employees':
                self._implement_table_clustering(table, ['department', 'role'])
            elif table_name == 'performance_reviews':
                self._implement_table_clustering(table, ['employee_id', 'review_date'])
    
    def setup_budget_alerts(self):
        """Set up budget alerts for GCP spending"""
        
        budget_config = {
            'display_name': 'DANI HRIS GCP Budget',
            'budget_filter': {
                'projects': [f'projects/{settings.GCP_PROJECT_ID}'],
                'services': [
                    'services/95FF2355-BD96-4FF0-8FA4-3F1F6E3C7E8D',  # Cloud Storage
                    'services/24E6F5DD-569D-4FCE-B883-077E308A4B72',  # BigQuery
                    'services/34CA2B42-8107-4F04-B3C4-E5C0E0E5E8A3',  # Cloud Functions
                ]
            },
            'amount': {
                'specified_amount': {
                    'currency_code': 'USD',
                    'units': 1000  # $1000/month budget
                }
            },
            'threshold_rules': [
                {
                    'threshold_percent': 0.5,  # 50%
                    'spend_basis': 'CURRENT_SPEND'
                },
                {
                    'threshold_percent': 0.8,  # 80%
                    'spend_basis': 'CURRENT_SPEND'
                },
                {
                    'threshold_percent': 1.0,  # 100%
                    'spend_basis': 'CURRENT_SPEND'
                }
            ]
        }
        
        # Create budget with alerts
        self._create_budget_with_alerts(budget_config)
```

---

## Implementation Timeline

### **Phase 1: Infrastructure (Weeks 1-2)**
- GCP project setup and service account creation
- Database models and basic admin interface
- Authentication and security framework
- Basic monitoring and logging setup

### **Phase 2: Workspace Integration (Weeks 3-4)**
- Google Workspace Admin SDK integration
- User provisioning and deprovisioning workflows
- Calendar and email integration
- Group management and organizational units

### **Phase 3: Storage & Documents (Week 5)**
- Cloud Storage integration for HR documents
- Document encryption and access controls
- Shared drives setup for departments
- File lifecycle management

### **Phase 4: Analytics (Week 6)**
- BigQuery data warehouse setup
- ETL pipelines for HR analytics
- Custom dashboards and reports
- Performance metrics and insights

### **Phase 5: Automation (Week 7)**
- Cloud Functions for automated workflows
- Pub/Sub event handling
- Celery task integration
- Webhook endpoints for real-time sync

### **Phase 6: Security & Compliance (Week 8)**
- Security scanning and hardening
- Compliance validation
- Audit logging verification
- Performance optimization
- Documentation completion

---

## Success Criteria

### **Functional Requirements**
- ✅ Complete Google Workspace user lifecycle management
- ✅ Real-time bi-directional data synchronization
- ✅ Secure document storage with encryption
- ✅ Comprehensive HR analytics in BigQuery
- ✅ Automated onboarding/offboarding workflows

### **Security Requirements**
- ✅ End-to-end encryption for sensitive data
- ✅ Role-based access controls
- ✅ Comprehensive audit logging
- ✅ Regular security key rotation
- ✅ Compliance with data protection regulations

### **Performance Requirements**
- ✅ User provisioning completed within 5 minutes
- ✅ Real-time sync latency < 30 seconds
- ✅ Analytics queries respond within 10 seconds
- ✅ 99.9% uptime for critical integrations
- ✅ Support for 10,000+ employees

### **Cost Requirements**
- ✅ Monthly GCP costs under $1000 for 1000 employees
- ✅ Automated cost optimization and monitoring
- ✅ Transparent cost allocation by department
- ✅ Scalable pricing model

---

**Document Version**: 1.0  
**Last Updated**: July 2025  
**Review Schedule**: Monthly cost review, quarterly security review