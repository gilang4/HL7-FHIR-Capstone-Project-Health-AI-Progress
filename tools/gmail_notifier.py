# tools/gmail_notifier.py
"""
Gmail Notification Tool — Send clinical summary emails via Gmail API with OAuth 2.0.
Refactored from 07_Gmail_API_OAuth.py for Agentic AI integration.

Usage:
    from tools.gmail_notifier import send_clinical_summary_email
    
    # Send a summary for a specific patient
    send_clinical_summary_email(
        patient_data=patient_dict,
        summary_data=summary_dict,
        recipient="doctor@hospital.com"
    )
"""

# ============================================================
# 🔐 STEP 1: OAuth Setup (Run this once to get token.json)
# ============================================================
from pathlib import Path
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# ============================================================
# 📧 STEP 2: Email Sender Engine
# ============================================================
import base64
from email.message import EmailMessage
from googleapiclient.discovery import build
from pathlib import Path
import json
from datetime import datetime

# ── Constants ────────────────────────────────────────────
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# Use the directory where THIS file lives, so it works from anywhere
TOOLS_DIR = Path(__file__).parent.parent  # Go up from tools/ to project root


def setup_oauth(credentials_path: str | None = None, token_path: str | None = None) -> bool:
    """
    Run OAuth 2.0 flow to get a fresh token.json for Gmail API access.
    
    Deconstruct the OAuth 2.0 Flow:
      Concept 1: The Problem (Password Auth sucks) -> Solution (Token-based Auth)
      Concept 2: The Three Files:
        - credentials.json (The "Public Key" / Blueprint)
          Tells Google which app is asking, but doesn't have permission yet.
          Created in Gmail API Cloud console, configured with PythonEmail app,
          with users allowed to use that app... which is me!
        
        - token.json (The "Access Key" / Permission Slip)
          The actual signed permission from the user (you).
        
        - token.json refresh capability (it updates itself automatically)
    
    Args:
        credentials_path: Path to credentials.json. 
                          Default: project_root/credentials.json
        token_path: Path where token.json should be saved.
                    Default: project_root/token.json
    
    Returns:
        True if OAuth setup was successful, False otherwise
    """
    
    # ── Determine paths ────────────────────────────────────
    if credentials_path is None:
        credentials_path = TOOLS_DIR / 'credentials.json'
    else:
        credentials_path = Path(credentials_path)
    
    if token_path is None:
        token_path = TOOLS_DIR / 'token.json'
    else:
        token_path = Path(token_path)
    
    print(f"📂 Looking for credentials at: {credentials_path}")
    
    # ── Check credentials.json exists ──────────────────────
    if not credentials_path.exists():
        print(f"❌ credentials.json NOT found at {credentials_path}!")
        print("   Download it from Google Cloud Console → APIs & Services → Credentials")
        return False
    
    creds = None
    
    # ── Load existing token if available ───────────────────
    if token_path.exists():
        # Load the Token: Credentials.from_authorized_user_file(token_path, SCOPES)
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    
    # ── Refresh or create new token ────────────────────────
    # Check if the Token is Dead: if not creds or not creds.valid: ... creds.refresh(Request())
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Token exists but expired — try to refresh silently
            try:
                creds.refresh(Request())
                print("🔄 Token refreshed automatically!")
            except Exception as e:
                print(f"⚠️ Token refresh failed: {e}")
                print("   Deleting old token and re-authenticating...")
                os.remove(token_path)
                creds = None
        
        # If still no valid creds, run the full OAuth flow
        if not creds:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(credentials_path), SCOPES
            )
            creds = flow.run_local_server(port=0)
        
        # Save the token for next time
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
        print("💾 token.json saved!")
    
    print("✅ OAuth setup complete!")
    return True


def send_email(
    to: str,
    subject: str,
    body_text: str,
    token_path: str | None = None
) -> bool:
    """
    Sends an email using Gmail API with OAuth 2.0.
    
    This is like handing the keys to a Gmail agent. 
    The agent now has permission to drive (send emails).
    
    Args:
        to: Recipient email address
        subject: Email subject line
        body_text: Plain text email body
        token_path: Path to token.json. Default: project_root/token.json
    
    Returns:
        True if email was sent successfully, False otherwise
    """
    
    if token_path is None:
        token_path = TOOLS_DIR / 'token.json'
    else:
        token_path = Path(token_path)
    
    # ── Check token exists ─────────────────────────────────
    if not token_path.exists():
        print("❌ token.json not found! Run setup_oauth() first.")
        return False
    
    # ── Load credentials ───────────────────────────────────
    creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    
    # ── Refresh if expired ─────────────────────────────────
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"❌ Token refresh failed: {e}")
                print("   Run setup_oauth() to re-authenticate.")
                return False
        else:
            print("❌ Invalid credentials. Run setup_oauth() to re-authenticate.")
            return False
    
    # ── Build and send the email ───────────────────────────
    try:
        # Hand the keys to a Gmail agent. The agent now has permission to drive.
        service = build('gmail', 'v1', credentials=creds)
        message = EmailMessage()
        message.set_content(body_text)
        message['To'] = to
        message['From'] = 'me'  # 'me' = the authenticated user
        message['Subject'] = subject
        
        # Encode the message for Gmail API
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        # This tells the Gmail agent: "Send this email NOW."
        send_message = service.users().messages().send(
            userId="me",
            body={'raw': encoded_message}
        ).execute()
        
        print(f'✅ Email sent! Message Id: {send_message["id"]}')
        return True
    
    except Exception as e:
        print(f'❌ Failed to send email: {e}')
        return False


