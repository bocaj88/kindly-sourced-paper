# Gmail API Setup Guide

## Overview
This script allows you to send emails and SMS messages using the Gmail API. It can automatically detect phone carriers and send SMS via email-to-SMS gateways.

## Prerequisites
- Python 3.6+
- Google account with Gmail
- Google Cloud Console access

## Setup Instructions

### 1. Google Cloud Console Setup

1. **Go to Google Cloud Console**: https://console.cloud.google.com/
2. **Create or select a project**
3. **Enable the Gmail API**:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Gmail API"
   - Click on it and press "Enable"

### 2. Create OAuth 2.0 Credentials

1. **Go to Credentials**: APIs & Services > Credentials
2. **Create Credentials** > OAuth 2.0 Client IDs
3. **Configure OAuth consent screen** (if prompted):
   - Choose "External" for testing
   - Fill in required fields (App name, User support email, Developer contact)
   - Add your email to test users
4. **Create OAuth 2.0 Client ID**:
   - Application type: "Desktop application"
   - Name: "Gmail API Client" (or any name you prefer)
5. **Download the JSON file**:
   - Click the download button next to your created credential
   - Rename the downloaded file to `credentials.json`
   - Place it in the same directory as `gmail.py`

### 3. Install Required Dependencies

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client requests
```

Or if you have a requirements.txt file:
```bash
pip install -r requirements.txt
```

### 4. First Run Authentication

1. Run the script for the first time:
   ```bash
   python gmail.py
   ```

2. **Browser Authentication**:
   - A browser window will open
   - Sign in to your Google account
   - Grant permissions to the application
   - You'll see a "The authentication flow has completed" message

3. **Token Storage**:
   - A `token.json` file will be created automatically
   - This stores your authentication tokens for future use
   - Keep this file secure and don't share it

## Usage Examples

### Basic Usage

```python
from gmail import CommObj, send_message, gmail_authenticate

# Initialize communication object
com = CommObj("recipient@example.com", subject="Test Email")
com.send("Hello, this is a test message!")

# Send SMS (automatically detects carrier)
sms_com = CommObj("7165252886")  # Phone number
sms_com.send("Hello via SMS!")

# Send to different addresses
com.sendTo("another@example.com", "Different message", "Different Subject")
```

### Advanced Usage

```python
# Direct service usage
service = gmail_authenticate()
send_message(service, "recipient@example.com", "Subject", "Body text")

# With attachments
send_message(service, "recipient@example.com", "Subject", "Body", ["file1.txt", "file2.pdf"])
```

## Features

- ✅ **Email sending** via Gmail API
- ✅ **SMS sending** via email-to-SMS gateways
- ✅ **Automatic carrier detection** for SMS
- ✅ **Attachment support**
- ✅ **OAuth 2.0 authentication**
- ✅ **Token refresh** handling
- ✅ **Error handling** and logging

## Supported SMS Carriers

- AT&T (`@mms.att.net`)
- T-Mobile (`@tmomail.net`)
- Verizon (`@vtext.com`)
- Sprint (`@page.nextel.com`)
- Omnipoint (`@messaging.sprintpcs.com`)

## Troubleshooting

### Error: "credentials.json file not found"
- Make sure you downloaded and renamed the OAuth 2.0 client credentials file
- Place it in the same directory as the script

### Error: "Token has been expired or revoked"
- Delete the `token.json` file
- Run the script again to re-authenticate

### SMS not working
- Verify the phone number format (US numbers only currently supported)
- Check if the carrier is supported
- Some carriers may block email-to-SMS messages

### Authentication flow issues
- Make sure your email is added to test users in OAuth consent screen
- Try using an incognito/private browser window
- Check that Gmail API is enabled in your Google Cloud project

## Security Notes

- **Never commit `credentials.json` or `token.json` to version control**
- Keep your OAuth 2.0 credentials secure
- The script no longer contains hardcoded passwords (security improvement)
- Consider using environment variables for sensitive configuration

## File Structure

```
your-project/
├── gmail.py                 # Main script
├── credentials.json         # OAuth 2.0 credentials (you create this)
├── token.json              # Auto-generated auth tokens
└── README_gmail_setup.md   # This setup guide
```

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Verify all setup steps were completed
3. Check Google Cloud Console for API quotas and limits
4. Review the error messages for specific guidance 