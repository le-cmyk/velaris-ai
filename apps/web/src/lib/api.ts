import type {
  AgentTemplate,
  ApiKey,
  AppNotification,
  ApprovalRequest,
  AuditLogEntry,
  ChatResponse,
  ClientDataRecord,
  ClientDataListResponse,
  ClientEndpoint,
  ClientEndpointListResponse,
  ClientEndpointMethod,
  ClientEndpointMode,
  Contact,
  Conversation,
  CrmStats,
  Customer,
  Dashboard,
  DashboardWidget,
  DashboardWithWidgets,
  Deal,
  Invoice,
  ListResponse,
  Message,
  Product,
  ScheduledJob,
  SupportTicket,
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
  access_token?: string;
  token?: string;
  token_type?: string;
  user_id: string;
  workspace_id: string;
  email: string;
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
  return text ? sanitizeBodyPreview(text).slice(0, BODY_PREVIEW_LENGTH) : '(empty)';
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

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

function sanitizeForLogs(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map((entry) => sanitizeForLogs(entry));
  }

  if (!isObject(value)) {
    return value;
  }

  const sanitized: Record<string, unknown> = {};
  const sensitiveKeys = new Set(['password', 'token', 'access_token', 'authorization', 'cookie']);

  for (const [key, keyValue] of Object.entries(value)) {
    sanitized[key] = sensitiveKeys.has(key.toLowerCase()) ? '[REDACTED]' : sanitizeForLogs(keyValue);
  }

  return sanitized;
}

function sanitizeBodyPreview(text: string): string {
  const parsed = parseResponseBody(text);

  if (typeof parsed === 'string') {
    return parsed
      .replace(/("?(?:access_token|token|password|authorization|cookie)"?\s*:\s*)"[^"]*"/gi, '$1"[REDACTED]"')
      .replace(/\b(?:Bearer)\s+[A-Za-z0-9\-._~+/]+=*/gi, '******');
  }

  return JSON.stringify(sanitizeForLogs(parsed));
}

function parseAuthUser(responseData: LoginResponse): User {
  if (!responseData.user_id || !responseData.workspace_id || !responseData.email) {
    throw new Error('Login response is missing required user fields');
  }

  return {
    id: responseData.user_id,
    email: responseData.email,
    workspace_id: responseData.workspace_id,
    full_name: responseData.email.split('@')[0],
  };
}

