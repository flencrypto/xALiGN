#!/bin/bash
# Vercel Build Script
# This ensures the frontend builds correctly on Vercel

echo "🚀 Starting Vercel build for aLiGN frontend..."

# Navigate to frontend directory
cd frontend || exit 1

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Build Next.js application
echo "🔨 Building Next.js application..."
npm run build

echo "✅ Build complete!"
