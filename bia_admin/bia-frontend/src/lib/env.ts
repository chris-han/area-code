import { z } from 'zod'

const envSchema = z.object({
  NEXT_PUBLIC_API_BASE_URL: z.string().url().default('http://localhost:4300'),
  NEXT_PUBLIC_MOOSE_CONSUMPTION_BASE_URL: z.string().url().default('http://localhost:4201/api'),
  NEXT_PUBLIC_TEMPORAL_UI_URL: z.string().url().default('http://localhost:8080'),
  NEXT_PUBLIC_MINIO_CONSOLE_URL: z.string().url().default('http://localhost:9501'),
  NEXT_PUBLIC_KAFDROP_URL: z.string().url().default('http://localhost:9999'),
  NODE_ENV: z.enum(['development', 'production', 'test']).default('development'),
})

export type Env = z.infer<typeof envSchema>

function getEnv(): Env {
  const env = {
    NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL,
    NEXT_PUBLIC_MOOSE_CONSUMPTION_BASE_URL: process.env.NEXT_PUBLIC_MOOSE_CONSUMPTION_BASE_URL,
    NEXT_PUBLIC_TEMPORAL_UI_URL: process.env.NEXT_PUBLIC_TEMPORAL_UI_URL,
    NEXT_PUBLIC_MINIO_CONSOLE_URL: process.env.NEXT_PUBLIC_MINIO_CONSOLE_URL,
    NEXT_PUBLIC_KAFDROP_URL: process.env.NEXT_PUBLIC_KAFDROP_URL,
    NODE_ENV: process.env.NODE_ENV,
  }

  const result = envSchema.safeParse(env)
  
  if (!result.success) {
    console.error('❌ Invalid environment variables:', result.error.format())
    throw new Error('Invalid environment variables')
  }

  return result.data
}

export const env = getEnv()

// Export individual environment variables for convenience
export const {
  NEXT_PUBLIC_API_BASE_URL,
  NEXT_PUBLIC_MOOSE_CONSUMPTION_BASE_URL,
  NEXT_PUBLIC_TEMPORAL_UI_URL,
  NEXT_PUBLIC_MINIO_CONSOLE_URL,
  NEXT_PUBLIC_KAFDROP_URL,
  NODE_ENV,
} = env