function parseAuthToken(responseData: LoginResponse): string {
  const token = responseData.access_token ?? responseData.token;

  if (!token) {
    throw new Error('Login response did not include an access token');
  }

  return token;
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
    headers.Authorization = 'Bearer ' + token;
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

    // Auto-clear auth and redirect to login on 401
    if (response.status === 401 && typeof window !== 'undefined') {
      localStorage.removeItem('velaris_token');
      localStorage.removeItem('velaris_user');
      window.location.href = '/login';
    }

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
    return { token: parseAuthToken(response.data), user: parseAuthUser(response.data) };
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
    return { token: parseAuthToken(response.data), user: parseAuthUser(response.data) };
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

  clientEndpoints: {
    list: async (): Promise<ClientEndpointListResponse> => {
      const response = await requestJson<ClientEndpointListResponse>('/backend/endpoints');
      return response.data;
    },
    create: async (data: {
      name: string;
      method: ClientEndpointMethod;
      path: string;
      mode: ClientEndpointMode;
      description?: string;
      config?: Record<string, unknown>;
      is_active?: boolean;
    }): Promise<ClientEndpoint> => {
      const response = await requestJson<ClientEndpoint>('/backend/endpoints', {
        method: 'POST',
        body: JSON.stringify(data),
      });
      return response.data;
    },
    update: async (
      id: string,
      data: { name?: string; description?: string; config?: Record<string, unknown>; is_active?: boolean },
    ): Promise<ClientEndpoint> => {
      const response = await requestJson<ClientEndpoint>(`/backend/endpoints/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      });
      return response.data;
    },
    execute: async (
      endpoint: Pick<ClientEndpoint, 'method' | 'path'>,
      options: { query?: string; body?: string } = {},
    ): Promise<unknown> => {
      const suffix = options.query?.trim() ? `?${options.query.trim().replace(/^\?/, '')}` : '';
      const response = await requestJson<unknown>(`/client-api${endpoint.path}${suffix}`, {
        method: endpoint.method,
        body: ['GET', 'DELETE'].includes(endpoint.method) ? undefined : options.body || '{}',
      });
      return response.data;
    },
  },

  // Conversations
  conversations: {
    list: async (): Promise<ListResponse<Conversation>> => {
      const response = await requestJson<ListResponse<Conversation>>('/conversations');
      return response.data;
    },
    create: async (data: { title?: string; agent_template_id?: string }): Promise<Conversation> => {
      const response = await requestJson<Conversation>('/conversations', {
        method: 'POST',
        body: JSON.stringify(data),
      });
      return response.data;
    },
    get: async (id: string): Promise<Conversation> => {
      const response = await requestJson<Conversation>(`/conversations/${id}`);
      return response.data;
    },
    delete: async (id: string): Promise<void> => {
      await requestJson<unknown>(`/conversations/${id}`, { method: 'DELETE' });
    },
    getMessages: async (id: string): Promise<ListResponse<Message>> => {
      const response = await requestJson<ListResponse<Message>>(`/conversations/${id}/messages`);
      return response.data;
    },
    sendMessage: async (id: string, content: string, workspaceId: string): Promise<{ message: Message; response: Message }> => {
      const response = await requestJson<{ message: Message; response: Message }>(`/conversations/${id}/messages`, {
        method: 'POST',
        body: JSON.stringify({ content, workspace_id: workspaceId }),
      });
      return response.data;
    },
  },

  // Agent Library
  agentLibrary: {
    list: async (): Promise<ListResponse<AgentTemplate>> => {
      const response = await requestJson<ListResponse<AgentTemplate>>('/agent-templates');
      return response.data;
    },
    create: async (data: Partial<AgentTemplate>): Promise<AgentTemplate> => {
      const response = await requestJson<AgentTemplate>('/agent-templates', {
        method: 'POST',
        body: JSON.stringify(data),
      });
      return response.data;
    },
    update: async (id: string, data: Partial<AgentTemplate>): Promise<AgentTemplate> => {
      const response = await requestJson<AgentTemplate>(`/agent-templates/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      });
      return response.data;
    },
    delete: async (id: string): Promise<void> => {
      await requestJson<unknown>(`/agent-templates/${id}`, { method: 'DELETE' });
    },
  },

  // Schedules
  schedules: {
    list: async (): Promise<ListResponse<ScheduledJob>> => {
      const response = await requestJson<ListResponse<ScheduledJob>>('/scheduled-jobs');
      return response.data;
    },
    create: async (data: Partial<ScheduledJob>): Promise<ScheduledJob> => {
      const response = await requestJson<ScheduledJob>('/scheduled-jobs', {
        method: 'POST',
        body: JSON.stringify(data),
      });
      return response.data;
    },
    update: async (id: string, data: Partial<ScheduledJob>): Promise<ScheduledJob> => {
      const response = await requestJson<ScheduledJob>(`/scheduled-jobs/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      });
      return response.data;
    },
    delete: async (id: string): Promise<void> => {
      await requestJson<unknown>(`/scheduled-jobs/${id}`, { method: 'DELETE' });
    },
    trigger: async (id: string): Promise<{ run_id: string; status: string }> => {
      const response = await requestJson<{ run_id: string; status: string }>(`/scheduled-jobs/${id}/trigger`, {
        method: 'POST',
      });
      return response.data;
    },
    toggle: async (id: string): Promise<ScheduledJob> => {
      const response = await requestJson<ScheduledJob>(`/scheduled-jobs/${id}/toggle`, {
        method: 'POST',
      });
      return response.data;
    },
  },

  // Dashboards
  dashboards: {
    list: async (): Promise<ListResponse<Dashboard>> => {
      const response = await requestJson<ListResponse<Dashboard>>('/dashboards');
      return response.data;
    },
    create: async (data: { name: string; description?: string }): Promise<Dashboard> => {
      const response = await requestJson<Dashboard>('/dashboards', {
        method: 'POST',
        body: JSON.stringify(data),
      });
      return response.data;
    },
    get: async (id: string): Promise<DashboardWithWidgets> => {
      const response = await requestJson<DashboardWithWidgets>(`/dashboards/${id}`);
      return response.data;
    },
    update: async (id: string, data: Partial<Dashboard>): Promise<Dashboard> => {
      const response = await requestJson<Dashboard>(`/dashboards/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      });
      return response.data;
    },
    addWidget: async (dashboardId: string, data: Partial<DashboardWidget>): Promise<DashboardWidget> => {
      const response = await requestJson<DashboardWidget>(`/dashboards/${dashboardId}/widgets`, {
        method: 'POST',
        body: JSON.stringify(data),
      });
      return response.data;
    },
    updateWidget: async (dashboardId: string, widgetId: string, data: Partial<DashboardWidget>): Promise<DashboardWidget> => {
      const response = await requestJson<DashboardWidget>(`/dashboards/${dashboardId}/widgets/${widgetId}`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      });
      return response.data;
    },
    deleteWidget: async (dashboardId: string, widgetId: string): Promise<void> => {
      await requestJson<unknown>(`/dashboards/${dashboardId}/widgets/${widgetId}`, { method: 'DELETE' });
    },
    getWidgetData: async (dashboardId: string, widgetId: string): Promise<{ data: unknown; widget_type: string }> => {
      const response = await requestJson<{ data: unknown; widget_type: string }>(
        `/dashboards/${dashboardId}/widgets/${widgetId}/data`,
      );
      return response.data;
    },
  },

  // CRM
  crm: {
    getStats: async (): Promise<CrmStats> => {
      const response = await requestJson<CrmStats>('/crm/stats');
      return response.data;
    },
    listCustomers: async (params?: { skip?: number; limit?: number; status?: string; tier?: string; search?: string }): Promise<ListResponse<Customer>> => {
      const query = new URLSearchParams();
      if (params?.skip != null) query.set('skip', String(params.skip));
      if (params?.limit != null) query.set('limit', String(params.limit));
      if (params?.status) query.set('status', params.status);
      if (params?.tier) query.set('tier', params.tier);
      if (params?.search) query.set('search', params.search);
      const qs = query.toString();
      const response = await requestJson<ListResponse<Customer>>(`/crm/customers${qs ? `?${qs}` : ''}`);
      return response.data;
    },
    createCustomer: async (data: Partial<Customer>): Promise<Customer> => {
      const response = await requestJson<Customer>('/crm/customers', {
        method: 'POST',
        body: JSON.stringify(data),
      });
      return response.data;
    },
    updateCustomer: async (id: string, data: Partial<Customer>): Promise<Customer> => {
      const response = await requestJson<Customer>(`/crm/customers/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      });
      return response.data;
    },
    deleteCustomer: async (id: string): Promise<void> => {
      await requestJson<unknown>(`/crm/customers/${id}`, { method: 'DELETE' });
    },
    listContacts: async (params?: { customer_id?: string; search?: string }): Promise<ListResponse<Contact>> => {
      const query = new URLSearchParams();
      if (params?.customer_id) query.set('customer_id', params.customer_id);
      if (params?.search) query.set('search', params.search);
      const qs = query.toString();
      const response = await requestJson<ListResponse<Contact>>(`/crm/contacts${qs ? `?${qs}` : ''}`);
      return response.data;
    },
    createContact: async (data: Partial<Contact>): Promise<Contact> => {
      const response = await requestJson<Contact>('/crm/contacts', {
        method: 'POST',
        body: JSON.stringify(data),
      });
      return response.data;
    },
    listDeals: async (params?: { stage?: string; customer_id?: string }): Promise<ListResponse<Deal>> => {
      const query = new URLSearchParams();
      if (params?.stage) query.set('stage', params.stage);
      if (params?.customer_id) query.set('customer_id', params.customer_id);
      const qs = query.toString();
      const response = await requestJson<ListResponse<Deal>>(`/crm/deals${qs ? `?${qs}` : ''}`);
      return response.data;
    },
    createDeal: async (data: Partial<Deal>): Promise<Deal> => {
      const response = await requestJson<Deal>('/crm/deals', {
        method: 'POST',
        body: JSON.stringify(data),
      });
      return response.data;
    },
    updateDeal: async (id: string, data: Partial<Deal>): Promise<Deal> => {
      const response = await requestJson<Deal>(`/crm/deals/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      });
      return response.data;
    },
    listInvoices: async (params?: { status?: string; customer_id?: string }): Promise<ListResponse<Invoice>> => {
      const query = new URLSearchParams();
      if (params?.status) query.set('status', params.status);
      if (params?.customer_id) query.set('customer_id', params.customer_id);
      const qs = query.toString();
      const response = await requestJson<ListResponse<Invoice>>(`/crm/invoices${qs ? `?${qs}` : ''}`);
      return response.data;
    },
    createInvoice: async (data: Partial<Invoice>): Promise<Invoice> => {
      const response = await requestJson<Invoice>('/crm/invoices', {
        method: 'POST',
        body: JSON.stringify(data),
      });
      return response.data;
    },
    updateInvoice: async (id: string, data: Partial<Invoice>): Promise<Invoice> => {
      const response = await requestJson<Invoice>(`/crm/invoices/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      });
      return response.data;
    },
    listTickets: async (params?: { status?: string; priority?: string; customer_id?: string }): Promise<ListResponse<SupportTicket>> => {
      const query = new URLSearchParams();
      if (params?.status) query.set('status', params.status);
      if (params?.priority) query.set('priority', params.priority);
      if (params?.customer_id) query.set('customer_id', params.customer_id);
      const qs = query.toString();
      const response = await requestJson<ListResponse<SupportTicket>>(`/crm/tickets${qs ? `?${qs}` : ''}`);
      return response.data;
    },
    createTicket: async (data: Partial<SupportTicket>): Promise<SupportTicket> => {
      const response = await requestJson<SupportTicket>('/crm/tickets', {
        method: 'POST',
        body: JSON.stringify(data),
      });
      return response.data;
    },
    updateTicket: async (id: string, data: Partial<SupportTicket>): Promise<SupportTicket> => {
      const response = await requestJson<SupportTicket>(`/crm/tickets/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      });
      return response.data;
    },
    listProducts: async (): Promise<ListResponse<Product>> => {
      const response = await requestJson<ListResponse<Product>>('/crm/products');
      return response.data;
    },
    createProduct: async (data: Partial<Product>): Promise<Product> => {
      const response = await requestJson<Product>('/crm/products', {
        method: 'POST',
        body: JSON.stringify(data),
      });
      return response.data;
    },
  },

  // Notifications
  notifications: {
    list: async (params?: { is_read?: boolean; limit?: number }): Promise<ListResponse<AppNotification>> => {
      const query = new URLSearchParams();
      if (params?.is_read != null) query.set('is_read', String(params.is_read));
      if (params?.limit != null) query.set('limit', String(params.limit));
      const qs = query.toString();
      const response = await requestJson<ListResponse<AppNotification>>(`/notifications${qs ? `?${qs}` : ''}`);
      return response.data;
    },
    getUnreadCount: async (): Promise<{ count: number }> => {
      const response = await requestJson<{ count: number }>('/notifications/unread-count');
      return response.data;
    },
    markRead: async (id: string): Promise<AppNotification> => {
      const response = await requestJson<AppNotification>(`/notifications/${id}/read`, { method: 'POST' });
      return response.data;
    },
    markAllRead: async (): Promise<void> => {
      await requestJson<unknown>('/notifications/read-all', { method: 'POST' });
    },
  },

  // API Keys
  apiKeys: {
    list: async (): Promise<ListResponse<ApiKey>> => {
      const response = await requestJson<ListResponse<ApiKey>>('/api-keys');
      return response.data;
    },
    create: async (data: { name: string; scopes?: string[] }): Promise<ApiKey> => {
      const response = await requestJson<ApiKey>('/api-keys', {
        method: 'POST',
        body: JSON.stringify(data),
      });
      return response.data;
    },
    delete: async (id: string): Promise<void> => {
      await requestJson<unknown>(`/api-keys/${id}`, { method: 'DELETE' });
    },
  },
};
