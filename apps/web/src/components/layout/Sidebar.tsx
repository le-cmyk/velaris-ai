'use client';

import Image from 'next/image';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Bot, ClipboardCheck, LayoutDashboard, ScrollText, Settings } from 'lucide-react';

import { getUser } from '@/lib/auth';
import { cn } from '@/lib/utils';

const navigation = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/dashboard/chat', label: 'Chat', icon: Bot },
  { href: '/dashboard/approvals', label: 'Approvals', icon: ClipboardCheck },
  { href: '/dashboard/audit-logs', label: 'Audit Logs', icon: ScrollText },
  { href: '/dashboard/settings', label: 'Settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const user = getUser();

  return (
    <aside className="hidden w-72 shrink-0 flex-col bg-slate-950 px-5 py-6 text-slate-100 lg:flex">
      <Link href="/dashboard" className="flex items-center gap-3 rounded-xl border border-slate-800 bg-slate-900/60 px-3 py-3">
        <Image src="/logo.svg" alt="Velaris AI" width={40} height={40} className="rounded-lg" />
        <div>
          <p className="text-sm font-medium text-slate-300">Velaris AI</p>
          <p className="text-lg font-semibold">Operations Console</p>
        </div>
      </Link>

      <nav className="mt-8 space-y-2">
        {navigation.map((item) => {
          const Icon = item.icon;
          const active = pathname === item.href;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors',
                active ? 'bg-blue-500 text-white shadow-lg shadow-blue-500/20' : 'text-slate-300 hover:bg-slate-900 hover:text-white',
              )}
            >
              <Icon className="h-4 w-4" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto rounded-xl border border-slate-800 bg-slate-900/70 p-4">
        <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Signed in as</p>
        <p className="mt-2 font-semibold text-white">{user?.full_name ?? 'Velaris User'}</p>
        <p className="text-sm text-slate-400">{user?.email ?? 'demo@velaris.ai'}</p>
      </div>
    </aside>
  );
}
