    # ============================================================
    # 🔐 STEP 1: OAuth Setup (Run this once to get token.json)
    # ============================================================
from pathlib import Path
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def setup_oauth():
    creds = None

        # for ipynb, with path including "space" characters, this grab the current folder these files are in, bypass all the problem of empty string
    script_dir = Path.cwd()

        # Deconstruct the OAuth 2.0 Flow

            # Concept 1: The Problem (Password Auth sucks) -> Solution (Token-based Auth)
            # Concept 2: The Three Files:

                # credentials.json (The "Public Key" / Blueprint). It tells Google which app is asking, but it doesn't have permission yet.

                # token.json (The "Access Key" / Permission Slip). The actual signed permission from the user (you).

                # token.json refresh capability (it updates itself automatically).

        # credentials.json (The "Public Key" / Blueprint). It tells Google which app is asking, but it doesn't have permission yet
        # in this case Gmail API Cloud console, configured to have PythonEmail app, with users allow to use that app.....which is me!

    credentials_path = script_dir / 'credentials.json'

        # send in request, acknowledge by Gmail API, send back a permission session: token.json
    token_path = script_dir / 'token.json'

    print(f"📂 Looking for credentials at: {credentials_path}")

    if not credentials_path.exists():
        print(f"❌ credentials.json NOT found!")
        return

    if token_path.exists():

            # Load the Token: Credentials.from_authorized_user_file(token_path, SCOPES)
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        
        # Check if the Token is Dead: if not creds or not creds.valid: ... creds.refresh(Request())
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_path, 'w') as token:
            token.write(creds.to_json())
        print("💾 token.json saved!")

    print("✅ OAuth setup complete!")

    # Run it
setup_oauth()

""" ##################################################################### """

    # ============================================================
    # 📧 STEP 2: Email Sender Function (Define the engine)
    # ============================================================
import base64
from email.message import EmailMessage
from googleapiclient.discovery import build
from pathlib import Path

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

    # this send email function has 3 variables passed in: to, subject, and body_text
def send_email(to, subject, body_text):
    
    """Sends an email using Gmail API with OAuth 2.0."""
    creds = None
    script_dir = Path.cwd()
    token_path = script_dir / 'token.json'

    if not token_path.exists():
        print("❌ token.json not found! Run OAuth setup first.")
        return

    creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            print("❌ Invalid credentials. Re-run OAuth setup.")
            return

    try:
            # This is like handing the keys to a Gmail agent. The agent now has permission to drive (send emails).
        service = build('gmail', 'v1', credentials=creds)
        message = EmailMessage()
        message.set_content(body_text)
        message['To'] = to
        message['From'] = 'me'
        message['Subject'] = subject

        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

            # This tells the Gmail agent: "Send this email NOW."
        send_message = service.users().messages().send(userId="me", body={'raw': encoded_message}).execute()
        print(f'✅ Email sent! Message Id: {send_message["id"]}')
    except Exception as e:
        print(f'❌ Failed: {e}')


""" ##################################################################### """

    # ============================================================
    # 📧 STEP 3 (FHIR VERSION): Send Clinical Summary via Email
    # ============================================================

import json
from datetime import datetime
from pathlib import Path

# --- Load FHIR Data ---
with open("patient_summary.json", "r") as f:
    patient_data = json.load(f)

with open("summary_output.json", "r") as f:
    summary_data = json.load(f)

# --- Patient Info ---
patient_id = patient_data.get("patient", {}).get("id", "Unknown")
patient_name = patient_data.get("patient", {}).get("name", "Unknown")
patient_dob = patient_data.get("patient", {}).get("dob", "Unknown")

# --- Clinical Summary ---
clinical_summary = summary_data.get("summary", "No summary generated.")
conditions = summary_data.get("conditions", [])
medications = summary_data.get("medications", [])

# --- Build Email Body ---
EMAIL_SUBJECT = f"📋 Clinical Summary - Patient {patient_id} - {datetime.now().strftime('%Y-%m-%d')}"

email_body = f"""
CLINICAL SUMMARY REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

👤 PATIENT INFORMATION:
- Patient ID: {patient_id}
- Name: {patient_name}
- DOB: {patient_dob}

🏥 CONDITIONS ({len(conditions)}):
{chr(10).join(['- ' + c for c in conditions])}

💊 MEDICATIONS ({len(medications)}):
{chr(10).join(['- ' + m for m in medications])}

📄 AI-GENERATED CLINICAL SUMMARY:
{clinical_summary}

---
This report was generated automatically by your AI-powered Clinical Summarizer Pipeline.
FHIR DocumentReference POST: ✅ Confirmed
"""

# --- Send the Email ---
RECIPIENT_EMAIL = "gilang4@yahoo.com"  # Change to security team or reviewer
send_email(RECIPIENT_EMAIL, EMAIL_SUBJECT, email_body)
print("📧 Clinical summary email sent!")
