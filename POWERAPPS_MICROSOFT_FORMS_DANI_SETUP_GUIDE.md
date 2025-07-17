# PowerApps + Microsoft Forms + DANI HRIS Integration Setup Guide

## Overview

This comprehensive guide walks you through setting up a complete integration between PowerApps forms, Microsoft Forms, and the DANI HRIS system for automated job application processing.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [DANI HRIS Configuration](#dani-hris-configuration)
3. [PowerApps Form Creation](#powerapps-form-creation)
4. [Microsoft Forms Integration](#microsoft-forms-integration)
5. [Testing the Integration](#testing-the-integration)
6. [Troubleshooting](#troubleshooting)
7. [Advanced Configuration](#advanced-configuration)

---

## Prerequisites

### System Requirements

- **DANI HRIS**: Version 1.0+ deployed and accessible
- **Microsoft 365**: Business or Enterprise subscription
- **PowerApps**: Access to PowerApps environment
- **Microsoft Forms**: Access to Microsoft Forms (included with M365)

### Required Permissions

- **DANI HRIS**: Admin or HR Manager access
- **PowerApps**: Environment Maker or higher
- **Microsoft Forms**: Form creation permissions

### Technical Requirements

- Valid SSL certificate for DANI HRIS deployment
- Network connectivity between Microsoft services and DANI HRIS
- Email configuration for notifications (optional)

---

## DANI HRIS Configuration

### Step 1: Create PowerApps Configuration

1. **Access DANI Admin Panel**
   - Navigate to your DANI HRIS instance
   - Log in with admin credentials
   - Go to `/admin/` (Django admin interface)

2. **Create PowerApps Configuration**
   - Navigate to **Recruitment** → **PowerApps configurations**
   - Click **"Add PowerApps configuration"**
   - Fill in the following fields:

   ```yaml
   Basic Configuration:
   - Name: "Job Application Form"
   - Description: "PowerApps form for job applications"
   - Status: "Active"
   - Auto assign to job: [Select target job posting]
   - Default application source: "PowerApps Form"
   ```

3. **Configure API Connection**
   - The system will automatically generate an API key
   - **Important**: Copy the API key and endpoint URL - you'll need these for PowerApps
   - Add allowed origins (PowerApps URLs):
     ```json
     [
       "https://apps.powerapps.com",
       "https://apps.preview.powerapps.com",
       "https://make.powerapps.com"
     ]
     ```

4. **Set Up Field Mapping**
   - Configure the mapping between PowerApps fields and DANI fields:
   ```json
   {
     "firstName": "first_name",
     "lastName": "last_name",
     "emailAddress": "email",
     "phoneNumber": "phone",
     "currentLocation": "current_location",
     "yearsOfExperience": "years_of_experience",
     "currentSalary": "current_salary",
     "expectedSalary": "expected_salary",
     "linkedInUrl": "linkedin_url",
     "portfolioUrl": "portfolio_url",
     "willingToRelocate": "willing_to_relocate",
     "availableStartDate": "available_start_date"
   }
   ```

5. **Configure Required Fields**
   ```json
   [
     "firstName",
     "lastName",
     "emailAddress",
     "resume_file"
   ]
   ```

6. **File Upload Settings**
   - Resume field name: `resume_file`
   - Cover letter field name: `cover_letter_file`
   - Max file size: `10` MB
   - Allowed file types: `["pdf", "doc", "docx"]`

7. **Workflow Settings**
   - Enable auto-send confirmation: `✓`
   - Add notification emails: `["hr@company.com", "recruiter@company.com"]`
   - Custom confirmation email template (optional)

8. **Save Configuration**
   - Click **"Save"**
   - Note down the API endpoint URL and API key

### Step 2: Verify Job Posting

1. **Create Target Job Posting**
   - Go to **Recruitment** → **Job postings**
   - Create or verify the job posting exists
   - Set status to **"Active"**
   - Note the job ID for PowerApps configuration

2. **Test API Endpoint**
   - Use a tool like Postman or curl to test the endpoint
   - URL: `https://your-dani-instance.com/api/recruitment/powerapps/YOUR_API_KEY/`
   - Method: `POST`
   - Headers: `Content-Type: application/json`

---

## PowerApps Form Creation

### Step 3: Create PowerApps Application

1. **Access PowerApps**
   - Navigate to [PowerApps](https://make.powerapps.com)
   - Select your environment
   - Click **"Create"** → **"Canvas app"** → **"Blank app"**

2. **Design Form Layout**
   - **App Name**: "Job Application Form"
   - **Format**: Phone or Tablet (based on your needs)

3. **Add Form Controls**

   Add the following controls to your form:

   ```yaml
   Personal Information:
   - Text Input: firstName (Display Name: "First Name")
   - Text Input: lastName (Display Name: "Last Name")
   - Text Input: emailAddress (Display Name: "Email Address")
   - Text Input: phoneNumber (Display Name: "Phone Number")
   ```

   ```yaml
   Professional Information:
   - Text Input: currentLocation (Display Name: "Current Location")
   - Number Input: yearsOfExperience (Display Name: "Years of Experience")
   - Number Input: currentSalary (Display Name: "Current Salary")
   - Number Input: expectedSalary (Display Name: "Expected Salary")
   - Text Input: linkedInUrl (Display Name: "LinkedIn Profile")
   - Text Input: portfolioUrl (Display Name: "Portfolio URL")
   - Toggle: willingToRelocate (Display Name: "Willing to Relocate")
   - Date Picker: availableStartDate (Display Name: "Available Start Date")
   ```

   ```yaml
   File Uploads:
   - Add Media Button: btnResumeUpload (Display Name: "Upload Resume")
   - Add Media Button: btnCoverLetterUpload (Display Name: "Upload Cover Letter")
   - Label: lblResumeStatus (Display Name: "Resume: Not Selected")
   - Label: lblCoverLetterStatus (Display Name: "Cover Letter: Not Selected")
   ```

   ```yaml
   Submission:
   - Button: btnSubmit (Display Name: "Submit Application")
   - Label: lblStatus (Display Name: "Status: Ready to Submit")
   ```

### Step 4: Configure File Upload Logic

1. **Resume Upload Button (btnResumeUpload)**

   **OnSelect Property:**
   ```javascript
   Set(varResumeFile, 
     {
       file: Last(
         First(Media.AddMediaWithOptionalData(
           {
             Title: "Select Resume",
             Extensions: ".pdf,.doc,.docx",
             MaxSize: 10000000
           }
         )).Value
       ),
       fileName: Last(
         First(Media.AddMediaWithOptionalData(
           {
             Title: "Select Resume", 
             Extensions: ".pdf,.doc,.docx",
             MaxSize: 10000000
           }
         )).Value
       ).Name
     }
   );
   
   If(IsBlank(varResumeFile.file),
     UpdateContext({resumeSelected: false}),
     UpdateContext({resumeSelected: true})
   )
   ```

2. **Resume Status Label (lblResumeStatus)**

   **Text Property:**
   ```javascript
   If(resumeSelected,
     "Resume: " & varResumeFile.fileName,
     "Resume: Not Selected"
   )
   ```

3. **Cover Letter Upload Button (btnCoverLetterUpload)**

   **OnSelect Property:**
   ```javascript
   Set(varCoverLetterFile, 
     {
       file: Last(
         First(Media.AddMediaWithOptionalData(
           {
             Title: "Select Cover Letter",
             Extensions: ".pdf,.doc,.docx",
             MaxSize: 10000000
           }
         )).Value
       ),
       fileName: Last(
         First(Media.AddMediaWithOptionalData(
           {
             Title: "Select Cover Letter", 
             Extensions: ".pdf,.doc,.docx",
             MaxSize: 10000000
           }
         )).Value
       ).Name
     }
   );
   
   If(IsBlank(varCoverLetterFile.file),
     UpdateContext({coverLetterSelected: false}),
     UpdateContext({coverLetterSelected: true})
   )
   ```

### Step 5: Configure Form Submission

1. **Submit Button (btnSubmit)**

   **OnSelect Property:**
   ```javascript
   // Validate required fields
   If(IsBlank(firstName.Text) || IsBlank(lastName.Text) || IsBlank(emailAddress.Text) || !resumeSelected,
     UpdateContext({
       submitStatus: "Error: Please fill in all required fields and upload a resume"
     }),
     
     // Prepare submission data
     Set(varSubmissionData, {
       firstName: firstName.Text,
       lastName: lastName.Text,
       emailAddress: emailAddress.Text,
       phoneNumber: phoneNumber.Text,
       currentLocation: currentLocation.Text,
       yearsOfExperience: Value(yearsOfExperience.Text),
       currentSalary: Value(currentSalary.Text),
       expectedSalary: Value(expectedSalary.Text),
       linkedInUrl: linkedInUrl.Text,
       portfolioUrl: portfolioUrl.Text,
       willingToRelocate: willingToRelocate.Value,
       availableStartDate: Text(availableStartDate.SelectedDate, "yyyy-mm-dd"),
       resume_file: "data:application/pdf;base64," & EncodeUrl(varResumeFile.file),
       cover_letter_file: If(coverLetterSelected, "data:application/pdf;base64," & EncodeUrl(varCoverLetterFile.file), "")
     });
     
     // Update status
     UpdateContext({submitStatus: "Submitting application..."});
     
     // Submit to DANI HRIS
     Set(varSubmissionResult,
       With(
         {
           url: "https://your-dani-instance.com/api/recruitment/powerapps/YOUR_API_KEY/",
           headers: {
             "Content-Type": "application/json"
           },
           body: JSON(varSubmissionData)
         },
         
         // Make HTTP POST request
         Switch(
           With(
             {response: 
               HTTPRequest(
                 url,
                 {
                   method: "POST",
                   headers: headers,
                   body: body
                 }
               )
             },
             
             // Handle response
             If(response.responseCode = 201 || response.responseCode = 200,
               UpdateContext({
                 submitStatus: "Application submitted successfully! You will receive a confirmation email shortly."
               });
               
               // Reset form
               Reset(firstName);
               Reset(lastName);
               Reset(emailAddress);
               Reset(phoneNumber);
               Reset(currentLocation);
               Reset(yearsOfExperience);
               Reset(currentSalary);
               Reset(expectedSalary);
               Reset(linkedInUrl);
               Reset(portfolioUrl);
               Reset(willingToRelocate);
               Reset(availableStartDate);
               Set(varResumeFile, Blank());
               Set(varCoverLetterFile, Blank());
               UpdateContext({resumeSelected: false});
               UpdateContext({coverLetterSelected: false});
               
               true,
               
               // Handle errors
               UpdateContext({
                 submitStatus: "Error: " & response.responseText
               });
               false
             )
           )
         )
       )
     )
   )
   ```

2. **Status Label (lblStatus)**

   **Text Property:**
   ```javascript
   If(IsBlank(submitStatus), "Status: Ready to Submit", submitStatus)
   ```

3. **Submit Button Display Mode**

   **DisplayMode Property:**
   ```javascript
   If(IsBlank(firstName.Text) || IsBlank(lastName.Text) || IsBlank(emailAddress.Text) || !resumeSelected,
     DisplayMode.Disabled,
     DisplayMode.Edit
   )
   ```

### Step 6: Configure App Settings

1. **App OnStart Property**
   ```javascript
   Set(varResumeFile, Blank());
   Set(varCoverLetterFile, Blank());
   UpdateContext({resumeSelected: false});
   UpdateContext({coverLetterSelected: false});
   UpdateContext({submitStatus: ""});
   ```

2. **Save and Publish**
   - Click **"File"** → **"Save"**
   - Click **"Publish"** → **"Publish this version"**
   - Note the app URL for sharing

---

## Microsoft Forms Integration

### Step 7: Create Microsoft Form (Alternative Method)

If you prefer using Microsoft Forms instead of a custom PowerApps form:

1. **Create Microsoft Form**
   - Go to [Microsoft Forms](https://forms.office.com)
   - Click **"New Form"**
   - Name: "Job Application Form"

2. **Add Form Questions**

   ```yaml
   Question 1: First Name
   - Type: Text
   - Required: Yes
   
   Question 2: Last Name
   - Type: Text
   - Required: Yes
   
   Question 3: Email Address
   - Type: Text
   - Required: Yes
   - Validation: Email format
   
   Question 4: Phone Number
   - Type: Text
   - Required: Yes
   
   Question 5: Current Location
   - Type: Text
   - Required: No
   
   Question 6: Years of Experience
   - Type: Number
   - Required: No
   
   Question 7: Current Salary
   - Type: Number
   - Required: No
   
   Question 8: Expected Salary
   - Type: Number
   - Required: No
   
   Question 9: LinkedIn Profile
   - Type: Text
   - Required: No
   
   Question 10: Portfolio URL
   - Type: Text
   - Required: No
   
   Question 11: Willing to Relocate
   - Type: Choice (Yes/No)
   - Required: No
   
   Question 12: Available Start Date
   - Type: Date
   - Required: No
   
   Question 13: Resume Upload
   - Type: File Upload
   - Required: Yes
   - File Types: PDF, DOC, DOCX
   - Max Size: 10 MB
   
   Question 14: Cover Letter Upload
   - Type: File Upload
   - Required: No
   - File Types: PDF, DOC, DOCX
   - Max Size: 10 MB
   ```

3. **Configure Form Settings**
   - **Collect responses**: On
   - **Anyone can respond**: Yes (or restrict as needed)
   - **Record name**: Off
   - **Shuffle questions**: Off
   - **Customized thank you message**: "Thank you for your application. We will review it and get back to you soon."

### Step 8: Create Power Automate Flow

1. **Create New Flow**
   - Go to [Power Automate](https://flow.microsoft.com)
   - Click **"Create"** → **"Automated cloud flow"**
   - Name: "Process Job Application from Forms"
   - Trigger: **"When a new response is submitted"** (Microsoft Forms)

2. **Configure Trigger**
   - Select your Microsoft Form
   - Click **"New step"**

3. **Get Response Details**
   - Add action: **"Get response details"** (Microsoft Forms)
   - Form ID: [Your form ID]
   - Response ID: [Dynamic content from trigger]

4. **Transform Data**
   - Add action: **"Compose"** (Data Operation)
   - Configure inputs to match DANI field mapping:

   ```json
   {
     "firstName": "@{outputs('Get_response_details')?['body/r1']}",
     "lastName": "@{outputs('Get_response_details')?['body/r2']}",
     "emailAddress": "@{outputs('Get_response_details')?['body/r3']}",
     "phoneNumber": "@{outputs('Get_response_details')?['body/r4']}",
     "currentLocation": "@{outputs('Get_response_details')?['body/r5']}",
     "yearsOfExperience": "@{outputs('Get_response_details')?['body/r6']}",
     "currentSalary": "@{outputs('Get_response_details')?['body/r7']}",
     "expectedSalary": "@{outputs('Get_response_details')?['body/r8']}",
     "linkedInUrl": "@{outputs('Get_response_details')?['body/r9']}",
     "portfolioUrl": "@{outputs('Get_response_details')?['body/r10']}",
     "willingToRelocate": "@{if(equals(outputs('Get_response_details')?['body/r11'], 'Yes'), true, false)}",
     "availableStartDate": "@{outputs('Get_response_details')?['body/r12']}",
     "resume_file": "@{outputs('Get_response_details')?['body/r13']}",
     "cover_letter_file": "@{outputs('Get_response_details')?['body/r14']}"
   }
   ```

5. **Process File Uploads**
   - Add action: **"Get file content"** (OneDrive/SharePoint)
   - File: [Dynamic content from resume upload]
   - Convert to base64: Yes

6. **Submit to DANI HRIS**
   - Add action: **"HTTP"** (Premium connector)
   - Method: **POST**
   - URI: `https://your-dani-instance.com/api/recruitment/powerapps/YOUR_API_KEY/`
   - Headers:
     ```json
     {
       "Content-Type": "application/json"
     }
     ```
   - Body: [Output from Compose action]

7. **Handle Response**
   - Add action: **"Condition"** (Control)
   - Condition: `@{outputs('HTTP')?['statusCode']}` equals `201`
   - **If yes**: Add success actions (email notification, etc.)
   - **If no**: Add error handling actions

8. **Save and Test**
   - Click **"Save"**
   - Test the flow with a sample form submission

---

## Testing the Integration

### Step 9: End-to-End Testing

1. **Test Form Submission**
   - Submit a test application through PowerApps or Microsoft Forms
   - Include all required fields
   - Upload test resume and cover letter files

2. **Verify DANI HRIS Processing**
   - Check the DANI admin panel for new applicant record
   - Verify all fields are mapped correctly
   - Check file uploads are processed successfully

3. **Test Email Notifications**
   - Confirm applicant receives confirmation email
   - Verify HR team receives notification emails

4. **Test Error Handling**
   - Submit form with missing required fields
   - Submit form with invalid file types
   - Submit form with oversized files
   - Verify appropriate error messages are shown

### Step 10: Validate API Response

1. **Successful Submission Response**
   ```json
   {
     "success": true,
     "message": "Application submitted successfully",
     "applicant_id": 123,
     "operation_id": "powerapps_abc12345",
     "job_title": "Software Engineer"
   }
   ```

2. **Error Response Examples**
   ```json
   {
     "success": false,
     "error": "Missing required fields: firstName, lastName",
     "missing_fields": ["firstName", "lastName"],
     "operation_id": "powerapps_abc12345"
   }
   ```

   ```json
   {
     "success": false,
     "error": "File size (15.2MB) exceeds maximum allowed (10MB)",
     "operation_id": "powerapps_abc12345"
   }
   ```

---

## Troubleshooting

### Common Issues and Solutions

1. **CORS Errors**
   - **Issue**: `Access-Control-Allow-Origin` errors
   - **Solution**: Add PowerApps URLs to allowed origins in DANI configuration
   - **Check**: Verify middleware is properly configured

2. **File Upload Failures**
   - **Issue**: Large files not uploading
   - **Solution**: Adjust `max_file_size_mb` in DANI configuration
   - **Check**: Verify file type is in allowed list

3. **Authentication Errors**
   - **Issue**: `Invalid API key` error
   - **Solution**: Verify API key is correct and configuration is active
   - **Check**: Ensure API key hasn't been regenerated

4. **Field Mapping Issues**
   - **Issue**: Data not appearing in DANI
   - **Solution**: Verify field mapping in PowerApps configuration
   - **Check**: Ensure PowerApps field names match mapping keys

5. **Email Delivery Issues**
   - **Issue**: Confirmation emails not sent
   - **Solution**: Check DANI email configuration in settings
   - **Check**: Verify SMTP settings and credentials

### Debug Steps

1. **Check DANI Logs**
   ```bash
   # View PowerApps integration logs
   tail -f /path/to/dani/logs/dani_powerapps.log
   
   # Check general application logs
   tail -f /path/to/dani/logs/django.log
   ```

2. **Test API Endpoint Manually**
   ```bash
   curl -X POST \
     -H "Content-Type: application/json" \
     -d '{
       "firstName": "John",
       "lastName": "Doe",
       "emailAddress": "john.doe@example.com",
       "phoneNumber": "555-0123",
       "resume_file": "data:application/pdf;base64,JVBERi0xLjQKJcfs..."
     }' \
     "https://your-dani-instance.com/api/recruitment/powerapps/YOUR_API_KEY/"
   ```

3. **Verify Database Records**
   - Check the `applicants` table for new records
   - Verify file uploads in media directory
   - Check `powerapps_configurations` table for statistics

---

## Advanced Configuration

### Custom Field Validation

Add custom validation rules to PowerApps configuration:

```json
{
  "email_domain_validation": {
    "rule": "email.endsWith('@company.com')",
    "message": "Please use your company email address"
  },
  "experience_validation": {
    "rule": "yearsOfExperience >= 0 && yearsOfExperience <= 50",
    "message": "Years of experience must be between 0 and 50"
  },
  "salary_validation": {
    "rule": "expectedSalary >= currentSalary",
    "message": "Expected salary should be equal or greater than current salary"
  }
}
```

### Webhook Integration

Configure webhooks for real-time processing:

1. **Set up webhook endpoint** in your system
2. **Configure webhook URL** in DANI PowerApps configuration
3. **Handle webhook payload**:
   ```json
   {
     "event": "new_application",
     "operation_id": "powerapps_abc12345",
     "applicant": {
       "id": 123,
       "name": "John Doe",
       "email": "john.doe@example.com",
       "phone": "555-0123",
       "job_title": "Software Engineer",
       "source": "PowerApps Form",
       "applied_at": "2025-07-09T10:30:00Z"
     }
   }
   ```

### Multi-Language Support

Configure forms for multiple languages:

1. **Create separate PowerApps configurations** for each language
2. **Use different field mappings** if needed
3. **Configure language-specific email templates**
4. **Set up conditional logic** in PowerApps based on user language

### Advanced File Processing

Configure advanced file processing options:

```json
{
  "file_processing": {
    "extract_text": true,
    "virus_scan": true,
    "auto_categorize": true,
    "thumbnail_generation": true
  },
  "file_storage": {
    "cloud_provider": "aws_s3",
    "bucket_name": "dani-resumes",
    "encryption": "AES-256"
  }
}
```

### Analytics and Reporting

Set up advanced analytics:

1. **Enable detailed logging** in DANI configuration
2. **Configure Power BI integration** for dashboard
3. **Set up automated reports** for application metrics
4. **Create custom KPIs** for recruitment process

---

## Security Considerations

### API Security

1. **API Key Management**
   - Store API keys securely
   - Rotate keys regularly
   - Use different keys for different environments

2. **Input Validation**
   - Validate all form inputs
   - Sanitize file uploads
   - Check for malicious content

3. **Rate Limiting**
   - Configure appropriate rate limits
   - Monitor for suspicious activity
   - Implement IP blocking if needed

### Data Protection

1. **Encryption**
   - Encrypt data in transit (HTTPS)
   - Encrypt sensitive data at rest
   - Use secure file storage

2. **Access Control**
   - Implement role-based access
   - Audit access logs
   - Regular security reviews

3. **Compliance**
   - Ensure GDPR compliance
   - Implement data retention policies
   - Provide data deletion capabilities

---

## Maintenance and Updates

### Regular Maintenance Tasks

1. **Monthly**
   - Review API usage statistics
   - Check error logs
   - Verify email delivery rates

2. **Quarterly**
   - Update field mappings if needed
   - Review file storage usage
   - Performance optimization

3. **Annually**
   - Security audit
   - Update API keys
   - Review and update documentation

### Update Procedures

1. **PowerApps Updates**
   - Test in development environment
   - Backup current configuration
   - Deploy during maintenance window

2. **DANI Updates**
   - Check API compatibility
   - Update field mappings if needed
   - Test integration after updates

---

## Support and Resources

### Getting Help

1. **DANI HRIS Support**
   - Documentation: Check system documentation
   - Logs: Review application logs
   - Community: Join user forums

2. **Microsoft Support**
   - PowerApps documentation
   - Power Automate help
   - Microsoft Forms support

### Additional Resources

1. **API Documentation**
   - Endpoint specifications
   - Authentication details
   - Error code reference

2. **Best Practices**
   - Performance optimization
   - Security guidelines
   - Testing procedures

---

**Document Version**: 1.0  
**Last Updated**: July 2025  
**Next Review**: Quarterly  
**Maintained By**: DANI HRIS Development Team

---

*This guide provides comprehensive instructions for integrating PowerApps forms with Microsoft Forms and DANI HRIS. For additional support or customization requests, please contact the DANI HRIS support team.*