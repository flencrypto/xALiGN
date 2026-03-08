import { dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Silence "multiple lockfiles" warning by pinning the workspace root
  outputFileTracingRoot: __dirname,

  // Use standalone output when building inside Docker (set DOCKER_BUILD=true).
  // Vercel and Netlify deployments should leave this unset.
  ...(process.env.DOCKER_BUILD === 'true' && { output: 'standalone' }),
  
  // Image optimization
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**',
      },
    ],
  },
  
  // Environment variables validation
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  },
};

export default nextConfig;
