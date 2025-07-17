"""
Microsoft Graph API service for Azure AD user management.

This service handles bidirectional synchronization between the HRIS platform
and Azure AD using the Microsoft Graph API.
"""

import logging
import secrets
import string
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone

from django.conf import settings
from django.utils import timezone as django_timezone
from msal import ConfidentialClientApplication
import requests

from .models import User

logger = logging.getLogger(__name__)


class AzureADService:
    """
    Service class for Microsoft Graph API integration with Azure AD.
    """
    
    def __init__(self):
        self.app = None
        self.graph_base_url = settings.GRAPH_API_BASE_URL
    
    def _get_settings(self):
        """Get current Azure AD settings from database."""
        # Import here to avoid circular imports
        from .models import AzureADSettings
        return AzureADSettings.get_settings()
    
    def _initialize_app(self, azure_settings):
        """Initialize MSAL app with current settings."""
        if not azure_settings.is_configured:
            return None
            
        try:
            return ConfidentialClientApplication(
                client_id=azure_settings.client_id,
                client_credential=azure_settings.client_secret,
                authority=azure_settings.authority_url
            )
        except Exception as e:
            logger.error(f"Failed to initialize Azure AD service: {str(e)}")
            return None
    
    def _is_configured(self) -> bool:
        """Check if Azure AD is properly configured."""
        azure_settings = self._get_settings()
        return azure_settings.is_configured
    
    def _get_access_token(self) -> Optional[str]:
        """
        Get access token for Microsoft Graph API.
        """
        azure_settings = self._get_settings()
        app = self._initialize_app(azure_settings)
        
        if not app:
            logger.error("Azure AD service not configured")
            return None
            
        try:
            scope = [azure_settings.scope]
            result = app.acquire_token_silent(scope, account=None)
            if not result:
                result = app.acquire_token_for_client(scopes=scope)
            
            if "access_token" in result:
                return result["access_token"]
            else:
                logger.error(f"Failed to acquire token: {result.get('error_description')}")
                return None
        except Exception as e:
            logger.error(f"Error acquiring access token: {str(e)}")
            return None
    
    def _make_graph_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Tuple[bool, Dict]:
        """
        Make a request to Microsoft Graph API.
        """
        token = self._get_access_token()
        if not token:
            return False, {"error": "Unable to acquire access token"}
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.graph_base_url}/{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data)
            elif method.upper() == "PATCH":
                response = requests.patch(url, headers=headers, json=data)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers)
            else:
                return False, {"error": f"Unsupported HTTP method: {method}"}
            
            if response.status_code in [200, 201, 204]:
                return True, response.json() if response.content else {}
            else:
                logger.error(f"Graph API request failed: {response.status_code} - {response.text}")
                return False, {"error": f"HTTP {response.status_code}", "details": response.text}
                
        except Exception as e:
            logger.error(f"Error making Graph API request: {str(e)}")
            return False, {"error": str(e)}
    
    def _generate_secure_password(self, length: int = None) -> str:
        """
        Generate a secure password for Azure AD user.
        """
        if not length:
            length = settings.AZURE_AD_DEFAULT_PASSWORD_LENGTH
        
        # Ensure password meets Azure AD complexity requirements
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        
        # Ensure at least one character from each category
        if not any(c.islower() for c in password):
            password = password[:-1] + secrets.choice(string.ascii_lowercase)
        if not any(c.isupper() for c in password):
            password = password[:-1] + secrets.choice(string.ascii_uppercase)
        if not any(c.isdigit() for c in password):
            password = password[:-1] + secrets.choice(string.digits)
        
        return password
    
    def create_user(self, user: User) -> Tuple[bool, Dict]:
        """
        Create a user in Azure AD.
        """
        azure_settings = self._get_settings()
        
        if not azure_settings.is_configured:
            return False, {"error": "Azure AD is not configured"}
            
        if not azure_settings.enabled or not azure_settings.sync_enabled:
            return False, {"error": "Azure AD sync is disabled"}
        
        if user.azure_ad_object_id:
            return False, {"error": "User already exists in Azure AD"}
        
        # Generate temporary password
        temp_password = self._generate_secure_password(azure_settings.default_password_length)
        
        # Prepare user data for Azure AD with proper validation
        azure_user_data = {
            "accountEnabled": user.is_active,
            "displayName": user.get_full_name(),
            "mailNickname": user.email.split('@')[0],
            "userPrincipalName": user.email,  # Use email field for UPN
            "mail": user.business_email if user.business_email else user.email,  # Use business_email for Azure AD email, fallback to email
            "givenName": user.first_name,
            "surname": user.last_name,
            "passwordProfile": {
                "forceChangePasswordNextSignIn": True,
                "password": temp_password
            }
        }
        
        # Add job title if present and valid (1-128 characters)
        if user.job_title and len(user.job_title.strip()) > 0:
            job_title = user.job_title.strip()
            if len(job_title) <= 128:
                azure_user_data["jobTitle"] = job_title
            else:
                azure_user_data["jobTitle"] = job_title[:128]  # Truncate to 128 chars
        
        # Add department if present and valid
        if user.department:
            department_name = user.department.name.strip() if user.department.name else ""
            if len(department_name) > 0:
                if len(department_name) <= 64:  # Department field limit in Azure AD
                    azure_user_data["department"] = department_name
                else:
                    azure_user_data["department"] = department_name[:64]  # Truncate to 64 chars
        
        # Add phone number if available
        if user.phone_number:
            azure_user_data["businessPhones"] = [user.phone_number]
        
        # Add company name if available
        if user.company_name:
            azure_user_data["companyName"] = user.company_name.strip()[:64]  # Azure AD limit
        
        # Add employee ID if available
        if user.employee_id:
            azure_user_data["employeeId"] = user.employee_id.strip()[:16]  # Azure AD limit
        
        # Add employee type if available
        if user.employee_type:
            azure_user_data["employeeType"] = user.get_employee_type_display()
        
        # Add hire date if available
        if user.hire_date:
            azure_user_data["employeeHireDate"] = user.hire_date.isoformat()
        
        # Add office location if available
        if user.office_location:
            azure_user_data["officeLocation"] = user.office_location.strip()[:128]  # Azure AD limit
        
        # Add manager if available
        if user.manager and user.manager.azure_ad_object_id:
            # Use proper Microsoft Graph API format for manager reference
            azure_user_data["manager@odata.bind"] = f"https://graph.microsoft.com/v1.0/users/{user.manager.azure_ad_object_id}"
            logger.info(f"Setting manager for {user.email}: {user.manager.email} (Azure ID: {user.manager.azure_ad_object_id})")
        elif user.manager and not user.manager.azure_ad_object_id:
            logger.warning(f"Manager {user.manager.email} for user {user.email} is not synced to Azure AD yet. Skipping manager assignment.")
        
        success, result = self._make_graph_request("POST", "users", azure_user_data)
        
        if success:
            # Update local user with Azure AD object ID
            user.azure_ad_object_id = result.get("id")
            user.azure_ad_sync_status = "synced"
            user.azure_ad_last_sync = django_timezone.now()
            user.azure_ad_sync_error = ""  # Clear any previous errors
            user.save()
            
            logger.info(f"Successfully created Azure AD user for {user.email}")
            return True, {
                "azure_ad_object_id": result.get("id"),
                "temporary_password": temp_password,
                "message": "User created successfully in Azure AD"
            }
        else:
            # Update sync status to failed with error details
            user.azure_ad_sync_status = "failed"
            error_message = f"{result.get('error', 'Unknown error')}: {result.get('details', 'No details available')}"
            user.azure_ad_sync_error = error_message
            user.save()
            
            logger.error(f"Failed to create Azure AD user for {user.email}: {result}")
            return False, result
    
    def update_user(self, user: User) -> Tuple[bool, Dict]:
        """
        Update a user in Azure AD.
        """
        azure_settings = self._get_settings()
        
        if not azure_settings.is_configured:
            return False, {"error": "Azure AD is not configured"}
            
        if not azure_settings.enabled or not azure_settings.sync_enabled:
            return False, {"error": "Azure AD sync is disabled"}
        
        if not user.azure_ad_object_id:
            return False, {"error": "User does not exist in Azure AD"}
        
        # Prepare update data with proper validation
        update_data = {
            "accountEnabled": user.is_active,
            "displayName": user.get_full_name(),
            "mail": user.business_email if user.business_email else user.email,  # Use business_email for Azure AD email, fallback to email
            "givenName": user.first_name,
            "surname": user.last_name,
        }
        
        # Add job title if present and valid (1-128 characters)
        if user.job_title and len(user.job_title.strip()) > 0:
            job_title = user.job_title.strip()
            if len(job_title) <= 128:
                update_data["jobTitle"] = job_title
            else:
                update_data["jobTitle"] = job_title[:128]  # Truncate to 128 chars
        
        # Add department if present and valid
        if user.department:
            department_name = user.department.name.strip() if user.department.name else ""
            if len(department_name) > 0:
                if len(department_name) <= 64:  # Department field limit in Azure AD
                    update_data["department"] = department_name
                else:
                    update_data["department"] = department_name[:64]  # Truncate to 64 chars
        
        # Add phone number if available
        if user.phone_number:
            update_data["businessPhones"] = [user.phone_number]
        else:
            update_data["businessPhones"] = []
        
        # Add company name if available
        if user.company_name:
            update_data["companyName"] = user.company_name.strip()[:64]  # Azure AD limit
        
        # Add employee ID if available
        if user.employee_id:
            update_data["employeeId"] = user.employee_id.strip()[:16]  # Azure AD limit
        
        # Add employee type if available
        if user.employee_type:
            update_data["employeeType"] = user.get_employee_type_display()
        
        # Add hire date if available
        if user.hire_date:
            update_data["employeeHireDate"] = user.hire_date.isoformat()
        
        # Add office location if available
        if user.office_location:
            update_data["officeLocation"] = user.office_location.strip()[:128]  # Azure AD limit
        
        # Add manager if available
        if user.manager and user.manager.azure_ad_object_id:
            # Use proper Microsoft Graph API format for manager reference
            update_data["manager@odata.bind"] = f"https://graph.microsoft.com/v1.0/users/{user.manager.azure_ad_object_id}"
            logger.info(f"Updating manager for {user.email}: {user.manager.email} (Azure ID: {user.manager.azure_ad_object_id})")
        elif user.manager and not user.manager.azure_ad_object_id:
            logger.warning(f"Manager {user.manager.email} for user {user.email} is not synced to Azure AD yet. Skipping manager assignment.")
        elif user.manager is None:
            # Remove manager reference if no manager is set
            update_data["manager@odata.bind"] = None
            logger.info(f"Removing manager for {user.email}")
        
        success, result = self._make_graph_request(
            "PATCH", 
            f"users/{user.azure_ad_object_id}", 
            update_data
        )
        
        if success:
            user.azure_ad_sync_status = "synced"
            user.azure_ad_last_sync = django_timezone.now()
            user.azure_ad_sync_error = ""  # Clear any previous errors
            user.save()
            
            logger.info(f"Successfully updated Azure AD user for {user.email}")
            return True, {"message": "User updated successfully in Azure AD"}
        else:
            user.azure_ad_sync_status = "failed"
            error_message = f"{result.get('error', 'Unknown error')}: {result.get('details', 'No details available')}"
            user.azure_ad_sync_error = error_message
            user.save()
            
            logger.error(f"Failed to update Azure AD user for {user.email}: {result}")
            return False, result
    
    def disable_user(self, user: User) -> Tuple[bool, Dict]:
        """
        Disable a user in Azure AD.
        """
        azure_settings = self._get_settings()
        
        if not azure_settings.is_configured:
            return False, {"error": "Azure AD is not configured"}
            
        if not azure_settings.enabled or not azure_settings.sync_enabled:
            return False, {"error": "Azure AD sync is disabled"}
        
        if not user.azure_ad_object_id:
            return False, {"error": "User does not exist in Azure AD"}
        
        success, result = self._make_graph_request(
            "PATCH",
            f"users/{user.azure_ad_object_id}",
            {"accountEnabled": False}
        )
        
        if success:
            user.azure_ad_sync_status = "synced"
            user.azure_ad_last_sync = django_timezone.now()
            user.save()
            
            logger.info(f"Successfully disabled Azure AD user for {user.email}")
            return True, {"message": "User disabled successfully in Azure AD"}
        else:
            user.azure_ad_sync_status = "failed"
            user.save()
            
            logger.error(f"Failed to disable Azure AD user for {user.email}: {result}")
            return False, result
    
    def delete_user(self, user: User) -> Tuple[bool, Dict]:
        """
        Delete a user from Azure AD (hard delete).
        """
        azure_settings = self._get_settings()
        
        if not azure_settings.is_configured:
            return False, {"error": "Azure AD is not configured"}
            
        if not azure_settings.enabled or not azure_settings.sync_enabled:
            return False, {"error": "Azure AD sync is disabled"}
        
        if not user.azure_ad_object_id:
            return False, {"error": "User does not exist in Azure AD"}
        
        success, result = self._make_graph_request(
            "DELETE",
            f"users/{user.azure_ad_object_id}"
        )
        
        if success:
            # Clear Azure AD fields from local user
            user.azure_ad_object_id = None
            user.azure_ad_sync_status = "disabled"
            user.azure_ad_last_sync = django_timezone.now()
            user.save()
            
            logger.info(f"Successfully deleted Azure AD user for {user.email}")
            return True, {"message": "User deleted successfully from Azure AD"}
        else:
            user.azure_ad_sync_status = "failed"
            user.save()
            
            logger.error(f"Failed to delete Azure AD user for {user.email}: {result}")
            return False, result
    
    def get_user(self, azure_ad_object_id: str) -> Tuple[bool, Dict]:
        """
        Get user details from Azure AD.
        """
        azure_settings = self._get_settings()
        
        if not azure_settings.is_configured:
            return False, {"error": "Azure AD is not configured"}
            
        if not azure_settings.enabled:
            return False, {"error": "Azure AD is disabled"}
        
        success, result = self._make_graph_request("GET", f"users/{azure_ad_object_id}")
        
        if success:
            logger.info(f"Successfully retrieved Azure AD user: {azure_ad_object_id}")
            return True, result
        else:
            logger.error(f"Failed to retrieve Azure AD user {azure_ad_object_id}: {result}")
            return False, result
    
    def sync_user_from_hris(self, user: User, force_create: bool = False) -> Tuple[bool, Dict]:
        """
        Sync a user from HRIS to Azure AD.
        
        Args:
            user: The User instance to sync
            force_create: If True, create user even if sync is disabled for this user
        """
        if not user.azure_ad_sync_enabled and not force_create:
            return False, {"error": "Azure AD sync is disabled for this user"}
        
        if user.azure_ad_object_id:
            # User exists, update it
            return self.update_user(user)
        else:
            # User doesn't exist, create it
            return self.create_user(user)
    
    def test_connection(self) -> Tuple[bool, Dict]:
        """
        Test the connection to Microsoft Graph API.
        """
        azure_settings = self._get_settings()
        
        if not azure_settings.is_configured:
            return False, {
                "error": "Azure AD is not configured",
                "details": "Please configure tenant ID, client ID, and client secret"
            }
        
        # Test token acquisition first
        try:
            token = self._get_access_token()
            if not token:
                return False, {
                    "error": "Failed to acquire access token",
                    "details": "Check client credentials and permissions"
                }
        except Exception as e:
            return False, {
                "error": "Token acquisition failed",
                "details": str(e)
            }
        
        # Test API connectivity with a simple endpoint that requires minimal permissions
        # Using /organization instead of /me as it works with application permissions
        success, result = self._make_graph_request("GET", "organization")
        
        if success:
            return True, {
                "message": "Successfully connected to Microsoft Graph API",
                "tenant_info": result.get("value", [{}])[0] if result.get("value") else {},
                "token_acquired": True
            }
        else:
            # Provide more detailed error information
            error_details = result.get("details", "Unknown error")
            
            # Parse common error scenarios
            if "401" in str(error_details):
                error_msg = "Authentication failed - check client ID and secret"
            elif "403" in str(error_details):
                error_msg = "Access denied - check API permissions"
            elif "404" in str(error_details):
                error_msg = "Endpoint not found - check tenant ID"
            else:
                error_msg = "Failed to connect to Microsoft Graph API"
            
            return False, {
                "error": error_msg,
                "details": error_details,
                "troubleshooting": {
                    "check_tenant_id": azure_settings.tenant_id[:8] + "..." if azure_settings.tenant_id else "Not set",
                    "check_client_id": azure_settings.client_id[:8] + "..." if azure_settings.client_id else "Not set",
                    "check_client_secret": "Set" if azure_settings.client_secret else "Not set",
                    "authority_url": azure_settings.authority_url
                }
            }


# Global service instance
azure_ad_service = AzureADService()