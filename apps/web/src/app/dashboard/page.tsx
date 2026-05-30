'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  ArrowRight,
  BarChart3,
  Bot,
  Clock,
  DollarSign,
  MessageSquare,
  TrendingUp,
  Users,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { api } from '@/lib/api';
import type { Conversation, CrmStats } from '@/types';

function formatAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60_000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export default function DashboardHomePage() {
  const [stats, setStats] = useState<CrmStats | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const [crmStats, convResult] = await Promise.all([
          api.crm.getStats(),
          api.conversations.list(),
        ]);
        setStats(crmStats);
        setConversations(convResult.items.slice(0, 5));
      } catch {
        // show partial data or empty state gracefully
      } finally {
        setLoading(false);
      }
    };
    void load();
  }, []);

  const kpiCards = [
    {
      label: 'Total Customers',
      value: stats ? String(stats.total_customers) : '—',
      sub: `${stats?.active_customers ?? 0} active`,
      icon: Users,
      color: 'bg-blue-100 text-blue-600',
    },
    {
      label: 'Open Deals',
      value: stats ? String(stats.open_deals ?? stats.deals_in_pipeline) : '—',
      sub: `$${(stats?.pipeline_value ?? stats?.total_mrr ?? 0).toLocaleString()} pipeline`,
      icon: TrendingUp,
      color: 'bg-emerald-100 text-emerald-600',
    },
    {
      label: 'Revenue (Month)',
      value: stats ? `$${(stats.monthly_revenue ?? stats.total_mrr ?? 0).toLocaleString()}` : '—',
      sub: 'invoiced this month',
      icon: DollarSign,
      color: 'bg-violet-100 text-violet-600',
    },
    {
      label: 'Open Tickets',
      value: stats ? String(stats.open_tickets) : '—',
      sub: `${stats?.overdue_tickets ?? stats?.overdue_invoices ?? 0} overdue`,
      icon: Clock,
      color: 'bg-amber-100 text-amber-600',
    },
  ];

  const quickActions = [
    {
      title: 'New Conversation',
      description: 'Start a fresh AI-powered workflow with any agent template.',
      href: '/dashboard/conversations',
      icon: MessageSquare,
    },
    {
      title: 'Explore Dashboards',
      description: 'View your custom analytics and live business metrics.',
      href: '/dashboard/dashboards',
      icon: BarChart3,
    },
    {
      title: 'Agent Library',
      description: 'Browse, configure, and deploy AI agent templates.',
      href: '/dashboard/agent-library',
      icon: Bot,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Welcome banner */}
      <Card className="border-slate-200 bg-gradient-to-br from-slate-950 via-slate-900 to-blue-950 text-white">
        <CardHeader>
          <CardTitle className="text-3xl">Welcome to Velaris AI</CardTitle>
          <CardDescription className="text-slate-300">
            Your unified operations console — manage customers, conversations, agents, and analytics from one place.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-3">
          <Button asChild variant="secondary">
            <Link href="/dashboard/conversations">New conversation</Link>
          </Button>
          <Button asChild variant="outline" className="border-white/20 bg-transparent text-white hover:bg-white/10 hover:text-white">
            <Link href="/dashboard/crm">Open CRM</Link>
          </Button>
        </CardContent>
      </Card>

      {/* KPI cards */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {kpiCards.map((card) => {
          const Icon = card.icon;
          return (
            <Card key={card.label} className="border-slate-200">
              <CardContent className="flex items-center justify-between p-6">
                <div>
                  <p className="text-sm text-slate-500">{card.label}</p>
                  <p className="mt-2 text-3xl font-semibold text-slate-950">
                    {loading ? (
                      <span className="inline-block h-8 w-16 animate-pulse rounded bg-slate-200" />
                    ) : (
                      card.value
                    )}
                  </p>
                  <p className="mt-1 text-xs text-slate-400">{card.sub}</p>
                </div>
                <div className={`rounded-full p-3 ${card.color}`}>
                  <Icon className="h-5 w-5" />
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.5fr,1fr]">
        {/* Quick actions */}
        <Card className="border-slate-200">
          <CardHeader>
            <CardTitle>Quick actions</CardTitle>
            <CardDescription>Jump into the most common operator tasks.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-3">
            {quickActions.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className="rounded-2xl border border-slate-200 p-5 transition hover:border-blue-300 hover:bg-blue-50"
                >
                  <div className="flex items-center justify-between">
                    <div className="rounded-full bg-slate-100 p-3 text-slate-700">
                      <Icon className="h-5 w-5" />
                    </div>
                    <ArrowRight className="h-4 w-4 text-slate-400" />
                  </div>
                  <h3 className="mt-4 font-semibold text-slate-950">{item.title}</h3>
                  <p className="mt-2 text-sm text-slate-500">{item.description}</p>
                </Link>
              );
            })}
          </CardContent>
        </Card>

        {/* Recent conversations */}
        <Card className="border-slate-200">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Recent conversations</CardTitle>
                <CardDescription>Your last 5 active threads.</CardDescription>
              </div>
              <Link href="/dashboard/conversations" className="text-sm font-medium text-blue-600 hover:underline">
                View all
              </Link>
            </div>
          </CardHeader>
          <CardContent className="space-y-2">
            {loading ? (
              Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="h-14 animate-pulse rounded-xl bg-slate-200" />
              ))
            ) : conversations.length > 0 ? (
              conversations.map((conv) => (
                (() => {
                  const status = conv.status ?? 'active';
                  return (
                <Link
                  key={conv.id}
                  href={`/dashboard/conversations/${conv.id}`}
                  className="flex items-center justify-between rounded-xl border border-slate-200 px-4 py-3 transition hover:bg-slate-50"
                >
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium text-slate-900">{conv.title ?? 'Untitled conversation'}</p>
                    <p className="text-xs text-slate-400">{formatAgo(conv.updated_at)}</p>
                  </div>
                  <Badge
                    variant={status === 'active' ? 'default' : 'secondary'}
                    className="ml-3 shrink-0"
                  >
                    {status}
                  </Badge>
                </Link>
                  );
                })()
              ))
            ) : (
              <div className="rounded-xl border border-dashed border-slate-300 p-6 text-sm text-slate-500">
                No conversations yet.{' '}
                <Link href="/dashboard/conversations" className="font-medium text-blue-600 hover:underline">
                  Start one
                </Link>
                .
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