def send_clinical_summary_email(
    patient_data: dict,
    summary_data: dict,
    recipient: str,
    token_path: str | None = None,
    save_to_file: bool = False
) -> bool:
    """
    Build and send a clinical summary email using FHIR patient data and AI summary.
    
    This is STEP 3 (FHIR VERSION): Send Clinical Summary via Email.
    Combines patient_summary.json + summary_output_AzureGPT.json into a professional email.
    
    Args:
        patient_data: Dict from fhir_explorer with patient, conditions, medications, etc.
        summary_data: Dict from ollama_summarizer or azure_summarizer with summary, conditions, etc.
        recipient: Email address to send to (e.g., "doctor@hospital.com")
        token_path: Path to token.json. Default: project_root/token.json
        save_to_file: If True, saves a copy of the email body to email_output.txt
    
    Returns:
        True if email was sent successfully, False otherwise
    
    Example:
        from tools.fhir_explorer import explore_patient
        from tools.azure_summarizer import summarize_with_azure
        from tools.gmail_notifier import send_clinical_summary_email
        
        data = explore_patient()
        summary = summarize_with_azure(data)
        send_clinical_summary_email(data, summary, "doctor@hospital.com")
    """
    
    # ── Extract Patient Info ───────────────────────────────
    patient_id = patient_data.get("patient", {}).get("id", "Unknown")
    patient_name = patient_data.get("patient", {}).get("name", "Unknown")
    patient_dob = patient_data.get("patient", {}).get("dob", "Unknown")
    
    # ── Extract Clinical Summary ───────────────────────────
    clinical_summary = summary_data.get("summary", "No summary generated.")
    conditions = summary_data.get("conditions", [])
    medications = summary_data.get("medications", [])
    
    # ── Build Email Subject ────────────────────────────────
    email_subject = f"📋 Clinical Summary - Patient {patient_id} - {datetime.now().strftime('%Y-%m-%d')}"
    
    # ── Build Email Body ───────────────────────────────────
    email_body = f"""
CLINICAL SUMMARY REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

👤 PATIENT INFORMATION:
- Patient ID: {patient_id}
- Name: {patient_name}
- DOB: {patient_dob}

🏥 CONDITIONS ({len(conditions)}):
{chr(10).join(['- ' + str(c) for c in conditions])}

💊 MEDICATIONS ({len(medications)}):
{chr(10).join(['- ' + str(m) for m in medications])}

📄 AI-GENERATED CLINICAL SUMMARY:
{clinical_summary}

---
This report was generated automatically by your AI-powered Clinical Summarizer Pipeline.
FHIR DocumentReference POST: ✅ Confirmed
"""
    
    # ── Optional: Save email body to file ──────────────────
    if save_to_file:
        output_path = TOOLS_DIR / f"email_output_{patient_id}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(email_body)
        print(f"📄 Email body saved to {output_path}")
    
    # ── Send the Email ─────────────────────────────────────
    return send_email(recipient, email_subject, email_body, token_path=token_path)


# ============================================================
# 🚀 STANDALONE RUNNER (Backward Compatible!)
# ============================================================
if __name__ == "__main__":
    print("=" * 50)
    print("📧 Gmail Notification Tool — Standalone Mode")
    print("=" * 50)
    
    # ── Step 1: Ensure OAuth is set up ─────────────────────
    print("\n🔐 Setting up OAuth...")
    if not setup_oauth():
        print("❌ OAuth setup failed. Exiting.")
        exit(1)
    
    # ── Step 2: Load FHIR data ─────────────────────────────
    print("\n📂 Loading patient data...")
    patient_json_path = TOOLS_DIR / "patient_summary.json"
    summary_json_path = TOOLS_DIR / "summary_output_AzureGPT.json"
    
    if not patient_json_path.exists():
        print(f"❌ patient_summary.json not found at {patient_json_path}")
        exit(1)
    if not summary_json_path.exists():
        print(f"❌ summary_output_AzureGPT.json not found at {summary_json_path}")
        print("   Run 05_azure_summarizer.py first to generate a summary.")
        exit(1)
    
    with open(patient_json_path, "r") as f:
        patient_data = json.load(f)
    
    with open(summary_json_path, "r") as f:
        summary_data = json.load(f)
    
    # ── Step 3: Send the email ─────────────────────────────
    print("\n📧 Sending clinical summary email...")
    RECIPIENT_EMAIL = "gilang4@yahoo.com"  # Change to your target recipient
    
    success = send_clinical_summary_email(
        patient_data=patient_data,
        summary_data=summary_data,
        recipient=RECIPIENT_EMAIL,
        save_to_file=True  # Save a copy of the email body
    )
    
    if success:
        print("\n📧 Clinical summary email sent successfully!")
    else:
        print("\n❌ Failed to send email. Check the errors above.")
    
    print("\n✅ Standalone run complete!")