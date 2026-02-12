/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  skipMiddlewareUrlNormalize: true,
}

// Disable static generation for client context pages
if (process.env.NEXT_PHASE === 'phase-production-build') {
  nextConfig.skipTrailingSlashRedirect = true
}

module.exports = nextConfig
