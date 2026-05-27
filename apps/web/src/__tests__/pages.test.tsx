import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import AuditLogsPage from '@/app/dashboard/audit-logs/page';
import ApprovalsPage from '@/app/dashboard/approvals/page';
import DashboardHomePage from '@/app/dashboard/page';
import LoginPage from '@/app/login/page';
import { ChatInterface } from '@/components/chat/ChatInterface';

const push = jest.fn();
const replace = jest.fn();

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push, replace }),
}));

jest.mock('@/lib/auth', () => ({
  isAuthenticated: jest.fn(() => false),
  saveToken: jest.fn(),
  saveUser: jest.fn(),
  getUser: jest.fn(() => ({ workspace_id: 'workspace-1' })),
}));

jest.mock('@/lib/api', () => ({
  api: {
    getWorkspace: jest.fn(async () => ({ id: 'workspace-1', name: 'Demo Workspace' })),
    getApprovals: jest.fn(async () => []),
    getAuditLogs: jest.fn(async () => []),
    sendMessage: jest.fn(async () => ({
      run_id: 'run-1',
      message: 'ok',
      intent: 'database_read',
      execution_plan: null,
      tool_calls: [],
      pending_approvals: [],
      status: 'completed',
    })),
  },
}));

describe('frontend page rendering', () => {
  it('Login page renders', () => {
    render(<LoginPage />);
    expect(screen.getByText('Welcome back')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in to workspace/i })).toBeInTheDocument();
  });

  it('Dashboard renders', async () => {
    render(<DashboardHomePage />);
    await waitFor(() => expect(screen.getByText(/Welcome to Demo Workspace/i)).toBeInTheDocument());
  });

  it('Chat input works', async () => {
    const user = userEvent.setup();
    render(<ChatInterface />);
    const input = screen.getByPlaceholderText(/Ask Velaris AI/i);
    await user.type(input, 'hello world');
    expect(input).toHaveValue('hello world');
  });

  it('Approval panel renders', async () => {
    render(<ApprovalsPage />);
    await waitFor(() => expect(screen.getByText(/There are no pending approvals/i)).toBeInTheDocument());
  });

  it('Audit logs page renders', async () => {
    render(<AuditLogsPage />);
    await waitFor(() => expect(screen.getByText(/No audit log entries are available yet/i)).toBeInTheDocument());
  });
});
