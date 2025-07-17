# Step-by-Step Guide: Connecting Microsoft Forms → PowerApps → DANI HRIS

## Overview
This guide provides detailed steps for connecting Microsoft Forms to PowerApps and then PowerApps to DANI HRIS for seamless job application processing.

## Connection Architecture
```
Microsoft Forms → Power Automate → PowerApps → DANI HRIS API
```

---

## Part 1: Microsoft Forms → PowerApps Connection

### Step 1: Create Microsoft Form

1. **Navigate to Microsoft Forms**
   - Go to [https://forms.office.com](https://forms.office.com)
   - Sign in with your Microsoft 365 account

2. **Create New Form**
   - Click **"New Form"**
   - Title: "Job Application Form"
   - Description: "Please fill out this form to apply for open positions"

3. **Add Questions** (in this exact order for easier mapping):
   ```
   Question 1: First Name
   - Type: Text
   - Required: Yes
   - Settings: Short answer
   
   Question 2: Last Name
   - Type: Text
   - Required: Yes
   - Settings: Short answer
   
   Question 3: Email Address
   - Type: Text
   - Required: Yes
   - Settings: Long answer
   - Restrictions: Must be a valid email
   
   Question 4: Phone Number
   - Type: Text
   - Required: Yes
   - Settings: Short answer
   
   Question 5: Current Location
   - Type: Text
   - Required: No
   - Settings: Short answer
   
   Question 6: Years of Experience
   - Type: Number
   - Required: No
   - Settings: Number between 0 and 50
   
   Question 7: Current Salary (USD)
   - Type: Number
   - Required: No
   - Settings: Number
   
   Question 8: Expected Salary (USD)
   - Type: Number
   - Required: No
   - Settings: Number
   
   Question 9: LinkedIn Profile URL
   - Type: Text
   - Required: No
   - Settings: Long answer
   
   Question 10: Portfolio/Website URL
   - Type: Text
   - Required: No
   - Settings: Long answer
   
   Question 11: Willing to Relocate?
   - Type: Choice
   - Required: No
   - Options: Yes, No
   
   Question 12: Available Start Date
   - Type: Date
   - Required: No
   
   Question 13: Resume Upload
   - Type: File upload
   - Required: Yes
   - Settings: One file, 10MB max
   - Allowed types: .pdf, .doc, .docx
   
   Question 14: Cover Letter Upload
   - Type: File upload
   - Required: No
   - Settings: One file, 10MB max
   - Allowed types: .pdf, .doc, .docx
   ```

4. **Configure Form Settings**
   - Click **"Settings"** (gear icon)
   - **Who can fill out this form**: Anyone with the link
   - **Response options**: 
     - ✓ Record name (optional)
     - ✓ One response per person
   - **Notification**: Turn off for now
   - Click **"Apply"**

5. **Note Form ID**
   - Copy the Form URL (you'll need this for PowerApps)
   - The Form ID is in the URL: `https://forms.office.com/r/YOUR_FORM_ID`

### Step 2: Create PowerApps Connection to Microsoft Forms

1. **Open PowerApps**
   - Navigate to [https://make.powerapps.com](https://make.powerapps.com)
   - Select your environment

2. **Create New Canvas App**
   - Click **"Create"**
   - Select **"Canvas app from blank"**
   - App name: "Job Application Dashboard"
   - Format: Tablet

3. **Add Microsoft Forms Data Source**
   - Click **"Data"** in the left panel
   - Click **"Add data"**
   - Search for **"Microsoft Forms"**
   - Click **"Microsoft Forms"**
   - Select your form from the list
   - Click **"Connect"**

4. **Add Display Gallery**
   - Insert → Gallery → **"Blank vertical gallery"**
   - Data source: Select your Microsoft Forms responses
   - Position: Top half of screen

5. **Configure Gallery Display**
   - Select the gallery
   - In the Items property, set:
   ```
   'Job Application Form'.GetResponses()
   ```
   - Add labels to show response data:
     - Label 1: `ThisItem.responder`
     - Label 2: `ThisItem.submitDate`
     - Label 3: `"Status: " & If(IsBlank(ThisItem.ProcessedToDani), "Pending", "Processed")`

---

## Part 2: PowerApps → DANI HRIS Connection

### Step 3: Configure DANI HRIS API Connection

1. **Get DANI API Details**
   - Login to DANI HRIS admin: `https://your-dani-instance.com/admin/`
   - Navigate to **Recruitment** → **PowerApps configurations**
   - Find your configuration or create new one
   - Copy the **API Key** and **API Endpoint URL**

2. **Add HTTP Connector to PowerApps**
   - In PowerApps, go to **"Data"** → **"Add data"**
   - Search for **"HTTP with Azure AD"** or **"HTTP"**
   - Select **"HTTP"** connector
   - Click **"Connect"**

3. **Create Processing Button**
   - Insert → Button
   - Text: "Process Selected Application"
   - Position: Below the gallery

### Step 4: Configure Form Data Processing

1. **Add Button OnSelect Logic**
   - Select the button
   - In the **OnSelect** property, add this formula:

```javascript
// Get selected form response
Set(varSelectedResponse, Gallery1.Selected);

// Extract form data
Set(varFormData, {
    firstName: Index(varSelectedResponse.questions, 1).answer,
    lastName: Index(varSelectedResponse.questions, 2).answer,
    emailAddress: Index(varSelectedResponse.questions, 3).answer,
    phoneNumber: Index(varSelectedResponse.questions, 4).answer,
    currentLocation: Index(varSelectedResponse.questions, 5).answer,
    yearsOfExperience: Value(Index(varSelectedResponse.questions, 6).answer),
    currentSalary: Value(Index(varSelectedResponse.questions, 7).answer),
    expectedSalary: Value(Index(varSelectedResponse.questions, 8).answer),
    linkedInUrl: Index(varSelectedResponse.questions, 9).answer,
    portfolioUrl: Index(varSelectedResponse.questions, 10).answer,
    willingToRelocate: If(Index(varSelectedResponse.questions, 11).answer = "Yes", true, false),
    availableStartDate: Index(varSelectedResponse.questions, 12).answer,
    resume_file: Index(varSelectedResponse.questions, 13).answer,
    cover_letter_file: Index(varSelectedResponse.questions, 14).answer
});

// Process file uploads
Set(varResumeFile, 
    If(Not(IsBlank(varFormData.resume_file)),
        "data:application/pdf;base64," & EncodeUrl(varFormData.resume_file),
        ""
    )
);

Set(varCoverLetterFile, 
    If(Not(IsBlank(varFormData.cover_letter_file)),
        "data:application/pdf;base64," & EncodeUrl(varFormData.cover_letter_file),
        ""
    )
);

// Prepare API payload
Set(varAPIPayload, {
    firstName: varFormData.firstName,
    lastName: varFormData.lastName,
    emailAddress: varFormData.emailAddress,
    phoneNumber: varFormData.phoneNumber,
    currentLocation: varFormData.currentLocation,
    yearsOfExperience: varFormData.yearsOfExperience,
    currentSalary: varFormData.currentSalary,
    expectedSalary: varFormData.expectedSalary,
    linkedInUrl: varFormData.linkedInUrl,
    portfolioUrl: varFormData.portfolioUrl,
    willingToRelocate: varFormData.willingToRelocate,
    availableStartDate: varFormData.availableStartDate,
    resume_file: varResumeFile,
    cover_letter_file: varCoverLetterFile
});

// Submit to DANI HRIS
Set(varAPIResponse,
    HTTP.Invoke(
        "https://your-dani-instance.com/api/recruitment/powerapps/YOUR_API_KEY/",
        "POST",
        {
            "Content-Type": "application/json"
        },
        JSON(varAPIPayload)
    )
);

// Handle response
If(varAPIResponse.responseCode = 201,
    // Success
    Notify("Application successfully submitted to DANI HRIS!", NotificationType.Success);
    
    // Mark as processed (you can store this in a collection or SharePoint list)
    Collect(ProcessedApplications, {
        ResponseId: varSelectedResponse.responseId,
        ProcessedDate: Now(),
        DANIApplicantId: varAPIResponse.responseJSON.applicant_id,
        Status: "Success"
    }),
    
    // Error
    Notify("Error submitting application: " & varAPIResponse.responseText, NotificationType.Error);
    
    // Log error
    Collect(ProcessedApplications, {
        ResponseId: varSelectedResponse.responseId,
        ProcessedDate: Now(),
        DANIApplicantId: "",
        Status: "Error: " & varAPIResponse.responseText
    })
);
```

### Step 5: Create Automated Processing with Power Automate

1. **Create Power Automate Flow**
   - Go to [https://flow.microsoft.com](https://flow.microsoft.com)
   - Click **"Create"** → **"Automated cloud flow"**
   - Name: "Auto-Process Form to DANI"
   - Trigger: **"When a new response is submitted (Microsoft Forms)"**

2. **Configure Form Trigger**
   - Select your Microsoft Form
   - Click **"New step"**

3. **Get Response Details**
   - Add action: **"Get response details (Microsoft Forms)"**
   - Form Id: Select your form
   - Response Id: Select from dynamic content

4. **Process File Uploads**
   - Add action: **"Get file content (OneDrive for Business)"**
   - File: Select resume upload from dynamic content
   - Convert to Base64: Yes
   - Rename to: "Get Resume Content"

   - Add action: **"Get file content (OneDrive for Business)"**
   - File: Select cover letter upload from dynamic content
   - Convert to Base64: Yes
   - Rename to: "Get Cover Letter Content"

5. **Prepare Data for DANI**
   - Add action: **"Compose (Data Operation)"**
   - Inputs: 
   ```json
   {
     "firstName": "@{outputs('Get_response_details')?['body/r1']}",
     "lastName": "@{outputs('Get_response_details')?['body/r2']}",
     "emailAddress": "@{outputs('Get_response_details')?['body/r3']}",
     "phoneNumber": "@{outputs('Get_response_details')?['body/r4']}",
     "currentLocation": "@{outputs('Get_response_details')?['body/r5']}",
     "yearsOfExperience": "@{int(outputs('Get_response_details')?['body/r6'])}",
     "currentSalary": "@{int(outputs('Get_response_details')?['body/r7'])}",
     "expectedSalary": "@{int(outputs('Get_response_details')?['body/r8'])}",
     "linkedInUrl": "@{outputs('Get_response_details')?['body/r9']}",
     "portfolioUrl": "@{outputs('Get_response_details')?['body/r10']}",
     "willingToRelocate": "@{if(equals(outputs('Get_response_details')?['body/r11'], 'Yes'), true, false)}",
     "availableStartDate": "@{outputs('Get_response_details')?['body/r12']}",
     "resume_file": "@{concat('data:application/pdf;base64,', outputs('Get_Resume_Content')?['body'])}",
     "cover_letter_file": "@{if(empty(outputs('Get_Cover_Letter_Content')?['body']), '', concat('data:application/pdf;base64,', outputs('Get_Cover_Letter_Content')?['body']))}"
   }
   ```

6. **Submit to DANI HRIS**
   - Add action: **"HTTP"**
   - Method: **POST**
   - URI: `https://your-dani-instance.com/api/recruitment/powerapps/YOUR_API_KEY/`
   - Headers:
   ```json
   {
     "Content-Type": "application/json"
   }
   ```
   - Body: Select output from Compose action

7. **Handle Success/Error**
   - Add action: **"Condition"**
   - Condition: `@{outputs('HTTP')?['statusCode']}` equals `201`
   
   **If Yes (Success):**
   - Add action: **"Send an email (Office 365 Outlook)"**
   - To: HR team email
   - Subject: `New Application Processed: @{outputs('Get_response_details')?['body/r1']} @{outputs('Get_response_details')?['body/r2']}`
   - Body: 
   ```
   A new job application has been automatically processed and added to DANI HRIS.
   
   Applicant: @{outputs('Get_response_details')?['body/r1']} @{outputs('Get_response_details')?['body/r2']}
   Email: @{outputs('Get_response_details')?['body/r3']}
   Phone: @{outputs('Get_response_details')?['body/r4']}
   DANI Applicant ID: @{outputs('HTTP')?['body']?['applicant_id']}
   
   Please review the application in DANI HRIS.
   ```
   
   **If No (Error):**
   - Add action: **"Send an email (Office 365 Outlook)"**
   - To: IT/Admin email
   - Subject: `Error Processing Application: @{outputs('Get_response_details')?['body/r1']} @{outputs('Get_response_details')?['body/r2']}`
   - Body:
   ```
   An error occurred while processing a job application.
   
   Applicant: @{outputs('Get_response_details')?['body/r1']} @{outputs('Get_response_details')?['body/r2']}
   Email: @{outputs('Get_response_details')?['body/r3']}
   Error: @{outputs('HTTP')?['body']?['error']}
   
   Please manually process this application.
   ```

8. **Save and Test Flow**
   - Click **"Save"**
   - Test with a sample form submission

---

## Part 3: Testing the Complete Integration

### Step 6: End-to-End Test

1. **Submit Test Application**
   - Fill out your Microsoft Form completely
   - Include test files for resume and cover letter
   - Submit the form

2. **Verify Power Automate Execution**
   - Go to [https://flow.microsoft.com](https://flow.microsoft.com)
   - Check your flow's run history
   - Verify all steps completed successfully

3. **Check DANI HRIS**
   - Login to DANI HRIS admin
   - Navigate to **Recruitment** → **Applicants**
   - Verify new applicant record was created
   - Check that all fields are populated correctly
   - Verify file uploads are present

4. **Verify Email Notifications**
   - Check for success email to HR team
   - Verify applicant received confirmation email

### Step 7: Troubleshooting Common Issues

1. **Form Response Mapping Issues**
   - **Problem**: Fields not mapping correctly
   - **Solution**: Check question order in Microsoft Forms
   - **Fix**: Update the `r1`, `r2`, etc. references in Power Automate

2. **File Upload Failures**
   - **Problem**: Files not uploading to DANI
   - **Solution**: Check file size and format
   - **Fix**: Ensure base64 encoding is working properly

3. **API Authentication Errors**
   - **Problem**: 401 Unauthorized errors
   - **Solution**: Verify API key is correct
   - **Fix**: Check PowerApps configuration in DANI admin

4. **CORS Errors**
   - **Problem**: Cross-origin request blocked
   - **Solution**: Update allowed origins in DANI configuration
   - **Fix**: Add Power Automate IP ranges to CORS settings

---

## Part 4: Advanced Configuration

### Step 8: Add Real-time Status Updates

1. **Create SharePoint List for Tracking**
   - Create SharePoint list: "Application Processing Status"
   - Columns:
     - ResponseId (Single line of text)
     - ApplicantName (Single line of text)
     - ProcessingStatus (Choice: Pending, Processing, Success, Error)
     - DANIApplicantId (Number)
     - ProcessedDate (Date and Time)
     - ErrorMessage (Multiple lines of text)

2. **Update Power Automate Flow**
   - Add action after form submission: **"Create item (SharePoint)"**
   - Set ProcessingStatus to "Pending"
   - Update status to "Processing" before DANI submission
   - Update status to "Success" or "Error" after DANI response

3. **Add Status Dashboard to PowerApps**
   - Add SharePoint list as data source
   - Create gallery showing processing status
   - Add refresh button to check latest status

### Step 9: Error Handling and Retry Logic

1. **Add Try-Catch in Power Automate**
   - Configure scope actions for error handling
   - Add retry policies for API calls
   - Implement exponential backoff for failures

2. **Create Error Notification System**
   - Set up Teams channel for error notifications
   - Configure email alerts for critical failures
   - Add webhook notifications for real-time monitoring

---

## Part 5: Monitoring and Maintenance

### Step 10: Set Up Monitoring

1. **Power Automate Analytics**
   - Monitor flow run history
   - Set up failure alerts
   - Track processing times

2. **DANI HRIS Monitoring**
   - Check PowerApps configuration statistics
   - Monitor API usage and success rates
   - Review error logs regularly

3. **Performance Optimization**
   - Optimize file upload sizes
   - Implement caching where appropriate
   - Monitor API response times

### Step 11: Regular Maintenance Tasks

1. **Weekly**
   - Review failed form submissions
   - Check error logs
   - Verify email notifications working

2. **Monthly**
   - Update API keys if needed
   - Review and update field mappings
   - Analyze processing statistics

3. **Quarterly**
   - Security audit of connections
   - Performance review and optimization
   - Update documentation

---

## Connection Summary

**Flow**: Microsoft Forms → Power Automate → DANI HRIS API

**Key Connection Points**:
1. **Forms → Power Automate**: Form submission trigger
2. **Power Automate → DANI**: HTTP POST to PowerApps API endpoint
3. **DANI Response → Power Automate**: Success/error handling
4. **Power Automate → Notifications**: Email/Teams notifications

**Files Needed**:
- Microsoft Form ID
- DANI API Key
- DANI API Endpoint URL
- Power Automate Flow
- PowerApps Dashboard (optional)

This completes the step-by-step connection guide for Microsoft Forms → PowerApps → DANI HRIS integration.