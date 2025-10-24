import { NextResponse } from 'next/server'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:4300'

async function proxyRequest(
  request: Request,
  params: { path: string[] }
) {
  const targetPath = params.path?.join('/') ?? ''
  const search = new URL(request.url).search
  const targetUrl = `${API_BASE_URL}/${targetPath}${search}`

  const init: RequestInit = {
    method: request.method,
    headers: new Headers(request.headers),
    body: undefined,
    redirect: 'manual',
  }

  if (!['GET', 'HEAD'].includes(request.method)) {
    const buffer = await request.arrayBuffer()
    init.body = buffer
  }

  // Remove host-related headers to avoid cross-origin issues
  init.headers.delete('host')
  init.headers.delete('origin')

  let response: Response

  try {
    response = await fetch(targetUrl, init)
  } catch (error) {
    const err = error as { cause?: { code?: string }; message?: string }
    const timeout = err?.cause?.code === 'UND_ERR_CONNECT_TIMEOUT'
    const status = timeout ? 504 : 502
    const message = timeout
      ? 'Upstream service timed out'
      : 'Failed to reach upstream service'

    console.error('Proxy request failed', {
      targetUrl,
      status,
      error: err,
    })

    return NextResponse.json(
      {
        error: message,
        details: err?.message,
      },
      { status }
    )
  }
  const responseHeaders = new Headers(response.headers)
  responseHeaders.delete('content-security-policy')
  responseHeaders.delete('content-length')
  responseHeaders.delete('content-encoding')

  const body = await response.arrayBuffer()
  return new NextResponse(body, {
    status: response.status,
    statusText: response.statusText,
    headers: responseHeaders,
  })
}

export async function GET(request: Request, { params }: { params: { path: string[] } }) {
  return proxyRequest(request, params)
}

export async function POST(request: Request, { params }: { params: { path: string[] } }) {
  return proxyRequest(request, params)
}

export async function PUT(request: Request, { params }: { params: { path: string[] } }) {
  return proxyRequest(request, params)
}

export async function PATCH(request: Request, { params }: { params: { path: string[] } }) {
  return proxyRequest(request, params)
}

export async function DELETE(request: Request, { params }: { params: { path: string[] } }) {
  return proxyRequest(request, params)
}

export const dynamic = 'force-dynamic'
