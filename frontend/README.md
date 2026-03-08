# aLiGN Frontend

Next.js 15 application with Clerk authentication and Vercel deployment support.

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/flencrypto/xALiGN&env=NEXT_PUBLIC_API_URL,NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY,CLERK_SECRET_KEY&project-name=align)

## ⚡ Quick Deploy to Vercel

### 1. Deploy Backend First
Choose one platform for your FastAPI backend:
- **Railway**: `railway up` (recommended)
- **Render**: Connect repo, deploy backend folder
- **fly.io**: `fly launch` from backend folder

### 2. Deploy Frontend to Vercel
Click button above or run:
```bash
vercel --cwd frontend
```

### 3. Configure Environment Variables
In Vercel dashboard → Settings → Environment Variables:
- `NEXT_PUBLIC_API_URL`: `https://your-backend.railway.app/api/v1`
- `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`: From [Clerk](https://dashboard.clerk.com)
- `CLERK_SECRET_KEY`: From [Clerk](https://dashboard.clerk.com)

**📖 Full deployment guide:** See [../VERCEL_DEPLOYMENT.md](../VERCEL_DEPLOYMENT.md)

---

## 🚀 Getting Started (Local Development)

### Prerequisites
- Node.js 18+ 
- npm or yarn
- Backend running at `http://localhost:8000`

### Installation

```bash
npm install
# or
yarn install
```

### Environment Setup

Create `.env.local`:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_CLERK_SIGN_IN_FALLBACK_REDIRECT_URL=/dashboard
NEXT_PUBLIC_CLERK_SIGN_UP_FALLBACK_REDIRECT_URL=/dashboard
```

See [.env.example](.env.example) for all options.

### Run Development Server

```bash
npm run dev
# or
yarn dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser.

---

## 📁 Project Structure

```
frontend/
├── app/                    # Next.js 15 App Router
│   ├── (auth)/            # Authentication pages
│   │   ├── sign-in/       # Clerk sign-in
│   │   └── sign-up/       # Clerk sign-up
│   ├── (dashboard)/       # Protected dashboard routes
│   │   ├── accounts/      # Account management
│   │   ├── opportunities/ # Opportunities tracking
│   │   ├── bids/          # Bid management
│   │   ├── calls/         # Call recordings
│   │   └── ...            # Other dashboard pages
│   ├── layout.tsx         # Root layout with Clerk
│   └── page.tsx           # Landing page
├── components/            # React components
│   ├── ui/               # Reusable UI components
│   └── ...               # Feature components
├── lib/                   # Utilities & API client
│   ├── api.ts            # Backend API client
│   └── utils.ts          # Helper functions
├── public/               # Static assets
├── types/                # TypeScript types
├── next.config.mjs       # Next.js configuration
├── tailwind.config.ts    # Tailwind CSS config
└── tsconfig.json         # TypeScript config
```

---

## 🛠️ Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server at http://localhost:3000 |
| `npm run build` | Build for production |
| `npm run start` | Start production server |
| `npm run lint` | Run ESLint |

---

## 🌐 Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API endpoint | `http://localhost:8000/api/v1` |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Clerk public key | `pk_test_...` |
| `CLERK_SECRET_KEY` | Clerk secret key | `sk_test_...` |

### Optional Variables (with defaults)

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_CLERK_SIGN_IN_URL` | `/sign-in` | Sign-in page path |
| `NEXT_PUBLIC_CLERK_SIGN_UP_URL` | `/sign-up` | Sign-up page path |
| `NEXT_PUBLIC_CLERK_SIGN_IN_FALLBACK_REDIRECT_URL` | `/dashboard` | Where to redirect after sign-in |
| `NEXT_PUBLIC_CLERK_SIGN_UP_FALLBACK_REDIRECT_URL` | `/dashboard` | Where to redirect after sign-up |

---

## 🔐 Authentication (Clerk)

This app uses [Clerk](https://clerk.com) for authentication.

### Setup Clerk

1. Create account at [clerk.com](https://clerk.com)
2. Create application
3. Copy API keys to `.env.local`
4. Configure paths in Clerk dashboard:
   - Sign-in: `/sign-in`
   - Sign-up: `/sign-up`
   - After sign-in: `/dashboard`

### Protected Routes

All routes under `/dashboard` require authentication. See [proxy.ts](./proxy.ts) for middleware configuration.

---

## 🎨 Tech Stack

- **Framework**: Next.js 15.5.12 (App Router)
- **Language**: TypeScript 5
- **Styling**: Tailwind CSS
- **Authentication**: Clerk
- **Maps**: Leaflet + react-leaflet
- **Charts**: Recharts
- **Deployment**: Vercel

---

## 🚀 Deployment

### Vercel (Recommended)

1. **Deploy backend** (Railway/Render/fly.io)
2. **Click deploy button** at top of README
3. **Add environment variables** in Vercel dashboard
4. **Update CORS** on backend to allow Vercel domain

Full guide: [../VERCEL_DEPLOYMENT.md](../VERCEL_DEPLOYMENT.md)

### Other Platforms

- **Netlify**: Already has plugin (`@netlify/plugin-nextjs`)
- **Docker**: Set `DOCKER_BUILD=true`, use standalone output
- **Self-hosted**: `npm run build && npm run start`

---

## 📚 Learn More

- [Next.js Documentation](https://nextjs.org/docs)
- [Clerk Documentation](https://clerk.com/docs)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [Vercel Deployment](https://vercel.com/docs)

---

## 🐛 Troubleshooting

### Build fails on Vercel
- Check environment variables are set
- Clear Vercel cache: Settings → General → Clear Cache

### API calls return 401
- Verify `NEXT_PUBLIC_API_URL` is correct
- Check backend CORS allows frontend domain
- Ensure Clerk token is being sent

### Clerk redirect loops
- Verify all Clerk environment variables
- Check Clerk dashboard paths match your variables
- Add frontend domain to Clerk allowed domains

---

## 📄 License

UNLICENSED - Private project

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
