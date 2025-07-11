import os
import json
import re
import time
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import joblib

# Load ML model and vectorizer
model = joblib.load("spam_classifier.pkl")
vectorizer = joblib.load("vectorizer.pkl")

# Gmail auth scope
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Path to store logs
log_path = "classified_emails.json"

# Keep track of last processed email
last_message_id = None

def classify_email(text):
    features = vectorizer.transform([text])
    prediction = model.predict(features)
    return "HAM" if prediction[0] == 1 else "SPAM"

def gmail_authenticate():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

def append_to_json(data, path):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(data) + "\n")  # one JSON per line

def fetch_emails():
    global last_message_id

    service = gmail_authenticate()
    results = service.users().messages().list(userId='me', maxResults=10).execute()
    messages = results.get('messages', [])

    new_messages = []

    for msg in messages:
        if msg['id'] == last_message_id:
            break  # Stop if we reach the last seen message
        new_messages.append(msg)

    if not new_messages:
        print("No new emails.")
        return

    # Update last seen message ID
    last_message_id = messages[0]['id']

    for msg in reversed(new_messages):  # Process oldest first
        msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()
        headers = msg_data['payload']['headers']

        # Initialize header map
        header_map = {
            'h.from': '',
            'From': '',
            'Subject': '',
            'Delivered-To': '',
            'Cc': '',
            'Date': '',
            'Message-ID': '',
            'In-Reply-To': '',
            'References': '',
            'MIME-Version': '',
            'Content-Type': '',
            'X-Received': '',
            'ARC-Message-Signature': '',
            'ARC-Authentication-Results': '',
            'Return-Path': '',
            'Authentication-Results': '',
            'DKIM-Signature': '',
            'List-Unsubscribe': '',
            'Reply-To': '',
            'X-SFMC-Stack': '',
            'Feedback-ID': '',
            'Received-SPF': '',
            'Received': '',
            'X-Google-DKIM-Signature': '',
            'smtp_mailfrom': '',
            'header_from': ''
        }

        for h in headers:
            name = h.get('name')
            value = h.get('value')
            if name in header_map:
                header_map[name] = value

        # Extract smtp.mailfrom and header.from from ARC-Authentication-Results
        arc_auth = header_map.get('ARC-Authentication-Results', '')

        smtp_mailfrom_match = re.search(r'smtp\.mailfrom=([^\s;]+)', arc_auth)
        if smtp_mailfrom_match:
            header_map['smtp_mailfrom'] = smtp_mailfrom_match.group(1)

        header_from_match = re.search(r'header\.from=([^\s;]+)', arc_auth)
        if header_from_match:
            header_map['header_from'] = header_from_match.group(1)

        snippet = msg_data.get("snippet", "")
        classification = classify_email(snippet)

        print(f"From: {header_map['From']}")
        print(f"Subject: {header_map['Subject']}")
        print(f"Classification: {classification}")
        print("-" * 50)

        data = {
            "timestamp": datetime.utcnow().isoformat(),
            "from": header_map['From'],
            "subject": header_map['Subject'],
            "to": header_map['Delivered-To'],
            "cc": header_map['Cc'],
            "X-Google-DKIM-Signature": header_map['X-Google-DKIM-Signature'],
            "date_sent": header_map['Date'],
            "message_id": header_map['Message-ID'],
            "in_reply_to": header_map['In-Reply-To'],
            "references": header_map['References'],
            "mime_version": header_map['MIME-Version'],
            "content_type": header_map['Content-Type'],
            "x_received": header_map['X-Received'],
            "arc_message_signature": header_map['ARC-Message-Signature'],
            "arc_authentication_results": header_map['ARC-Authentication-Results'],
            "return_path": header_map['Return-Path'],
            "authentication_results": header_map['Authentication-Results'],
            "dkim_signature": header_map['DKIM-Signature'],
            "list_unsubscribe": header_map['List-Unsubscribe'],
            "reply_to": header_map['Reply-To'],
            "x_sfmc_stack": header_map['X-SFMC-Stack'],
            "feedback_id": header_map['Feedback-ID'],
            "received_spf": header_map['Received-SPF'],
            "received": header_map['Received'],
            "smtp_mailfrom": header_map['smtp_mailfrom'],
            "header_from": header_map['header_from'],
            "snippet": snippet,
            "classification": classification
        }

        append_to_json(data, log_path)

def Real_Time():
    while True:
        fetch_emails()
        time.sleep(30)  # Check every 30 seconds

# Start real-time fetch loop
Real_Time()
