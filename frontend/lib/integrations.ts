/**
 * Integration Requirements Registry
 *
 * Single source of truth for all integrations that require external credentials.
 * Each entry declares what is needed, why, and how to obtain it.
 *
 * This file is client-safe: it contains no secret values, only metadata.
 */

export interface IntegrationRequirement {
  /** Stable identifier matching the backend setup/status response */
  id: string;
  name: string;
  icon: string;
  description: string;
  /** Whether the app is broken without this (vs. just degraded) */
  optional: boolean;
  /** Environment variables that must be set on the server */
  requiredServerVars: string[];
  /** Environment variables that are helpful but not strictly required */
  optionalServerVars?: string[];
  /** Whether an OAuth/login flow is required (not just an API key) */
  requiresOAuth: boolean;
  /** Step-by-step instructions to obtain credentials */
  howToGet: string[];
  /** Official link for obtaining the credential */
  officialLink: string;
  officialLinkLabel: string;
  /** Which UI routes/features depend on this integration */
  usedBy: string[];
  /** Notes on server-only handling */
  serverOnlyNote?: string;
}

export const INTEGRATIONS: IntegrationRequirement[] = [
  {
    id: 'grok_ai',
    name: 'Grok AI (xAI)',
    icon: '🤖',
    description:
      'Powers all AI features: company deep research, website swoop, blog generation, intelligence collectors, call transcript analysis, and the 5 specialist agents.',
    optional: false,
    requiredServerVars: ['XAI_API_KEY'],
    requiresOAuth: false,
    howToGet: [
      'Go to https://x.ai/api and sign in or create an account.',
      'Navigate to the API Keys section in your dashboard.',
      'Click "Create API Key" and copy the key (starts with xai-).',
      'Add to your server environment: XAI_API_KEY=xai-your-key-here',
      'Restart the backend server for the change to take effect.',
    ],
    officialLink: 'https://x.ai/api',
    officialLinkLabel: 'x.ai/api',
    usedBy: [
      '/intel (Company Research, Website Swoop)',
      '/blog (Generate Post)',
      '/intelligence (News/Planning/Jobs/Press Release/Infrastructure Collectors)',
      '/calls (Analyse Transcript)',
      '/agents (Build Captain, UI Surgeon, Test Pilot, Data Curator, Ops Boss)',
    ],
    serverOnlyNote:
      'XAI_API_KEY must ONLY be set as a server-side environment variable. Never expose it in NEXT_PUBLIC_ vars or client code.',
  },
  {
    id: 'aws_s3',
    name: 'Amazon S3 (File Storage)',
    icon: '☁️',
    description:
      'Required only if you set STORAGE_BACKEND=s3. By default the app uses local filesystem storage which works without any AWS credentials.',
    optional: true,
    requiredServerVars: ['S3_BUCKET', 'S3_REGION'],
    optionalServerVars: ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY'],
    requiresOAuth: false,
    howToGet: [
      'Open the AWS Console at https://aws.amazon.com/console/',
      'Create an S3 bucket in your preferred region.',
      'Create an IAM user or role with s3:PutObject, s3:GetObject, s3:DeleteObject permissions on the bucket.',
      'Generate an Access Key for the IAM user.',
      'Set: STORAGE_BACKEND=s3, S3_BUCKET=your-bucket-name, S3_REGION=eu-west-2',
      'Optionally set: AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY (or use IAM instance profile).',
    ],
    officialLink: 'https://aws.amazon.com/s3/',
    officialLinkLabel: 'aws.amazon.com/s3',
    usedBy: ['/intel (Photo Uploads, when S3 backend is selected)'],
    serverOnlyNote:
      'AWS credentials must ONLY be set as server-side environment variables. Never expose in NEXT_PUBLIC_ vars.',
  },
  {
    id: 'auth_clerk',
    name: 'Clerk Authentication',
    icon: '🔐',
    description:
      'Optional SSO provider. Set AUTH_PROVIDER=clerk to enforce authentication. By default (AUTH_PROVIDER=none) the app is open-access.',
    optional: true,
    requiredServerVars: ['CLERK_ISSUER', 'CLERK_SECRET_KEY'],
    optionalServerVars: ['CLERK_JWKS_URL', 'NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY'],
    requiresOAuth: true,
    howToGet: [
      'Create a free account at https://clerk.com',
      'Create a new application in the Clerk dashboard.',
      'Copy the Issuer URL from API Keys → Frontend API.',
      'Copy the Secret Key from API Keys.',
      'Set: AUTH_PROVIDER=clerk, CLERK_ISSUER=https://your-instance.clerk.accounts.dev',
      'Set: CLERK_SECRET_KEY=sk_...',
      'Optionally set: NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_... for frontend auth UI.',
    ],
    officialLink: 'https://clerk.com/docs/quickstarts/nextjs',
    officialLinkLabel: 'clerk.com/docs',
    usedBy: ['All routes (when AUTH_PROVIDER=clerk)'],
    serverOnlyNote:
      'CLERK_SECRET_KEY must remain server-only. NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY is safe for the frontend.',
  },
  {
    id: 'auth_auth0',
    name: 'Auth0 Authentication',
    icon: '🔑',
    description:
      'Optional SSO provider. Set AUTH_PROVIDER=auth0 to enforce authentication. By default (AUTH_PROVIDER=none) the app is open-access.',
    optional: true,
    requiredServerVars: ['AUTH0_DOMAIN', 'AUTH0_AUDIENCE'],
    optionalServerVars: ['NEXT_PUBLIC_AUTH0_DOMAIN', 'NEXT_PUBLIC_AUTH0_CLIENT_ID'],
    requiresOAuth: true,
    howToGet: [
      'Create a free account at https://auth0.com',
      'Create a new API in the Auth0 dashboard (Applications → APIs).',
      'Copy the Domain (e.g. your-tenant.auth0.com) and the API Audience.',
      'Set: AUTH_PROVIDER=auth0, AUTH0_DOMAIN=your-tenant.auth0.com',
      'Set: AUTH0_AUDIENCE=https://your-api-audience',
      'Optionally configure a frontend SPA application for login UI.',
    ],
    officialLink: 'https://auth0.com/docs/quickstart/backend/python',
    officialLinkLabel: 'auth0.com/docs',
    usedBy: ['All routes (when AUTH_PROVIDER=auth0)'],
    serverOnlyNote:
      'AUTH0_AUDIENCE and backend API credentials must remain server-only. Client-side auth flow uses separate Auth0 SPA credentials.',
  },
];

/** Map from integration id → IntegrationRequirement */
export const INTEGRATION_MAP = Object.fromEntries(INTEGRATIONS.map((i) => [i.id, i]));

/** Feature → integration id map – which integration gates each feature */
export const FEATURE_INTEGRATION: Record<string, string> = {
  company_research: 'grok_ai',
  website_swoop: 'grok_ai',
  blog_generation: 'grok_ai',
  intelligence_collectors: 'grok_ai',
  call_transcription: 'grok_ai',
  agents: 'grok_ai',
  file_uploads_s3: 'aws_s3',
  authentication: 'auth_clerk',
};
