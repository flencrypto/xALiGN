# Vercel Deployment Guide for aLiGN

This guide walks you through deploying the **aLiGN frontend** to Vercel.

## Architecture Overview

- **Frontend (Next.js)**: Deployed to Vercel
- **Backend (FastAPI/Python)**: Deploy separately to Railway, Render, fly.io, or any Python-compatible host
- **Database (PostgreSQL)**: Use Vercel Postgres, Railway, or managed PostgreSQL (Neon, Supabase)

## Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **Clerk Account**: Set up at [clerk.com](https://clerk.com) for authentication
3. **Backend Deployed**: Your FastAPI backend must be deployed and accessible via HTTPS

## Step 1: Deploy Backend (FastAPI)

**Option A: Railway** (Recommended)
1. Go to [railway.app](https://railway.app)
2. Create new project → Deploy from GitHub
3. Select your repository → Choose `backend` directory
4. Add environment variables:
   ```
   DATABASE_URL=postgresql://...
   XAI_API_KEY=xai-...
   CLERK_ISSUER=https://...
   CLERK_JWKS_URL=https://...
   CORS_ORIGINS=https://your-app.vercel.app
   ```
5. Note your backend URL: `https://your-app.railway.app`

**Option B: Render**
1. Go to [render.com](https://render.com)
2. New Web Service → Connect repository
3. Build command: `pip install -r backend/requirements.txt`
4. Start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables (same as above)

**Option C: fly.io**
```bash
cd backend
fly launch
fly secrets set DATABASE_URL=... XAI_API_KEY=... CLERK_ISSUER=...
fly deploy
```

## Step 2: Configure Clerk

1. Go to [dashboard.clerk.com](https://dashboard.clerk.com)
2. Create application (or use existing)
3. **Add production domain**:
   - Settings → Domains → Add domain
   - Add: `your-app.vercel.app`
4. **Get credentials**:
   - API Keys → Copy:
     - `Publishable Key` (pk_live_...)
     - `Secret Key` (sk_live_...)
5. **Configure URLs**:
   - Paths → Set:
     - Sign-in: `/sign-in`
     - Sign-up: `/sign-up`
     - After sign-in: `/dashboard`
     - After sign-up: `/dashboard`

## Step 3: Deploy to Vercel

### Option A: Vercel CLI (Recommended)

```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy (from project root)
cd aLiGN
vercel

# Follow prompts:
# - Set up and deploy? Y
# - Which scope? (your account)
# - Link to existing project? N
# - Project name? align (or your choice)
# - Directory? ./frontend
# - Override settings? N

# Add environment variables
vercel env add NEXT_PUBLIC_API_URL
# Enter: https://your-backend.railway.app/api/v1

vercel env add NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
# Enter: pk_live_...

vercel env add CLERK_SECRET_KEY
# Enter: sk_live_...

# Deploy to production
vercel --prod
```

### Option B: Vercel Dashboard

1. Go to [vercel.com/new](https://vercel.com/new)
2. Import Git Repository → Select your repo
3. **Configure Project**:
   - Framework Preset: **Next.js**
   - Root Directory: `frontend`
   - Build Command: `npm run build` (auto-detected)
   - Output Directory: `.next` (auto-detected)
4. **Environment Variables** → Add:
   ```
   NEXT_PUBLIC_API_URL=https://your-backend.railway.app/api/v1
   NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_...
   CLERK_SECRET_KEY=sk_live_...
   NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
   NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
   NEXT_PUBLIC_CLERK_SIGN_IN_FALLBACK_REDIRECT_URL=/dashboard
   NEXT_PUBLIC_CLERK_SIGN_UP_FALLBACK_REDIRECT_URL=/dashboard
   ```
5. Click **Deploy**

## Step 4: Update Backend CORS

After Vercel gives you a URL (e.g., `https://align-xyz.vercel.app`), update your backend:

**Railway/Render/fly.io:**
```bash
# Add Vercel URL to CORS_ORIGINS
CORS_ORIGINS=https://align-xyz.vercel.app,https://align-xyz-preview.vercel.app
```

**Restart backend** to apply changes.

## Step 5: Test Deployment

1. Visit your Vercel URL: `https://align-xyz.vercel.app`
2. Click **Sign In** → Should redirect to Clerk
3. Sign in → Should redirect to `/dashboard`
4. Test API calls:
   - Accounts page → Should fetch from backend
   - Opportunities → Should display data
   - Check browser console for errors

## Environment Variables Reference

### Required for Vercel

| Variable | Example | Where to Get |
|----------|---------|--------------|
| `NEXT_PUBLIC_API_URL` | `https://backend.railway.app/api/v1` | Your deployed backend URL |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | `pk_live_...` | [Clerk Dashboard](https://dashboard.clerk.com) → API Keys |
| `CLERK_SECRET_KEY` | `sk_live_...` | [Clerk Dashboard](https://dashboard.clerk.com) → API Keys |

### Optional (have defaults)

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_CLERK_SIGN_IN_URL` | `/sign-in` | Sign-in page path |
| `NEXT_PUBLIC_CLERK_SIGN_UP_URL` | `/sign-up` | Sign-up page path |
| `NEXT_PUBLIC_CLERK_SIGN_IN_FALLBACK_REDIRECT_URL` | `/dashboard` | Where to go after sign-in |
| `NEXT_PUBLIC_CLERK_SIGN_UP_FALLBACK_REDIRECT_URL` | `/dashboard` | Where to go after sign-up |

## Troubleshooting

### Build fails: "Module not found"
```bash
# Clear Vercel cache
vercel --force

# Or in dashboard: Settings → General → Clear Cache
```

### 401 errors on API calls
- Check `NEXT_PUBLIC_API_URL` is correct
- Verify backend CORS allows your Vercel domain
- Check Clerk token is being sent (Network tab → Headers)

### Clerk redirects not working
- Verify all Clerk URLs in environment variables
- Check Clerk dashboard → Paths are configured correctly
- Add Vercel domain to Clerk → Settings → Domains

### Backend unreachable
- Verify backend is running: `curl https://your-backend.railway.app/api/v1/`
- Check backend logs for errors
- Ensure DATABASE_URL is set on backend

## Preview Deployments

Vercel automatically creates preview deployments for every PR:
- URL: `https://align-xyz-git-branch-name.vercel.app`
- Uses same environment variables as production
- Great for testing before merging

To use different backend for previews:
```bash
vercel env add NEXT_PUBLIC_API_URL preview
# Enter: https://your-staging-backend.railway.app/api/v1
```

## Custom Domain

1. Vercel Dashboard → Your Project → Settings → Domains
2. Add domain: `align.yourdomain.com`
3. Configure DNS (Vercel provides instructions)
4. Update Clerk allowed domains
5. Update backend CORS_ORIGINS

## Database Options for Backend

### Option 1: Vercel Postgres (Recommended for Vercel + Railway)
```bash
# Add to your Railway/Render backend
DATABASE_URL=postgresql://user:pass@db.vercel-storage.com:5432/verceldb
```

### Option 2: Railway Postgres
```bash
# Railway automatically provisions this
DATABASE_URL=postgresql://user:pass@containers-us-west-xxx.railway.app:7215/railway
```

### Option 3: Neon (Serverless Postgres)
```bash
# From neon.tech
DATABASE_URL=postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/neondb
```

### Option 4: Supabase
```bash
# From supabase.com
DATABASE_URL=postgresql://postgres:pass@db.xxx.supabase.co:5432/postgres
```

## CI/CD

Vercel automatically redeploys when you:
- Push to `main` branch → Production deployment
- Create PR → Preview deployment
- Merge PR → Production deployment

No additional CI/CD setup needed!

## Cost Estimate

**Free Tier:**
- Vercel: 100GB bandwidth/month, unlimited deployments
- Railway: $5/month credit (backend + database)
- Clerk: 10,000 MAU free

**Pro Tier** (when you scale):
- Vercel Pro: $20/month (unlimited bandwidth, advanced features)
- Railway Pro: ~$20-50/month (depends on usage)
- Clerk Pro: $25/month (50,000 MAU)

## Next Steps

1. ✅ Deploy backend to Railway/Render
2. ✅ Configure Clerk authentication
3. ✅ Deploy frontend to Vercel
4. ✅ Test end-to-end workflow
5. 🎯 Add custom domain
6. 🎯 Set up monitoring (Vercel Analytics, Sentry)
7. 🎯 Configure Vercel Edge Functions for API routes (optional)

## Support

- **Vercel Issues**: Check [vercel.com/docs](https://vercel.com/docs)
- **Clerk Issues**: Check [clerk.com/docs](https://clerk.com/docs)
- **Backend Issues**: Check Railway/Render logs

## Files in This Repo

- `vercel.json` - Vercel project configuration
- `.vercelignore` - Files excluded from Vercel build
- `frontend/.env.example` - Environment variables reference
- `VERCEL_DEPLOYMENT.md` - This guide
