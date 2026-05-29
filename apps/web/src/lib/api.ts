import type {
  ApprovalRequest,
  AuditLogEntry,
  ChatResponse,
  ClientDataRecord,
  ClientDataListResponse,
  ToolInfo,
  User,
  WorkspaceInfo,
} from '@/types';

const RAW_API_URL = process.env.NEXT_PUBLIC_API_URL ?? '';
const API_URL = normalizeApiBaseUrl(RAW_API_URL);
const MISSING_API_URL_MESSAGE = 'Frontend API is not configured. Set NEXT_PUBLIC_API_URL in Vercel and reload the app.';
const BODY_PREVIEW_LENGTH = 500;

let apiConfigLogged = false;

interface LoginResponse {
  token?: string;
  access_token?: string;
  user: User;
}

interface ApprovalActionResponse {
  approval_id: string;
  status: ApprovalRequest['status'];
}

interface AuditLogsResponse {
  items: AuditLogEntry[];
}

interface ApiResponse<T> {
  data: T;
  status: number;
  statusText: string;
  url: string;
}

export interface ApiHealthDebugResult {
  configuredApiUrl: string;
  requestUrl: string | null;
  status: number | null;
  statusText: string | null;
  data: unknown;
  error: string | null;
  checkedAt: string;
}

class ApiRequestError extends Error {
  requestUrl?: string;
  status?: number;
  statusText?: string;
  missingApiUrl: boolean;

  constructor(
    message: string,
    details: {
      requestUrl?: string;
      status?: number;
      statusText?: string;
      missingApiUrl?: boolean;
    } = {},
  ) {
    super(message);
    this.name = 'ApiRequestError';
    this.requestUrl = details.requestUrl;
    this.status = details.status;
    this.statusText = details.statusText;
    this.missingApiUrl = details.missingApiUrl ?? false;
  }
}

function normalizeApiBaseUrl(value: string): string {
  return value.trim().replace(/\/+$/, '');
}

