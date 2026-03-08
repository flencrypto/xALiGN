# Gmail OAuth & Fallback Notifications Setup

This guide shows you how to set up Gmail OAuth for auto-fetching daily briefing emails and configure fallback notifications when briefings are missing.

---

## 📋 Prerequisites

1. **Google Cloud Project** with Gmail API enabled
2. **OAuth 2.0 credentials** (Desktop app type)
3. **client_secret.json** file (already in `backend/client_secret.json`)
4. Python 3.11+ with required packages installed

---

## 🔑 Step 1: Generate Gmail OAuth Token

The `client_secret.json` file is already in place. Now generate your refresh token:

```bash
cd backend
python scripts/generate_gmail_token.py
```

**What happens:**
1. Opens browser for Google account login
2. Requests Gmail permissions (read/modify)
3. Saves `token.pickle` with refresh token
4. Prints credentials for `.env` file

**Expected output:**
```
Add these to your .env file:
GOOGLE_CLIENT_ID=YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=YOUR_GOOGLE_CLIENT_SECRET
GOOGLE_REFRESH_TOKEN=1//0g...your_refresh_token_here
```

---

## ⚙️ Step 2: Update Environment Variables

Add the credentials to your `.env` file:

```env
# Gmail Integration
GOOGLE_CLIENT_ID=YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=YOUR_GOOGLE_CLIENT_SECRET
GOOGLE_REFRESH_TOKEN=1//0g...your_refresh_token_here
BRIEFING_EMAIL_SUBJECT=GLOBAL DATA CENTRE INTELLIGENCE BRIEFING

# Fallback Notifications
NOTIFICATION_EMAIL=your-email@example.com
X_HANDLE=TheMrFlen
```

---

## 🔔 Step 3: Configure Fallback Notifications

When the daily briefing email is **not found** or **fetch fails**, the system can:

✅ **Create X (Twitter) DM draft** - Notifies you via social media  
✅ **Create Gmail draft email** - Sends backup notification  
✅ **Log detailed warnings** - Visible in scheduler logs

### Default Behavior (Safe Mode)

By default, the system creates **drafts only** - no auto-posting:

```python
permissions = {
    "social_draft": True,      # Creates X draft (safe)
    "gmail_draft": True,       # Creates email draft (safe)
    "full_autopilot": False,   # No auto-send (safe)
}
```

### Fallback Message Templates

**X DM Draft:**
```
@TheMrFlen Daily DC briefing email missing today (2026-03-07). 
No new intel pulled – check inbox or manual upload? #alignapp
```

**Email Draft:**
```
Subject: aLiGN Daily Briefing Missing - 2026-03-07

Ben,

No new GLOBAL DATA CENTRE INTELLIGENCE BRIEFING email found today (2026-03-07).

The automated ingestion task ran but skipped processing.

Possible actions:
• Check inbox for the briefing email
• Check spam/junk folders
• Run manual upload if needed
• Verify Gmail OAuth token is still valid

GHOST 👻
```

---

## 🧪 Step 4: Test the Setup

### Test 1: Manual Fetch

```bash
# In Python console or script
from backend.services.gmail_utils import fetch_latest_briefing_from_gmail
import asyncio

briefing = asyncio.run(fetch_latest_briefing_from_gmail())
print(f"Found: {len(briefing) if briefing else 0} characters")
```

**Expected:** Prints briefing text length or "No new briefing email found"

### Test 2: Fallback Notifications

```bash
# Temporarily disable Gmail fetch to test fallback
from backend.services.notification_utils import send_fallback_notifications
import asyncio

result = asyncio.run(send_fallback_notifications("2026-03-07"))
print(result)
```

**Expected output:**
```json
{
  "briefing_date": "2026-03-07",
  "notifications_sent": [
    {"type": "x_draft", "status": "success", "draft_id": "draft_x_1234567890"},
    {"type": "gmail_draft", "status": "success", "draft_id": "r-1234567890"}
  ],
  "errors": []
}
```

### Test 3: Full Ingestion Workflow

```bash
from backend.services.briefing_ingestion import run_daily_briefing_ingestion
import asyncio

result = asyncio.run(run_daily_briefing_ingestion())
print(result)
```

**Expected:** Full briefing parse + ingestion, or fallback notifications if no email found

---

## 📅 Step 5: Enable Daily Scheduler

