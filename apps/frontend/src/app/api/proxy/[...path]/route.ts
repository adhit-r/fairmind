import { NextRequest, NextResponse } from 'next/server'

const BACKEND_BASE_URL =
  process.env.BACKEND_INTERNAL_URL ||
  process.env.BACKEND_API_URL ||
  'http://fairmind.railway.internal:8000'

async function proxy(request: NextRequest, path: string[]) {
  try {
    const targetPath = path.join('/')
    const search = request.nextUrl.search || ''
    const targetUrl = `${BACKEND_BASE_URL}/${targetPath}${search}`

    const headers = new Headers(request.headers)
    headers.delete('host')

    const response = await fetch(targetUrl, {
      method: request.method,
      headers,
      body: request.method === 'GET' || request.method === 'HEAD' ? undefined : request.body,
      duplex: 'half',
      redirect: 'manual',
    } as RequestInit)

    const responseHeaders = new Headers(response.headers)
    responseHeaders.delete('content-encoding')
    responseHeaders.delete('content-length')

    return new NextResponse(response.body, {
      status: response.status,
      headers: responseHeaders,
    })
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown proxy error'
    console.error('[API Proxy] Request failed:', {
      backend: BACKEND_BASE_URL,
      method: request.method,
      path,
      message,
    })
    return NextResponse.json(
      {
        error: 'Proxy request failed',
        backend: BACKEND_BASE_URL,
        message,
      },
      { status: 502 }
    )
  }
}

export async function GET(request: NextRequest, { params }: { params: { path: string[] } }) {
  return proxy(request, params.path || [])
}

export async function POST(request: NextRequest, { params }: { params: { path: string[] } }) {
  return proxy(request, params.path || [])
}

export async function PUT(request: NextRequest, { params }: { params: { path: string[] } }) {
  return proxy(request, params.path || [])
}

export async function PATCH(request: NextRequest, { params }: { params: { path: string[] } }) {
  return proxy(request, params.path || [])
}

export async function DELETE(request: NextRequest, { params }: { params: { path: string[] } }) {
  return proxy(request, params.path || [])
}

export async function OPTIONS(request: NextRequest, { params }: { params: { path: string[] } }) {
  return proxy(request, params.path || [])
}