function sanitizeUrlForLogs(value: string): string {
  if (!value) {
    return '(missing)';
  }

  try {
    const url = new URL(value);
    url.username = '';
    url.password = '';
    url.search = '';
    url.hash = '';
    return url.toString().replace(/\/$/, '');
  } catch {
    return value.replace(/[?#].*$/, '');
  }
}

function logApiConfig(): void {
  if (apiConfigLogged) {
    return;
  }

  apiConfigLogged = true;
  console.log('[API DEBUG] NEXT_PUBLIC_API_URL:', sanitizeUrlForLogs(RAW_API_URL));
}

function getConfiguredApiUrl(): string {
  return sanitizeUrlForLogs(RAW_API_URL);
}

logApiConfig();

function buildApiUrl(path: string): string {
  if (!API_URL) {
    throw new ApiRequestError(MISSING_API_URL_MESSAGE, { missingApiUrl: true });
  }

  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${API_URL}${normalizedPath}`;
}

function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('velaris_token');
}

function parseResponseBody(text: string): unknown {
  if (!text) {
    return null;
  }

  try {
    return JSON.parse(text) as unknown;
  } catch {
    return text;
  }
}

function getBodyPreview(text: string): string {
  return text ? text.slice(0, BODY_PREVIEW_LENGTH) : '(empty)';
}

function getResponseDetail(data: unknown): string | null {
  if (typeof data === 'string' && data.trim()) {
    return data.trim();
  }

  if (typeof data === 'object' && data !== null) {
    if ('detail' in data && data.detail != null) {
      return String(data.detail);
    }

    if ('message' in data && data.message != null) {
      return String(data.message);
    }
  }

  return null;
}

function buildFailedRequestMessage(requestUrl: string, status: number, statusText: string, detail?: string | null): string {
  const statusLabel = statusText ? `${status} ${statusText}` : String(status);
  return detail
    ? `API request to ${requestUrl} failed with ${statusLabel}: ${detail}`
    : `API request to ${requestUrl} failed with ${statusLabel}.`;
}

function buildNetworkErrorMessage(requestUrl: string): string {
  return `Unable to reach API at ${requestUrl}. Check NEXT_PUBLIC_API_URL in Vercel and open /debug-api for more details.`;
}

function logApiError(error: Error, requestUrl: string | undefined, missingApiUrl: boolean): void {
  console.error('[API DEBUG] Error:', {
    name: error.name,
    message: error.message,
    requestUrl: requestUrl ?? '(unavailable)',
    missingApiUrl,
  });
}

async function requestJson<T>(path: string, options: RequestInit = {}): Promise<ApiResponse<T>> {
  logApiConfig();

  let requestUrl: string;

  try {
    requestUrl = buildApiUrl(path);
  } catch (error) {
    const apiError = error instanceof ApiRequestError ? error : new ApiRequestError(MISSING_API_URL_MESSAGE, { missingApiUrl: true });
    logApiError(apiError, apiError.requestUrl, apiError.missingApiUrl);
    throw apiError;
  }

  const token = getToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...((options.headers as Record<string, string> | undefined) ?? {}),
  };

  if (token) {
    headers.Authorization = `******;
  }

  console.log('[API DEBUG] Request:', requestUrl);

  let response: Response;

  try {
    response = await fetch(requestUrl, {
      ...options,
      headers,
    });
  } catch (error) {
    const networkError =
      error instanceof Error ? error : new Error('Unknown network error while contacting the frontend API.');
    logApiError(networkError, requestUrl, !API_URL);
    throw new ApiRequestError(buildNetworkErrorMessage(requestUrl), {
      requestUrl,
      missingApiUrl: !API_URL,
    });
  }

  const text = await response.text();
  const data = parseResponseBody(text);

  console.log('[API DEBUG] Response:', response.status, response.statusText);
  console.log('[API DEBUG] Body preview:', getBodyPreview(text));

  if (!response.ok) {
    const detail = getResponseDetail(data);
    const apiError = new ApiRequestError(buildFailedRequestMessage(requestUrl, response.status, response.statusText, detail), {
      requestUrl,
      status: response.status,
      statusText: response.statusText,
      missingApiUrl: !API_URL,
    });
    logApiError(apiError, requestUrl, apiError.missingApiUrl);
    throw apiError;
  }

  return {
    data: data as T,
    status: response.status,
    statusText: response.statusText,
    url: requestUrl,
  };
}

export const api = {
  login: async (email: string, password: string): Promise<{ token: string; user: User }> => {
    const response = await requestJson<LoginResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    const token = response.data.access_token ?? response.data.token;

    if (!token) {
      throw new Error('Login response did not include a token');
    }

    return { token, user: response.data.user };
  },

  signup: async (
    email: string,
    password: string,
    fullName?: string,
    workspaceName?: string,
  ): Promise<{ token: string; user: User }> => {
    const response = await requestJson<LoginResponse>('/auth/signup', {
      method: 'POST',
      body: JSON.stringify({
        email,
        password,
        full_name: fullName ?? '',
        workspace_name: workspaceName ?? '',
      }),
    });
    const token = response.data.access_token ?? response.data.token;

    if (!token) {
      throw new Error('Signup response did not include a token');
    }

    return { token, user: response.data.user };
  },

  sendMessage: async (message: string, workspace_id: string): Promise<ChatResponse> => {
    const response = await requestJson<ChatResponse>('/chat', {
      method: 'POST',
      body: JSON.stringify({ message, workspace_id }),
    });
    return response.data;
  },

  getApprovals: async (): Promise<ApprovalRequest[]> => {
    const response = await requestJson<ApprovalRequest[]>('/approvals');
    return response.data;
  },

  approveAction: async (approvalId: string): Promise<ApprovalActionResponse> => {
    const response = await requestJson<ApprovalActionResponse>(`/approvals/${approvalId}/approve`, {
      method: 'POST',
      body: JSON.stringify({ decision: 'approve' }),
    });
    return response.data;
  },

  rejectAction: async (approvalId: string): Promise<ApprovalActionResponse> => {
    const response = await requestJson<ApprovalActionResponse>(`/approvals/${approvalId}/reject`, {
      method: 'POST',
      body: JSON.stringify({ decision: 'reject' }),
    });
    return response.data;
  },

  getAuditLogs: async (): Promise<AuditLogEntry[]> => {
    const response = await requestJson<AuditLogsResponse>('/audit-logs');
    return response.data.items;
  },

  getTools: async (): Promise<ToolInfo[]> => {
    const response = await requestJson<ToolInfo[]>('/tools');
    return response.data;
  },

  getWorkspace: async (): Promise<WorkspaceInfo> => {
    const response = await requestJson<WorkspaceInfo>('/workspace');
    return response.data;
  },

  getHealth: async (): Promise<unknown> => {
    const response = await requestJson<unknown>('/health', { cache: 'no-store' });
    return response.data;
  },

  getHealthDebug: async (): Promise<ApiHealthDebugResult> => {
    const checkedAt = new Date().toISOString();

    try {
      const response = await requestJson<unknown>('/health', { cache: 'no-store' });
      return {
        configuredApiUrl: getConfiguredApiUrl(),
        requestUrl: response.url,
        status: response.status,
        statusText: response.statusText,
        data: response.data,
        error: null,
        checkedAt,
      };
    } catch (error) {
      return {
        configuredApiUrl: getConfiguredApiUrl(),
        requestUrl: error instanceof ApiRequestError ? error.requestUrl ?? null : null,
        status: error instanceof ApiRequestError ? error.status ?? null : null,
        statusText: error instanceof ApiRequestError ? error.statusText ?? null : null,
        data: null,
        error: error instanceof Error ? error.message : 'Unexpected API debug error.',
        checkedAt,
      };
    }
  },

  getClientData: async (params?: {
    type?: string;
    search?: string;
    skip?: number;
    limit?: number;
  }): Promise<ClientDataListResponse> => {
    const query = new URLSearchParams();
    if (params?.type) query.set('type', params.type);
    if (params?.search) query.set('search', params.search);
    if (params?.skip != null) query.set('skip', String(params.skip));
    if (params?.limit != null) query.set('limit', String(params.limit));
    const qs = query.toString();
    const response = await requestJson<ClientDataListResponse>(`/client-data${qs ? `?${qs}` : ''}`);
    return response.data;
  },

  createClientData: async (payload: {
    type: string;
    title: string;
    content?: string;
    metadata_?: Record<string, unknown>;
  }): Promise<ClientDataRecord> => {
    const response = await requestJson<ClientDataRecord>('/client-data', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    return response.data;
  },

  updateClientData: async (
    id: string,
    payload: { type?: string; title?: string; content?: string },
  ): Promise<ClientDataRecord> => {
    const response = await requestJson<ClientDataRecord>(`/client-data/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
    return response.data;
  },

  deleteClientData: async (id: string): Promise<void> => {
    await requestJson<unknown>(`/client-data/${id}?confirmed=true`, { method: 'DELETE' });
  },
};
