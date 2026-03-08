#!/usr/bin/env python3
"""
Gmail OAuth Token Generator for aLiGN Briefing Auto-Fetch

Run this script ONCE to generate a refresh token for Gmail API access.

Prerequisites:
1. Go to https://console.cloud.google.com/apis/credentials
2. Create a project (e.g., "align-gmail-fetch")
3. Enable Gmail API
4. Create OAuth 2.0 Client ID → Desktop app → Download as client_secret.json
5. Place client_secret.json in the same directory as this script

Usage:
    python generate_gmail_token.py

The script will:
- Open your browser for OAuth consent
- Save credentials to token.pickle
- Print your GOOGLE_REFRESH_TOKEN (copy to .env)
"""

import os
import pickle
import sys

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
except ImportError:
    print("❌ Error: Missing required packages")
    print("\nInstall them with:")
    print("  pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    sys.exit(1)


SCOPES = ['https://www.googleapis.com/auth/gmail.modify']


def main():
    """Generate Gmail OAuth refresh token."""
    creds = None
    
    print("\n" + "="*70)
    print("Gmail OAuth Token Generator for aLiGN Briefing Auto-Fetch")
    print("="*70 + "\n")
    
    # Check for client_secret.json
    if not os.path.exists('client_secret.json'):
        print("❌ Error: client_secret.json not found")
        print("\n📋 Setup steps:")
        print("  1. Go to https://console.cloud.google.com/apis/credentials")
        print("  2. Create project → Enable Gmail API")
        print("  3. Create OAuth 2.0 Client ID → Desktop app")
        print("  4. Download JSON and save as 'client_secret.json'")
        print("  5. Place it in the same directory as this script")
        print("  6. Run this script again\n")
        sys.exit(1)
    
    print("📄 Found client_secret.json\n")
    
    # If token.pickle exists, load it
    if os.path.exists('token.pickle'):
        print("📦 Loading existing token.pickle...")
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If no valid creds, let user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing expired token...")
            creds.refresh(Request())
        else:
            print("🌐 Opening browser for OAuth consent...")
            print("👉 Log in with the Gmail account that receives briefing emails")
            print("👉 Grant access to Gmail (allows reading and marking as read)\n")
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
        print("\n💾 Saved credentials to token.pickle")
    
    # Test the connection
    print("\n🧪 Testing Gmail API connection...")
    try:
        service = build('gmail', 'v1', credentials=creds)
        profile = service.users().getProfile(userId='me').execute()
        print(f"✅ Connected to: {profile.get('emailAddress')}")
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        sys.exit(1)
    
    # Print the credentials to add to .env
    print("\n" + "="*70)
    print("✅ SUCCESS! Copy these to your aLiGN/.env file:")
    print("="*70 + "\n")
    print(f"GOOGLE_CLIENT_ID={creds.client_id}")
    print(f"GOOGLE_REFRESH_TOKEN={creds.refresh_token}")
    print("\n" + "="*70)
    print("\n⚠️  SECURITY NOTES:")
    print("  • Keep these credentials SECRET")
    print("  • Never commit client_secret.json or token.pickle to git")
    print("  • Refresh token grants access to your Gmail")
    print("  • .env is already in .gitignore (safe)")
    print("\n✅ NEXT STEPS:")
    print("  1. Copy the GOOGLE_CLIENT_ID and GOOGLE_REFRESH_TOKEN values above")
    print("  2. Copy GOOGLE_CLIENT_SECRET from your client_secret.json file")
    print("  3. Paste all 3 values into backend/.env (or aLiGN/.env)")
    print("  4. Restart your backend: docker-compose restart backend")
    print("  5. Test: POST http://localhost:8000/api/v1/briefing/ingest/test")
    print("\n" + "="*70 + "\n")


if __name__ == '__main__':
    main()
