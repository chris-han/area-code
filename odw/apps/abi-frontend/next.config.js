/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:4300',
    NEXT_PUBLIC_MOOSE_CONSUMPTION_BASE_URL:
      process.env.NEXT_PUBLIC_MOOSE_CONSUMPTION_BASE_URL || 'http://localhost:4200/consumption',
    NEXT_PUBLIC_TEMPORAL_UI_URL: process.env.NEXT_PUBLIC_TEMPORAL_UI_URL || 'http://localhost:8080',
    NEXT_PUBLIC_MINIO_CONSOLE_URL: process.env.NEXT_PUBLIC_MINIO_CONSOLE_URL || 'http://localhost:9501',
    NEXT_PUBLIC_KAFDROP_URL: process.env.NEXT_PUBLIC_KAFDROP_URL || 'http://localhost:9999',
  },
};

module.exports = nextConfig;
