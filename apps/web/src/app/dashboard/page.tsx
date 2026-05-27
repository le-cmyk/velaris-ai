'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { ArrowRight, Bot, ClipboardCheck, Loader2, PlayCircle, Wrench } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { api } from '@/lib/api';
import type { ApprovalRequest, WorkspaceInfo } from '@/types';

const stats = [
  { label: 'Active runs', value: '14', icon: PlayCircle },
  { label: 'Pending approvals', value: '0', icon: ClipboardCheck },
  { label: 'Tool calls today', value: '182', icon: Wrench },
];

export default function DashboardHomePage() {
  const [workspace, setWorkspace] = useState<WorkspaceInfo | null>(null);
  const [approvals, setApprovals] = useState<ApprovalRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const [workspaceResult, approvalsResult] = await Promise.all([api.getWorkspace(), api.getApprovals()]);
        setWorkspace(workspaceResult);
        setApprovals(approvalsResult);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unable to load dashboard data.');
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, []);

  const overviewStats = stats.map((stat) =>
    stat.label === 'Pending approvals' ? { ...stat, value: String(approvals.filter((item) => item.status === 'pending').length) } : stat,
  );

  return (
    <div className="space-y-6">
      <Card className="border-slate-200 bg-gradient-to-br from-slate-950 via-slate-900 to-blue-950 text-white">
        <CardHeader>
          <CardTitle className="text-3xl">Welcome to {workspace?.name ?? 'your Velaris workspace'}</CardTitle>
          <CardDescription className="text-slate-300">
            Launch workflows, review critical approvals, and inspect audit activity from a unified operator console.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-3">
          <Button asChild variant="secondary">
            <Link href="/dashboard/chat">Open chat</Link>
          </Button>
          <Button asChild variant="outline" className="border-white/20 bg-transparent text-white hover:bg-white/10 hover:text-white">
            <Link href="/dashboard/approvals">Review approvals</Link>
          </Button>
        </CardContent>
      </Card>

      {loading ? (
        <div className="flex items-center gap-2 text-sm text-slate-500">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading workspace overview...
        </div>
      ) : null}
      {error ? <p className="text-sm text-red-600">{error}</p> : null}

      <div className="grid gap-4 md:grid-cols-3">
        {overviewStats.map((stat) => {
          const Icon = stat.icon;
          return (
            <Card key={stat.label} className="border-slate-200">
              <CardContent className="flex items-center justify-between p-6">
                <div>
                  <p className="text-sm text-slate-500">{stat.label}</p>
                  <p className="mt-2 text-3xl font-semibold text-slate-950">{stat.value}</p>
                </div>
                <div className="rounded-full bg-blue-100 p-3 text-blue-600">
                  <Icon className="h-5 w-5" />
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.5fr,1fr]">
        <Card className="border-slate-200">
          <CardHeader>
            <CardTitle>Quick actions</CardTitle>
            <CardDescription>Jump into the most common operator tasks.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-2">
            {[
              {
                title: 'Agent chat',
                description: 'Start a new multi-step run with connected tools and execution planning.',
                href: '/dashboard/chat',
                icon: Bot,
              },
              {
                title: 'Approval queue',
                description: 'Review pending human-in-the-loop steps and unblock workflows.',
                href: '/dashboard/approvals',
                icon: ClipboardCheck,
              },
            ].map((item) => {
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

        <Card className="border-slate-200">
          <CardHeader>
            <CardTitle>Approval snapshot</CardTitle>
            <CardDescription>Current queue health for high-risk actions.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {approvals.length > 0 ? (
              approvals.slice(0, 3).map((approval) => (
                <div key={approval.id} className="rounded-xl border border-slate-200 p-4">
                  <p className="font-medium text-slate-900">{approval.requested_action}</p>
                  <p className="mt-1 text-sm text-slate-500">{approval.reason ?? 'No reason provided'}</p>
                </div>
              ))
            ) : (
              <div className="rounded-xl border border-dashed border-slate-300 p-6 text-sm text-slate-500">
                No pending approvals right now. Agent runs can execute immediately.
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
