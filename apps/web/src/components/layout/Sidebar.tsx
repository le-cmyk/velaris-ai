'use client';

import Image from 'next/image';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  BarChart3,
  Bot,
  Clock,
  ClipboardCheck,
  Database,
  Key,
  LayoutDashboard,
  MessageSquare,
  ScrollText,
  Settings,
  Users,
  X,
} from 'lucide-react';

import { getUser } from '@/lib/auth';
import { cn } from '@/lib/utils';

const navSections = [
  {
    label: 'Platform',
    items: [
      { href: '/dashboard', label: 'Overview', icon: LayoutDashboard, exact: true },
      { href: '/dashboard/conversations', label: 'Conversations', icon: MessageSquare },
      { href: '/dashboard/agent-library', label: 'Agent Library', icon: Bot },
      { href: '/dashboard/scheduler', label: 'Scheduler', icon: Clock },
    ],
  },
  {
    label: 'Business Data',
    items: [
      { href: '/dashboard/dashboards', label: 'Dashboards', icon: BarChart3 },
      { href: '/dashboard/crm', label: 'CRM', icon: Users },
      { href: '/dashboard/data', label: 'Data Browser', icon: Database },
    ],
  },
  {
    label: 'Operations',
    items: [
      { href: '/dashboard/approvals', label: 'Approvals', icon: ClipboardCheck },
      { href: '/dashboard/audit-logs', label: 'Audit Logs', icon: ScrollText },
    ],
  },
  {
    label: 'Settings',
    items: [
      { href: '/dashboard/settings', label: 'Settings', icon: Settings },
      { href: '/dashboard/settings/api-keys', label: 'API Keys', icon: Key },
    ],
  },
];

interface SidebarProps {
  mobileOpen?: boolean;
  onClose?: () => void;
}

function SidebarContent({ onClose }: { onClose?: () => void }) {
  const pathname = usePathname();
  const user = getUser();

  const isActive = (href: string, exact = false) => {
    if (exact) return pathname === href;
    return pathname === href || pathname.startsWith(href + '/');
  };

  return (
    <div className="flex h-full flex-col bg-slate-950 px-5 py-6 text-slate-100">
      <div className="flex items-center justify-between">
        <Link
          href="/dashboard"
          onClick={onClose}
          className="flex flex-1 items-center gap-3 rounded-xl border border-slate-800 bg-slate-900/60 px-3 py-3"
        >
          <Image src="/logo.svg" alt="Velaris AI" width={40} height={40} className="rounded-lg" />
          <div>
            <p className="text-sm font-medium text-slate-300">Velaris AI</p>
            <p className="text-lg font-semibold">Operations Console</p>
          </div>
        </Link>
        {onClose && (
          <button
            onClick={onClose}
            className="ml-3 rounded-lg p-2 text-slate-400 hover:bg-slate-800 hover:text-white lg:hidden"
            aria-label="Close menu"
          >
            <X className="h-5 w-5" />
          </button>
        )}
      </div>

      <nav className="mt-8 flex-1 space-y-6 overflow-y-auto">
        {navSections.map((section) => (
          <div key={section.label}>
            <p className="mb-2 px-3 text-xs font-semibold uppercase tracking-widest text-slate-500">
              {section.label}
            </p>
            <div className="space-y-1">
              {section.items.map((item) => {
                const Icon = item.icon;
                const active = isActive(item.href, item.exact);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={onClose}
                    className={cn(
                      'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors',
                      active
                        ? 'bg-blue-500 text-white shadow-lg shadow-blue-500/20'
                        : 'text-slate-300 hover:bg-slate-900 hover:text-white',
                    )}
                  >
                    <Icon className="h-4 w-4" />
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      <div className="mt-4 rounded-xl border border-slate-800 bg-slate-900/70 p-4">
        <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Signed in as</p>
        <p className="mt-2 font-semibold text-white">{user?.full_name ?? 'Velaris User'}</p>
        <p className="text-sm text-slate-400">{user?.email ?? 'demo@velaris.ai'}</p>
      </div>
    </div>
  );
}

export function Sidebar({ mobileOpen = false, onClose }: SidebarProps) {
  return (
    <>
      {/* Desktop sidebar */}
      <aside className="hidden w-64 shrink-0 lg:block">
        <div className="sticky top-0 h-screen">
          <SidebarContent />
        </div>
      </aside>

      {/* Mobile overlay backdrop */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Mobile drawer */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 w-72 transform transition-transform duration-300 ease-in-out lg:hidden',
          mobileOpen ? 'translate-x-0' : '-translate-x-full',
        )}
      >
        <SidebarContent onClose={onClose} />
      </aside>
    </>
  );
}
