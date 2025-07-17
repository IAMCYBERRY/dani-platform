# Microsoft Forms → PowerApps → DANI HRIS Quick Start Guide

## Overview
This quick start guide will have you up and running with automated job application processing in 30 minutes or less.

**Flow**: Microsoft Forms → Power Automate → DANI HRIS

---

## Prerequisites ✅

- [ ] Microsoft 365 account with Forms and Power Automate access
- [ ] DANI HRIS system running and accessible
- [ ] DANI HRIS admin or HR manager account
- [ ] Active job posting in DANI HRIS

---

## Step 1: Create Microsoft Form (5 minutes)

### 1.1 Create the Form
1. Go to [https://forms.office.com](https://forms.office.com)
2. Click **"New Form"**
3. **Title**: "Job Application Form"
4. **Description**: "Apply for open positions at our company"

### 1.2 Add Questions (copy exactly as shown)
**Add these questions in this exact order:**

```
Question 1: First Name
- Type: Text (Short answer)
- Required: ✓

Question 2: Last Name  
- Type: Text (Short answer)
- Required: ✓

Question 3: Email Address
- Type: Text (Long answer)
- Required: ✓
- Add restriction: "Must be a valid email"

Question 4: Phone Number
- Type: Text (Short answer)
- Required: ✓

Question 5: Current Location
- Type: Text (Short answer)
- Required: ✗

Question 6: Years of Experience
- Type: Number
- Required: ✗
- Restrictions: Between 0 and 50

Question 7: Current Salary (USD)
- Type: Number
- Required: ✗

Question 8: Expected Salary (USD)
- Type: Number
- Required: ✗

Question 9: LinkedIn Profile URL
- Type: Text (Long answer)
- Required: ✗

Question 10: Portfolio/Website URL
- Type: Text (Long answer)
- Required: ✗

Question 11: Willing to Relocate?
- Type: Choice
- Options: Yes, No
- Required: ✗

Question 12: Available Start Date
- Type: Date
- Required: ✗

Question 13: Resume Upload
- Type: File upload
- Required: ✓
- Settings: One file, 10MB max, .pdf/.doc/.docx only

Question 14: Cover Letter Upload
- Type: File upload
- Required: ✗
- Settings: One file, 10MB max, .pdf/.doc/.docx only
```

### 1.3 Configure Form Settings
1. Click **Settings** (gear icon)
2. **Who can fill out this form**: "Anyone with the link"
3. **Response options**: 
   - ✗ Record name
   - ✓ One response per person
4. Click **"Apply"**

### 1.4 Save Form Details
1. Click **"Share"** to get the form link
2. **Copy and save**:
   - Form URL: `https://forms.office.com/r/YOUR_FORM_ID`
   - Form ID: The part after `/r/` in the URL

---

## Step 2: Configure DANI HRIS (10 minutes)

### 2.1 Access DANI Console
1. Login to DANI HRIS: `https://your-dani-instance.com`
2. Navigate to **Recruitment** → **PowerApps Integration**
3. Click **"Add New Configuration"**

### 2.2 Create PowerApps Configuration
**Fill out the configuration form:**

```yaml
Basic Settings:
- Configuration Name: "Microsoft Forms Integration"
- Description: "Job applications from Microsoft Forms"
- Status: "Active"

Job Assignment:
- Auto-assign to Job: [Select your target job posting]
- Default Application Source: "Microsoft Forms"

API Settings:
- API Key: [Auto-generated - copy this value]
- Rate Limit: 100 per hour
- Allowed Origins: 
  - https://prod-00.westus.logic.azure.com
  - https://prod-01.westus.logic.azure.com
  - https://prod-02.westus.logic.azure.com
  - https://prod-03.westus.logic.azure.com
  - https://prod-04.westus.logic.azure.com
  - https://prod-05.westus.logic.azure.com

Field Mapping:
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

Required Fields:
- firstName
- lastName
- emailAddress
- phoneNumber
- resume_file

File Upload Settings:
- Resume Field Name: "resume_file"
- Cover Letter Field Name: "cover_letter_file"
- Max File Size: 10 MB
- Allowed File Types: ["pdf", "doc", "docx"]

Email Settings:
- Send Confirmation Email: ✓
- Notification Emails: ["hr@company.com", "hiring@company.com"]
- Custom Email Template: [Leave blank for default]

Security Settings:
- Email Domain Restrictions: [Leave blank or add your domains]
- Enable Duplicate Detection: ✓
- Require Email Verification: ✗
```

### 2.3 Save Configuration
1. Click **"Save Configuration"**
2. **Copy and save these values**:
   - API Key: `dani_powerapps_xxxxxxxxxxxxx`
   - API Endpoint: `https://your-dani-instance.com/api/recruitment/powerapps/YOUR_API_KEY/`

---

## Step 3: Create Power Automate Flow (10 minutes)

### 3.1 Create New Flow
1. Go to [https://flow.microsoft.com](https://flow.microsoft.com)
2. Click **"Create"** → **"Automated cloud flow"**
3. **Flow name**: "Process Microsoft Forms to DANI"
4. **Choose trigger**: "When a new response is submitted (Microsoft Forms)"
5. Click **"Create"**

### 3.2 Configure Form Trigger
1. **Form Id**: Select your Microsoft Form from the dropdown
2. Click **"New step"**

### 3.3 Get Response Details
1. Search for and add: **"Get response details (Microsoft Forms)"**
2. **Form Id**: Select your form
3. **Response Id**: Select "Response Id" from dynamic content
4. Click **"New step"**

### 3.4 Get File Contents (Resume)
1. Search for and add: **"Get file content (OneDrive for Business)"**
2. **File**: Click in the field and select the resume upload response from dynamic content
3. **Convert to Base64**: Yes
4. **Rename this step**: "Get Resume Content"
5. Click **"New step"**

### 3.5 Get File Contents (Cover Letter)
1. Add another: **"Get file content (OneDrive for Business)"**
2. **File**: Select the cover letter upload response from dynamic content
3. **Convert to Base64**: Yes
4. **Rename this step**: "Get Cover Letter Content"
5. Click **"New step"**

### 3.6 Compose API Payload
1. Search for and add: **"Compose (Data Operation)"**
2. **Inputs**: Copy and paste this JSON (replace with your actual response IDs):

```json
{
  "firstName": "@{outputs('Get_response_details')?['body/r1']}",
  "lastName": "@{outputs('Get_response_details')?['body/r2']}",
  "emailAddress": "@{outputs('Get_response_details')?['body/r3']}",
  "phoneNumber": "@{outputs('Get_response_details')?['body/r4']}",
  "currentLocation": "@{outputs('Get_response_details')?['body/r5']}",
  "yearsOfExperience": "@{if(empty(outputs('Get_response_details')?['body/r6']), 0, int(outputs('Get_response_details')?['body/r6']))}",
  "currentSalary": "@{if(empty(outputs('Get_response_details')?['body/r7']), 0, int(outputs('Get_response_details')?['body/r7']))}",
  "expectedSalary": "@{if(empty(outputs('Get_response_details')?['body/r8']), 0, int(outputs('Get_response_details')?['body/r8']))}",
  "linkedInUrl": "@{outputs('Get_response_details')?['body/r9']}",
  "portfolioUrl": "@{outputs('Get_response_details')?['body/r10']}",
  "willingToRelocate": "@{if(equals(outputs('Get_response_details')?['body/r11'], 'Yes'), true, false)}",
  "availableStartDate": "@{outputs('Get_response_details')?['body/r12']}",
  "resume_file": "@{if(empty(outputs('Get_Resume_Content')?['body']), '', concat('data:application/pdf;base64,', outputs('Get_Resume_Content')?['body']))}",
  "cover_letter_file": "@{if(empty(outputs('Get_Cover_Letter_Content')?['body']), '', concat('data:application/pdf;base64,', outputs('Get_Cover_Letter_Content')?['body']))}"
}
```

3. Click **"New step"**

### 3.7 Submit to DANI HRIS
1. Search for and add: **"HTTP"**
2. **Method**: POST
3. **URI**: `https://your-dani-instance.com/api/recruitment/powerapps/YOUR_API_KEY/`
4. **Headers**: Click "Add new parameter" → "Headers"
   ```json
   {
     "Content-Type": "application/json"
   }
   ```
5. **Body**: Select "Outputs" from the Compose step
6. Click **"New step"**

### 3.8 Add Success/Error Handling
1. Search for and add: **"Condition"**
2. **Choose a value**: Select "Status code" from HTTP step
3. **Condition**: "is equal to"
4. **Value**: `201`

**If Yes (Success):**
1. Add action: **"Send an email (Office 365 Outlook)"**
2. **To**: `hr@company.com`
3. **Subject**: `✅ New Application: @{outputs('Get_response_details')?['body/r1']} @{outputs('Get_response_details')?['body/r2']}`
4. **Body**:
```
A new job application has been successfully processed and added to DANI HRIS.

Applicant Details:
- Name: @{outputs('Get_response_details')?['body/r1']} @{outputs('Get_response_details')?['body/r2']}
- Email: @{outputs('Get_response_details')?['body/r3']}
- Phone: @{outputs('Get_response_details')?['body/r4']}
- DANI Applicant ID: @{outputs('HTTP')?['body']?['applicant_id']}

Please review the application in DANI HRIS.
```

**If No (Error):**
1. Add action: **"Send an email (Office 365 Outlook)"**
2. **To**: `admin@company.com`
3. **Subject**: `❌ Application Processing Error: @{outputs('Get_response_details')?['body/r1']} @{outputs('Get_response_details')?['body/r2']}`
4. **Body**:
```
Error processing job application submission.

Applicant: @{outputs('Get_response_details')?['body/r1']} @{outputs('Get_response_details')?['body/r2']}
Email: @{outputs('Get_response_details')?['body/r3']}
Error Code: @{outputs('HTTP')?['statusCode']}
Error Message: @{outputs('HTTP')?['body']?['error']}

Please manually process this application.
```

### 3.9 Save Flow
1. Click **"Save"**
2. Wait for save confirmation

---

## Step 4: Test the Integration (5 minutes)

### 4.1 Submit Test Application
1. Open your Microsoft Form link
2. Fill out all required fields:
   - First Name: "Test"
   - Last Name: "Applicant"
   - Email: "test@company.com"
   - Phone: "555-0123"
   - Upload a test PDF for resume
3. Click **"Submit"**

### 4.2 Monitor Power Automate
1. Go to [https://flow.microsoft.com](https://flow.microsoft.com)
2. Click on your flow
3. Check **"Run history"**
4. Click on the latest run
5. Verify all steps completed successfully ✅

### 4.3 Verify DANI HRIS
1. Login to DANI HRIS
2. Go to **Recruitment** → **Applicants**
3. Look for your test applicant
4. Verify all fields populated correctly
5. Check that resume file uploaded

### 4.4 Check Email Notifications
1. Check HR email for success notification
2. Check test applicant email for confirmation

---

## Step 5: Go Live (2 minutes)

### 5.1 Share the Form
1. In Microsoft Forms, click **"Share"**
2. Copy the public link
3. **Share with**:
   - Post on company website
   - Include in job postings
   - Send to recruitment team
   - Add to email signatures

### 5.2 Monitor and Maintain
1. **Daily**: Check Power Automate run history
2. **Weekly**: Review DANI applicant reports
3. **Monthly**: Update form questions if needed

---

## Troubleshooting Quick Fixes

### ❌ **Power Automate Flow Fails**
**Check**: Response field mapping (r1, r2, r3, etc.)
**Fix**: Update field references in Compose step

### ❌ **DANI API Returns 401 Error**
**Check**: API key in HTTP step
**Fix**: Verify API key matches DANI configuration

### ❌ **Files Not Uploading**
**Check**: File size and format
**Fix**: Ensure files are under 10MB and PDF/DOC/DOCX

### ❌ **Email Notifications Not Working**
**Check**: Email addresses in DANI configuration
**Fix**: Update notification email list

### ❌ **Duplicate Applications**
**Check**: DANI duplicate detection setting
**Fix**: Enable duplicate detection in DANI configuration

---

## Success! 🎉

You now have a fully automated job application processing system:

1. **Candidates** fill out Microsoft Form
2. **Power Automate** processes submissions automatically
3. **DANI HRIS** receives and stores applications
4. **HR team** gets notified of new applications
5. **Candidates** receive confirmation emails

**Your system is processing applications 24/7 automatically!**

---

## Next Steps

- [ ] Add more job-specific questions to the form
- [ ] Create separate forms for different positions
- [ ] Set up advanced filtering and routing
- [ ] Add integration with your ATS
- [ ] Create dashboard for application metrics

---

**Setup Time**: ~30 minutes  
**Maintenance**: ~5 minutes per week  
**ROI**: Immediate automation of application processing

**Need help?** Check the detailed guides:
- `FORMS_TO_POWERAPPS_TO_DANI_CONNECTION_GUIDE.md`
- `POWERAPPS_MICROSOFT_FORMS_DANI_SETUP_GUIDE.md`