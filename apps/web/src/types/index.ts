export interface User {
  id: string;
  email: string;
  full_name: string;
  workspace_id: string;
}

export interface AuthState {
  token: string | null;
  user: User | null;
}

export interface ToolCallResult {
  tool_name: string;
  arguments: Record<string, unknown>;
  status:
    | 'pending'
    | 'approved'
    | 'rejected'
    | 'executed'
    | 'failed'
    | 'blocked'
    | 'pending_approval';
  result: unknown | null;
  requires_approval: boolean;
}

export interface ChatResponse {
  run_id: string;
  message: string;
  intent: string;
  execution_plan: Record<string, unknown> | null;
  tool_calls: ToolCallResult[];
  pending_approvals: ApprovalRequest[];
  status: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  chatResponse?: ChatResponse;
}

export interface ApprovalRequest {
  id: string;
  run_id: string;
  tool_call_id: string;
  requested_action: string;
  reason: string | null;
  status: 'pending' | 'approved' | 'rejected';
  created_at: string;
}

export interface AuditLogEntry {
  id: string;
  action: string;
  resource_type: string;
  resource_id: string | null;
  details: Record<string, unknown> | null;
  created_at: string;
}

export interface ToolInfo {
  name: string;
  description: string;
  requires_approval: boolean;
  enabled: boolean;
}

export interface WorkspaceInfo {
  id: string;
  name: string;
  slug?: string;
}

export interface ClientDataRecord {
  id: string;
  workspace_id: string;
  type: string;
  title: string;
  content: string | null;
  metadata_: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface ClientDataListResponse {
  items: ClientDataRecord[];
  total: number;
}

