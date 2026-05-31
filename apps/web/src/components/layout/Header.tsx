'use client';

import { useEffect, useMemo, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { Bell, LogOut, Menu } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { clearAuth, getUser } from '@/lib/auth';
import { api } from '@/lib/api';

const titles: Record<string, { title: string; subtitle: string }> = {
  '/dashboard': {
    title: 'Workspace overview',
    subtitle: 'Monitor agent activity, approvals, and key workspace metrics.',
  },
  '/dashboard/conversations': {
    title: 'Conversations',
    subtitle: 'Manage and continue AI-powered conversations.',
  },
  '/dashboard/routes': {
    title: 'Routes',
    subtitle: 'Create, inspect, authenticate, and test agent-backed API routes.',
  },
  '/dashboard/agent-library': {
    title: 'Agent Library',
    subtitle: 'Browse, configure, and deploy AI agent templates.',
  },
  '/dashboard/scheduler': {
    title: 'Scheduler',
    subtitle: 'Automate recurring tasks with scheduled jobs.',
  },
  '/dashboard/dashboards': {
    title: 'Dashboards',
    subtitle: 'Build custom analytics and reporting dashboards.',
  },
  '/dashboard/crm': {
    title: 'CRM',
    subtitle: 'Manage customers, deals, invoices, and support tickets.',
  },
  '/dashboard/data': {
    title: 'Data Browser',
    subtitle: 'Explore and manage structured workspace data.',
  },
  '/dashboard/approvals': {
    title: 'Approval queue',
    subtitle: 'Review actions that require a human decision before execution.',
  },
  '/dashboard/audit-logs': {
    title: 'Audit trail',
    subtitle: 'Track every action performed across the workspace.',
  },
  '/dashboard/notifications': {
    title: 'Notifications',
    subtitle: 'Stay up to date with system and workspace events.',
  },
  '/dashboard/settings': {
    title: 'Settings',
    subtitle: 'Inspect workspace details, user access, and connected tools.',
  },
  '/dashboard/settings/api-keys': {
    title: 'API Keys',
    subtitle: 'Generate and manage API keys for programmatic access.',
  },
};

interface HeaderProps {
  onMenuClick?: () => void;
}

export function Header({ onMenuClick }: HeaderProps) {
  const pathname = usePathname();
  const router = useRouter();
  const user = getUser();
  const [unreadCount, setUnreadCount] = useState(0);

  const content = useMemo(() => {
    // Try exact match first, then prefix match for dynamic routes
    if (titles[pathname]) return titles[pathname];
    const parent = Object.keys(titles)
      .filter((k) => k !== '/dashboard' && pathname.startsWith(k + '/'))
      .sort((a, b) => b.length - a.length)[0];
    return parent ? titles[parent] : titles['/dashboard'];
  }, [pathname]);

  useEffect(() => {
    let cancelled = false;

    const fetchCount = async () => {
      try {
        const result = await api.notifications.getUnreadCount();
        if (!cancelled) setUnreadCount(result.count);
      } catch {
        // Fail silently — notification count is non-critical
      }
    };

    fetchCount();
    const interval = setInterval(fetchCount, 30_000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

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

        {/* Notifications bell */}
        <button
          onClick={() => router.push('/dashboard/notifications')}
          className="relative rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-900"
          aria-label="Notifications"
        >
          <Bell className="h-5 w-5" />
          {unreadCount > 0 && (
            <span className="absolute right-1 top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white">
              {unreadCount > 99 ? '99+' : unreadCount}
            </span>
          )}
        </button>

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