The scheduler runs at **07:30 UTC** daily (configured in `main.py`):

```python
scheduler.add_job(
    run_daily_briefing_ingestion,
    trigger='cron',
    hour=7,
    minute=30,
    timezone='UTC',
    id='daily_briefing_ingestion'
)
```

**To adjust schedule:**
- Edit `hour` and `minute` parameters
- Change `timezone` (e.g., `Europe/London`, `America/New_York`)
- Restart backend server

---

## 🛡️ Security & Permissions

### File Permissions (Already Configured)

The following files are **excluded from Git** (via `.gitignore`):
- `client_secret.json` - OAuth app credentials
- `token.pickle` - Refresh token storage
- `gmail_credentials.json` - Legacy credentials

**⚠️ NEVER commit these files to Git!**

### Gmail API Scopes

The integration requests:
- `https://www.googleapis.com/auth/gmail.modify` - Read, send, delete emails

This allows the system to:
- Search for unread briefing emails
- Mark emails as read after fetch
- Create draft emails for fallback notifications

---

## 🔧 Troubleshooting

### Issue: "Gmail OAuth credentials not configured"

**Cause:** Missing environment variables  
**Fix:** Run `generate_gmail_token.py` and add credentials to `.env`

### Issue: "No new briefing email found"

**Possible causes:**
1. Briefing email not sent yet
2. Email subject doesn't match `BRIEFING_EMAIL_SUBJECT`
3. Email already marked as read (modify query to remove `is:unread`)
4. Email older than 7 days (increase `newer_than` limit)

**Fix:** Check Gmail manually or adjust search query in `gmail_utils.py`

### Issue: Token expired or invalid

**Symptoms:**
```
googleapiclient.errors.HttpError: 401 Invalid Credentials
```

**Fix:** Regenerate token:
```bash
rm backend/token.pickle
python backend/scripts/generate_gmail_token.py
```

Update `GOOGLE_REFRESH_TOKEN` in `.env` with new value

### Issue: Fallback notifications not sent

**Check logs for:**
- `"Fallback X draft created for @TheMrFlen"` → X draft success
- `"Fallback email draft created to..."` → Email draft success
- `"No notification email configured"` → Set `NOTIFICATION_EMAIL` in `.env`

**Verify permissions:**
```python
from backend.services.notification_utils import get_user_settings
import asyncio

settings = asyncio.run(get_user_settings())
print(settings["permissions"])  # Should show social_draft=True, gmail_draft=True
```

---

## 🚀 Production Recommendations

1. **Set up monitoring** - Alert on repeated fallback notifications (indicates briefing delivery issues)
2. **Review drafts regularly** - Check X and Gmail drafts for false alarms
3. **Rotate OAuth tokens** - Consider regenerating tokens every 6-12 months
4. **Enable audit logging** - Track when briefings are fetched vs. when fallbacks trigger
5. **Test disaster recovery** - Simulate Gmail API downtime to verify fallback behavior

---

## 📚 Related Files

- `backend/services/gmail_utils.py` - Gmail OAuth & fetch logic
- `backend/services/notification_utils.py` - Fallback notification system
- `backend/services/briefing_ingestion.py` - Daily orchestration workflow
- `backend/scripts/generate_gmail_token.py` - OAuth token generator
- `backend/models/settings.py` - User settings & permissions model

---

## 🔄 Extending Notifications

The fallback system is designed to be **easily extensible**. To add new notification channels:

### Example: Slack Webhook

```python
# In notification_utils.py

async def send_slack_notification(webhook_url: str, message: str):
    """Send Slack notification via webhook."""
    import httpx
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            webhook_url,
            json={"text": message}
        )
        return response.status_code == 200

# In send_fallback_notifications():
if user_settings.get("slack_webhook"):
    await send_slack_notification(
        user_settings["slack_webhook"],
        f"⚠️ Daily briefing missing: {briefing_date}"
    )
```

### Example: SMS via Twilio

```python
from twilio.rest import Client

async def send_sms_notification(phone: str, message: str):
    """Send SMS via Twilio."""
    client = Client(settings.TWILIO_SID, settings.TWILIO_TOKEN)
    message = client.messages.create(
        to=phone,
        from_=settings.TWILIO_FROM,
        body=message
    )
    return message.sid
```

---

**Questions or issues?** Check server logs or open an issue on GitHub.
