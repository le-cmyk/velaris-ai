'use client';

import { useMemo } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { LogOut } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { clearAuth, getUser } from '@/lib/auth';

const titles: Record<string, { title: string; subtitle: string }> = {
  '/dashboard': {
    title: 'Workspace overview',
    subtitle: 'Monitor agent activity, approvals, and key workspace metrics.',
  },
  '/dashboard/chat': {
    title: 'Agent chat',
    subtitle: 'Run tasks through the Velaris orchestration engine.',
  },
  '/dashboard/approvals': {
    title: 'Approval queue',
    subtitle: 'Review actions that require a human decision before execution.',
  },
  '/dashboard/audit-logs': {
    title: 'Audit trail',
    subtitle: 'Track every action performed across the workspace.',
  },
  '/dashboard/settings': {
    title: 'Settings',
    subtitle: 'Inspect workspace details, user access, and connected tools.',
  },
};

export function Header() {
  const pathname = usePathname();
  const router = useRouter();
  const user = getUser();

  const content = useMemo(() => titles[pathname] ?? titles['/dashboard'], [pathname]);

  const handleLogout = () => {
    clearAuth();
    router.push('/login');
  };

  return (
    <header className="border-b bg-white/80 backdrop-blur">
      <div className="flex flex-col gap-4 px-6 py-5 sm:flex-row sm:items-center sm:justify-between lg:px-8">
        <div>
          <h1 className="text-2xl font-semibold text-slate-950">{content.title}</h1>
          <p className="text-sm text-slate-500">{content.subtitle}</p>
        </div>

        <div className="flex items-center gap-3">
          <div className="rounded-xl border bg-slate-50 px-4 py-2 text-right">
            <p className="text-sm font-medium text-slate-900">{user?.full_name ?? 'Velaris User'}</p>
            <p className="text-xs text-slate-500">{user?.email ?? 'demo@velaris.ai'}</p>
          </div>
          <Button variant="outline" onClick={handleLogout} className="gap-2">
            <LogOut className="h-4 w-4" />
            Logout
          </Button>
        </div>
      </div>
    </header>
  );
}
