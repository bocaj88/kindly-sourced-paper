# Author: Jake Michalski
# Date: 9/19/2021
# Project Name: Communication
# Description: Send SMS or Email!
# Requirements: Enable Gmail API
# https://developers.google.com/gmail/api/quickstart/python - Setup Service
# https://www.thepythoncode.com/article/use-gmail-api-in-python - Send Email

import requests
import json
import sys
import smtplib
from email.message import EmailMessage
import time

import os.path
from googleapiclient.discovery import build             # google-api-python-client
from google_auth_oauthlib.flow import InstalledAppFlow  #  google-auth-httplib2 google-auth-oauthlib
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

import os
import re
import pickle
# Gmail API utils
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
# for encoding/decoding messages in base64
from base64 import urlsafe_b64decode, urlsafe_b64encode
# for dealing with attachement MIME types
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from mimetypes import guess_type as guess_mime_type


# https://avtech.com/articles/138/list-of-email-to-sms-addresses/
carriers = {
    'att':          '@mms.att.net',
    'tmobile':      '@tmomail.net',
    'verizon':      '@vtext.com',
    'sprint':       '@page.nextel.com',
    'omnipoint':    '@messaging.sprintpcs.com'
}

# Request all access (permission to read/send/receive emails, manage the inbox, and more)
SCOPES = ['https://mail.google.com/']

class CommObj:
    def __init__(self, address, subject=None):
        self.address = address
        self.subject = subject
        self.service = gmail_authenticate()
        self.our_email = self._get_our_email()

    def _get_our_email(self):
        """Get the authenticated user's email address"""
        if self.service:
            try:
                profile = self.service.users().getProfile(userId='me').execute()
                return profile.get('emailAddress', 'unknown@gmail.com')
            except Exception as e:
                print(f"Could not get user email: {e}")
                return 'unknown@gmail.com'
        return None

    def send(self, message, attachments=[]):
        if not self.service:
            print("Gmail service not available. Cannot send message.")
            return False
            
        if self.subject:
            return send_message(self.service, self.address, self.subject, message, attachments)
        else:
            return send_message(self.service, self.address, "No Subject", message, attachments)

    def sendTo(self, addr, message, subject=None, attachments=[]):
        if not self.service:
            print("Gmail service not available. Cannot send message.")
            return False
            
        try:
            return send_message(self.service, addr, subject or "No Subject", message, attachments)
        except KeyError as e:   # Catch the carrier not found
            print(f"Carrier error: {e}")
            self.send(str(e))
            raise e


def gmail_authenticate():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Check if credentials.json exists
            if not os.path.exists('credentials.json'):
                print("❌ ERROR: credentials.json file not found!")
                print("Please download your OAuth 2.0 credentials from Google Cloud Console:")
                print("1. Go to https://console.cloud.google.com/")
                print("2. Create a project or select existing one")
                print("3. Enable Gmail API")
                print("4. Create OAuth 2.0 credentials")
                print("5. Download as 'credentials.json' and place in this directory")
                raise FileNotFoundError("credentials.json file is required for Gmail API authentication")
            
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('gmail', 'v1', credentials=creds)
    return service


def getCarrier(number):
    """Get carrier information for a phone number"""
    number = number.strip("-")
    url = 'https://api.telnyx.com/v1/phone_number/1' + number   # Preface the 1 for USA
    try:
        html = getHTML(url)
        data = json.loads(html)
        carrier = data["carrier"]["name"]
    except (json.decoder.JSONDecodeError, KeyError, requests.RequestException):
        print(f"Could not determine carrier for {number}, defaulting to Verizon")
        carrier = "verizon"
    
    for c in carriers.keys():
        if c in carrier.lower():
            return c

    # If we don't have the carrier prefix
    errorMessage = "Unable to get carrier for " + number + "\n" + carrier + "\n"
    sys.stderr.write(errorMessage)
    raise KeyError(errorMessage)


def getHTML(url, depth=3):
    """Get HTML content from URL with retry logic"""
    if depth <= 0:
        return ""
    try:
        html = str(requests.get(url, timeout=10).text)
        if len(html.strip()) != 0:
            return html
        else:
            time.sleep(.1)
            return getHTML(url, depth=depth-1)
    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return ""


# Adds the attachment with the given filename to the given message
def add_attachment(message, filename):
    content_type, encoding = guess_mime_type(filename)
    if content_type is None or encoding is not None:
        content_type = 'application/octet-stream'
    main_type, sub_type = content_type.split('/', 1)
    if main_type == 'text':
        fp = open(filename, 'rb')
        msg = MIMEText(fp.read().decode(), _subtype=sub_type)
        fp.close()
    elif main_type == 'image':
        fp = open(filename, 'rb')
        msg = MIMEImage(fp.read(), _subtype=sub_type)
        fp.close()
    elif main_type == 'audio':
        fp = open(filename, 'rb')
        msg = MIMEAudio(fp.read(), _subtype=sub_type)
        fp.close()
    else:
        fp = open(filename, 'rb')
        msg = MIMEBase(main_type, sub_type)
        msg.set_payload(fp.read())
        fp.close()
    filename = os.path.basename(filename)
    msg.add_header('Content-Disposition', 'attachment', filename=filename)
    message.attach(msg)


def build_message(destination, obj, body, attachments=[], our_email=None):
    """Build email message with optional attachments"""
    if our_email is None:
        our_email = "unknown@gmail.com"
        
    if not attachments: # no attachments given
        message = MIMEText(body)
        message['to'] = destination
        message['from'] = our_email
        message['subject'] = obj
    else:
        message = MIMEMultipart()
        message['to'] = destination
        message['from'] = our_email
        message['subject'] = obj
        message.attach(MIMEText(body))
        for filename in attachments:
            add_attachment(message, filename)
    return {'raw': urlsafe_b64encode(message.as_bytes()).decode()}


def send_message(service, destination, obj, body, attachments=[]):
    """Send email message via Gmail API"""
    # Check if destination is a phone number and convert to SMS gateway
    destination = re.sub("[- ()]", "", destination)     # Format to a number by replacing [(,),-," "] with ""
    if destination.isdigit():
        try:
            carrier = getCarrier(destination)
            destination = destination + '{}'.format(carriers[carrier])
        except KeyError as e:
            print(f"SMS gateway error: {e}")
            return None
    
    # Get our email address
    try:
        profile = service.users().getProfile(userId='me').execute()
        our_email = profile.get('emailAddress', 'unknown@gmail.com')
    except Exception as e:
        print(f"Could not get user email: {e}")
        our_email = 'unknown@gmail.com'
    
    try:
        result = service.users().messages().send(
            userId="me",
            body=build_message(destination, obj, body, attachments, our_email)
        ).execute()
        print(f"Message sent successfully to {destination}")
        return result
    except Exception as e:
        print(f"Failed to send message: {e}")
        return None


def main():
    """Test the Gmail API functionality"""
    try:
        print("Testing Gmail API...")
        com = CommObj("7165252886")
        if com.service:
            com.send("Hi there Jake (GMAIL API)")
            com.address = "bocaj@michalski1.com"
            com.send("Email Sent (GMAIL API)")
            print("✅ Messages sent successfully!")
        else:
            print("❌ Failed to initialize Gmail service")
    except Exception as e:
        print(f"❌ Error in main: {e}")


if __name__ == '__main__':
    main()