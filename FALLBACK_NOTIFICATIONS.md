# Fallback Notification System - Quick Reference

## ✅ What's Been Implemented

The system now has intelligent fallback notifications when the daily briefing email is missing or fetch fails.

### 📁 New Files Created

1. **`backend/models/settings.py`** - User settings & permissions model
   - `social_draft` - Allow X/Twitter draft creation (default: True)
   - `gmail_draft` - Allow email draft creation (default: True)  
   - `full_autopilot` - Allow auto-posting without approval (default: False)
   - Contact details: `notification_email`, `x_handle`, `slack_webhook`

2. **`backend/services/notification_utils.py`** - Notification system
   - `get_user_settings()` - Fetch permissions (safe defaults)
   - `social_create_draft()` - Create X/Twitter DM draft
   - `gmail_draft_email()` - Create Gmail draft via API
   - `send_fallback_notifications()` - Main orchestrator

3. **`backend/client_secret.json`** - Gmail OAuth credentials
   - Client ID: `YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com`
   - Client Secret: `YOUR_GOOGLE_CLIENT_SECRET`
   - ⚠️ Already added to `.gitignore` (never commit!)

4. **`docs/gmail-fallback-setup.md`** - Complete setup guide
   - OAuth token generation steps
   - Testing instructions
   - Troubleshooting guide
   - Extension examples (Slack, SMS)

### 🔧 Modified Files

1. **`backend/core/config.py`** - Added notification settings
   ```python
   NOTIFICATION_EMAIL: str = ""  # Your email for fallback alerts
   X_HANDLE: str = "TheMrFlen"   # X/Twitter handle
   ```

2. **`backend/services/briefing_ingestion.py`** - Updated workflow
   ```python
   if not briefing_text:
       # NEW: Send fallback notifications instead of silent skip
       notification_result = await send_fallback_notifications(briefing_date)
       result["fallback_notifications"] = notification_result
       logger.info(f"Fallback notifications: {len(notification_result.get('notifications_sent', []))} sent")
   ```

3. **`backend/models/__init__.py`** - Registered UserSettings model

4. **`.env`** - Added Gmail OAuth and notification settings

---

## 🚀 Next Steps: Complete Setup

### Step 1: Generate Gmail OAuth Token

```bash
cd backend
python scripts/generate_gmail_token.py
```

This will:
1. Open browser for Google login
2. Request Gmail permissions
3. Save `token.pickle` file
4. Print credentials for `.env`

### Step 2: Update `.env` File

Add the credentials printed by the script:

```env
# Gmail Integration
GOOGLE_CLIENT_ID=YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=YOUR_GOOGLE_CLIENT_SECRET
GOOGLE_REFRESH_TOKEN=1//0g...your_refresh_token_here

# Fallback Notifications
NOTIFICATION_EMAIL=your-email@example.com  # ← Add your email
X_HANDLE=TheMrFlen
```

### Step 3: Run Database Migration

Add the new `UserSettings` table:

```bash
cd backend
alembic revision --autogenerate -m "Add user settings for notifications"
alembic upgrade head
```

### Step 4: Test Fallback Notifications

```python
# Test in Python console
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
    {"type": "x_draft", "status": "success", "draft_id": "draft_x_..."},
    {"type": "gmail_draft", "status": "success", "draft_id": "r-..."}
  ],
  "errors": []
}
```

---

## 📋 How It Works

### Normal Flow (Briefing Found)
```
Daily Scheduler → Fetch Gmail → Parse with Grok → Upsert Data → Generate Touchpoints → Success ✅
```

### Fallback Flow (No Briefing)
```
Daily Scheduler → Fetch Gmail → ❌ No Email Found → Check Permissions → Create X Draft ✅ → Create Email Draft ✅ → Log Warning 📝
```

### Safety Checks

✅ **Drafts only by default** - No auto-posting unless `full_autopilot=True`  
✅ **Permission checking** - Respects user settings (social_draft, gmail_draft)  
✅ **Non-critical failures** - Wrapped in try/except (won't break scheduler)  
✅ **Detailed logging** - Full visibility in server logs  
✅ **No false alarms** - Only triggers when email truly missing

---

## 🔔 Notification Examples

### X (Twitter) DM Draft
```
@TheMrFlen Daily DC briefing email missing today (2026-03-07). 
No new intel pulled – check inbox or manual upload? #alignapp
```

### Gmail Draft Email
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

## 🛠️ Extending to Other Channels

The system is designed to be easily extensible. See `docs/gmail-fallback-setup.md` for examples:

- **Slack Webhook** - Instant team notifications
- **SMS via Twilio** - Critical mobile alerts
- **Push Notifications** - Browser/mobile push
- **Microsoft Teams** - Enterprise messaging
- **Discord** - Community alerts

Just add the logic to `send_fallback_notifications()` in `notification_utils.py`.

---

## 📚 Documentation

- **Full setup guide**: `docs/gmail-fallback-setup.md`
- **OAuth setup**: Run `python backend/scripts/generate_gmail_token.py`
- **Code reference**: 
  - `backend/services/notification_utils.py`
  - `backend/services/briefing_ingestion.py`
  - `backend/models/settings.py`

---

**Status**: ✅ Implementation complete - Ready for OAuth setup and testing!
