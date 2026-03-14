const withMDX = require('@next/mdx')({
  extension: /\.mdx?$/,
  options: {
    remarkPlugins: [],
    rehypePlugins: [],
  },
})

// Security: Restrict remote image patterns to specific trusted domains
// Production: Only allow images from trusted sources (prevents SSRF, hotlinking, cache poisoning)
// Development: Allow any HTTPS images for testing convenience
const remotePatterns = process.env.NODE_ENV === 'production'
  ? [
      // Self-hosted images (when deployed to production domain)
      {
        protocol: 'https',
        hostname: 'agent-jumbo.com',
      },
      // GitHub raw content for documentation images
      {
        protocol: 'https',
        hostname: 'raw.githubusercontent.com',
        pathname: '/agent-jumbo-deploy/agent-jumbo/**',
      },
      // GitHub user avatars (if needed)
      {
        protocol: 'https',
        hostname: 'avatars.githubusercontent.com',
      },
    ]
  : [
      // Development/preview: More permissive for testing
      {
        protocol: 'https',
        hostname: '**',
      },
    ]

module.exports = withMDX({
  pageExtensions: ['js', 'jsx', 'ts', 'tsx', 'md', 'mdx'],
  reactStrictMode: true,
  swcMinify: true,
  images: {
    remotePatterns,
  },
  experimental: {
    esmExternals: 'loose',
  },
})
