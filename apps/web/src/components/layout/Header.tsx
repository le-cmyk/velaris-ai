'use client';

import { useMemo } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { LogOut, Menu } from 'lucide-react';

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

interface HeaderProps {
  onMenuClick?: () => void;
}

export function Header({ onMenuClick }: HeaderProps) {
  const pathname = usePathname();
  const router = useRouter();
  const user = getUser();

  const content = useMemo(() => titles[pathname] ?? titles['/dashboard'], [pathname]);

  const handleLogout = () => {
    clearAuth();
    router.push('/login');
  };

  return (
    <header className="sticky top-0 z-30 border-b bg-white/80 backdrop-blur">
      <div className="flex items-center gap-3 px-4 py-4 sm:px-6 lg:px-8">
        {/* Hamburger — mobile only */}
        <button
          onClick={onMenuClick}
          className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-900 lg:hidden"
          aria-label="Open menu"
        >
          <Menu className="h-5 w-5" />
        </button>

        {/* Title — grows to fill space */}
        <div className="min-w-0 flex-1">
          <h1 className="truncate text-lg font-semibold text-slate-950 sm:text-2xl">{content.title}</h1>
          <p className="hidden text-sm text-slate-500 sm:block">{content.subtitle}</p>
        </div>

        {/* User info + logout */}
        <div className="flex shrink-0 items-center gap-2 sm:gap-3">
          <div className="hidden rounded-xl border bg-slate-50 px-4 py-2 text-right sm:block">
            <p className="text-sm font-medium text-slate-900">{user?.full_name ?? 'Velaris User'}</p>
            <p className="text-xs text-slate-500">{user?.email ?? 'demo@velaris.ai'}</p>
          </div>
          <Button variant="outline" onClick={handleLogout} className="gap-2" size="sm">
            <LogOut className="h-4 w-4" />
            <span className="hidden sm:inline">Logout</span>
          </Button>
        </div>
      </div>
    </header>
  );
}
