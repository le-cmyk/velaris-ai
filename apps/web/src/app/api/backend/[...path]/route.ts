import { NextRequest, NextResponse } from 'next/server';

const DEFAULT_BACKEND_URL = 'http://127.0.0.1:8000';

type RouteContext = {
  params: {
    path?: string[];
  };
};

function getBackendBaseUrl(): string {
  return (process.env.BACKEND_API_URL || DEFAULT_BACKEND_URL).replace(/\/+$/, '');
}

function buildTargetUrl(request: NextRequest, path: string[] = []): string {
  const target = new URL(`${getBackendBaseUrl()}/${path.join('/')}`);
  target.search = request.nextUrl.search;
  return target.toString();
}

function buildProxyHeaders(request: NextRequest): Headers {
  const headers = new Headers(request.headers);
  headers.delete('host');
  headers.delete('content-length');
  headers.delete('connection');
  return headers;
}

async function proxyRequest(request: NextRequest, context: RouteContext): Promise<NextResponse> {
  const method = request.method.toUpperCase();
  const hasBody = !['GET', 'HEAD'].includes(method);
  const response = await fetch(buildTargetUrl(request, context.params.path), {
    method,
    headers: buildProxyHeaders(request),
    body: hasBody ? await request.text() : undefined,
    cache: 'no-store',
  });

  const body = await response.arrayBuffer();
  const headers = new Headers(response.headers);
  headers.delete('content-encoding');
  headers.delete('content-length');

  return new NextResponse(body, {
    status: response.status,
    statusText: response.statusText,
    headers,
  });
}

export async function GET(request: NextRequest, context: RouteContext) {
  return proxyRequest(request, context);
}

export async function POST(request: NextRequest, context: RouteContext) {
  return proxyRequest(request, context);
}

export async function PATCH(request: NextRequest, context: RouteContext) {
  return proxyRequest(request, context);
}

export async function PUT(request: NextRequest, context: RouteContext) {
  return proxyRequest(request, context);
}

export async function DELETE(request: NextRequest, context: RouteContext) {
  return proxyRequest(request, context);
}
