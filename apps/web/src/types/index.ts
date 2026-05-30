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

export interface ChatMessage {
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

// ── CRM ──────────────────────────────────────────────────────────────────────
export interface Customer {
  id: string
  workspace_id: string
  name: string
  email?: string
  phone?: string
  company?: string
  status: 'prospect' | 'active' | 'churned' | 'at_risk'
  tier?: 'free' | 'starter' | 'pro' | 'enterprise'
  mrr: number
  churn_risk_score?: number
  industry?: string
  country?: string
  tags: string[]
  notes?: string
  last_contact_at?: string
  created_at: string
  updated_at: string
}

export interface Contact {
  id: string
  workspace_id: string
  customer_id?: string
  name: string
  email?: string
  phone?: string
  role?: string
  linkedin_url?: string
  is_primary: boolean
  last_contact_at?: string
  notes?: string
  created_at: string
  updated_at: string
}

export interface Deal {
  id: string
  workspace_id: string
  customer_id?: string
  name: string
  value: number
  currency: string
  stage: 'discovery' | 'proposal' | 'negotiation' | 'closed_won' | 'closed_lost'
  probability: number
  close_date?: string
  owner?: string
  notes?: string
  tags: string[]
  created_at: string
  updated_at: string
}

export interface InvoiceLineItem {
  description: string
  quantity: number
  unit_price: number
  total: number
}

export interface Invoice {
  id: string
  workspace_id: string
  customer_id?: string
  invoice_number: string
  amount: number
  currency: string
  status: 'draft' | 'sent' | 'paid' | 'overdue' | 'cancelled'
  due_date?: string
  paid_at?: string
  line_items: InvoiceLineItem[]
  notes?: string
  created_at: string
  updated_at: string
}

export interface SupportTicket {
  id: string
  workspace_id: string
  customer_id?: string
  ticket_number: string
  subject: string
  body?: string
  status: 'open' | 'in_progress' | 'waiting' | 'resolved' | 'closed'
  priority: 'low' | 'medium' | 'high' | 'critical'
  assignee?: string
  tags: string[]
  resolved_at?: string
  satisfaction_score?: number
  created_at: string
  updated_at: string
}

export interface Task {
  id: string
  workspace_id: string
  title: string
  description?: string
  status: 'todo' | 'in_progress' | 'done' | 'cancelled'
  priority: 'low' | 'medium' | 'high' | 'critical'
  due_date?: string
  assignee?: string
  parent_id?: string
  linked_entity_type?: string
  linked_entity_id?: string
  tags: string[]
  created_at: string
  updated_at: string
}

export interface Product {
  id: string
  workspace_id: string
  name: string
  sku?: string
  description?: string
  price: number
  category?: string
  inventory_count: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface CrmStats {
  total_customers: number
  active_customers: number
  total_mrr: number
  open_tickets: number
  deals_in_pipeline: number
  overdue_invoices: number
  open_deals?: number
  pipeline_value?: number
  monthly_revenue?: number
  overdue_tickets?: number
}

// ── Platform ──────────────────────────────────────────────────────────────────
export interface Conversation {
  id: string
  workspace_id: string
  user_id?: string
  title: string
  status?: string
  agent_template_id?: string
  message_count: number
  last_message_at?: string
  created_at: string
  updated_at: string
}

export interface Message {
  id: string
  workspace_id: string
  conversation_id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  agent_run_id?: string
  metadata?: Record<string, unknown>
  created_at: string
}

export interface AgentTemplate {
  id: string
  workspace_id: string
  name: string
  description?: string
  icon: string
  category: 'crm' | 'finance' | 'support' | 'operations' | 'analytics' | 'general'
  system_prompt: string
  allowed_tools: string[]
  is_active: boolean
  is_builtin: boolean
  created_by_id?: string
  version: number
  created_at: string
  updated_at: string
}

export interface ScheduledJob {
  id: string
  workspace_id: string
  name: string
  description?: string
  agent_template_id?: string
  message: string
  cron_expr?: string
  interval_minutes?: number
  is_active: boolean
  last_run_at?: string
  last_run_status?: 'success' | 'failed' | 'running'
  last_run_error?: string
  next_run_at?: string
  run_count: number
  created_at: string
  updated_at: string
}

export interface Dashboard {
  id: string
  workspace_id: string
  name: string
  description?: string
  is_default: boolean
  created_by_id?: string
  created_at: string
  updated_at: string
}

export interface DashboardWidget {
  id: string
  workspace_id: string
  dashboard_id: string
  title: string
  widget_type: 'metric' | 'table' | 'bar_chart' | 'line_chart' | 'pie_chart' | 'kpi_row' | 'agent_output'
  data_source: 'query' | 'agent' | 'static'
  query?: string
  config: Record<string, unknown>
  position_x: number
  position_y: number
  width: number
  height: number
  refresh_seconds?: number
  last_data?: unknown
  last_refreshed_at?: string
  created_at: string
  updated_at: string
}

export interface DashboardWithWidgets extends Dashboard {
  widgets: DashboardWidget[]
}

export interface AppNotification {
  id: string
  workspace_id: string
  user_id?: string
  type: 'agent_complete' | 'approval_needed' | 'job_failed' | 'info' | 'warning'
  title: string
  body?: string
  is_read: boolean
  linked_entity_type?: string
  linked_entity_id?: string
  created_at: string
}

export interface ApiKey {
  id: string
  workspace_id: string
  user_id?: string
  name: string
  key_prefix: string
  scopes: string[]
  is_active: boolean
  last_used_at?: string
  expires_at?: string
  created_at: string
  plain_key?: string
}

export interface ListResponse<T> {
  items: T[]
  total: number
}
