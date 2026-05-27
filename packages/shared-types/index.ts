// Shared TypeScript types for Velaris AI
// Used by both frontend and future TypeScript services

export type Intent = 
  | 'database_read'
  | 'database_write_request'
  | 'summarize_data'
  | 'unknown';

export type ToolCallStatus = 
  | 'pending'
  | 'approved'
  | 'rejected'
  | 'executed'
  | 'failed'
  | 'blocked'
  | 'pending_approval';

export type ApprovalStatus = 'pending' | 'approved' | 'rejected';

export type RunStatus = 'pending' | 'running' | 'completed' | 'failed';

export interface ToolCall {
  id: string;
  run_id: string;
  workspace_id: string;
  tool_name: string;
  arguments: Record<string, unknown>;
  status: ToolCallStatus;
  result: unknown | null;
  error: string | null;
  requires_approval: boolean;
  created_at: string;
}

export interface AgentRun {
  id: string;
  workspace_id: string;
  user_id: string;
  status: RunStatus;
  intent: Intent | null;
  input_message: string;
  output_message: string | null;
  execution_plan: string[] | null;
  created_at: string;
}
