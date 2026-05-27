import type {
  ApprovalRequest,
  AuditLogEntry,
  ChatResponse,
  ToolInfo,
  User,
  WorkspaceInfo,
} from '@/types';

const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? '').replace(/\/$/, '');

function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('velaris_token');
}

async function parseResponse<T>(response: Response): Promise<T> {
  const text = await response.text();
  let data: unknown = null;

  if (text) {
    try {
      data = JSON.parse(text) as unknown;
    } catch {
      data = text;
    }
  }

  if (!response.ok) {
    const message =
      typeof data === 'object' && data !== null && 'detail' in data
        ? String((data as { detail: unknown }).detail)
        : 'Request failed';
    throw new Error(message);
  }

  return data as T;
}

async function fetchWithAuth(path: string, options: RequestInit = {}): Promise<Response> {
  if (!API_URL) {
    throw new Error('NEXT_PUBLIC_API_URL is not configured.');
  }
  const token = getToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...((options.headers as Record<string, string> | undefined) ?? {}),
  };

  if (token) {
    headers.Authorization = 'Bearer ' + token;
  }

  return fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  });
}

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

export const api = {
  login: async (email: string, password: string): Promise<{ token: string; user: User }> => {
    const response = await fetchWithAuth('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    const data = await parseResponse<LoginResponse>(response);
    const token = data.access_token ?? data.token;

    if (!token) {
      throw new Error('Login response did not include a token');
    }

    return { token, user: data.user };
  },

  sendMessage: async (message: string, workspace_id: string): Promise<ChatResponse> => {
    const response = await fetchWithAuth('/chat', {
      method: 'POST',
      body: JSON.stringify({ message, workspace_id }),
    });
    return parseResponse<ChatResponse>(response);
  },

  getApprovals: async (): Promise<ApprovalRequest[]> => {
    const response = await fetchWithAuth('/approvals');
    return parseResponse<ApprovalRequest[]>(response);
  },

  approveAction: async (approvalId: string): Promise<ApprovalActionResponse> => {
    const response = await fetchWithAuth(`/approvals/${approvalId}/approve`, {
      method: 'POST',
      body: JSON.stringify({ decision: 'approve' }),
    });
    return parseResponse<ApprovalActionResponse>(response);
  },

  rejectAction: async (approvalId: string): Promise<ApprovalActionResponse> => {
    const response = await fetchWithAuth(`/approvals/${approvalId}/reject`, {
      method: 'POST',
      body: JSON.stringify({ decision: 'reject' }),
    });
    return parseResponse<ApprovalActionResponse>(response);
  },

  getAuditLogs: async (): Promise<AuditLogEntry[]> => {
    const response = await fetchWithAuth('/audit-logs');
    const payload = await parseResponse<AuditLogsResponse>(response);
    return payload.items;
  },

  getTools: async (): Promise<ToolInfo[]> => {
    const response = await fetchWithAuth('/tools');
    return parseResponse<ToolInfo[]>(response);
  },

  getWorkspace: async (): Promise<WorkspaceInfo> => {
    const response = await fetchWithAuth('/workspace');
    return parseResponse<WorkspaceInfo>(response);
  },
};
