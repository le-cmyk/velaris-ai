'use client';

import { useEffect, useState } from 'react';
import { Loader2 } from 'lucide-react';

import { ApprovalCard } from '@/components/approvals/ApprovalCard';
import { Card, CardContent } from '@/components/ui/card';
import { api } from '@/lib/api';
import type { ApprovalRequest } from '@/types';

export default function ApprovalsPage() {
  const [approvals, setApprovals] = useState<ApprovalRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const result = await api.getApprovals();
        setApprovals(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unable to load approvals.');
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, []);

  const handleUpdated = (updatedApproval: ApprovalRequest) => {
    setApprovals((current) => current.map((approval) => (approval.id === updatedApproval.id ? updatedApproval : approval)));
  };

  const pendingApprovals = approvals.filter((approval) => approval.status === 'pending');

  return (
    <div className="space-y-4">
      {loading ? (
        <div className="flex items-center gap-2 text-sm text-slate-500">
          <Loader2 className="h-4 w-4 animate-spin" />
          Fetching approval requests...
        </div>
      ) : null}
      {error ? <p className="text-sm text-red-600">{error}</p> : null}
      {!loading && pendingApprovals.length === 0 ? (
        <Card className="border-dashed border-slate-300">
          <CardContent className="p-10 text-center text-sm text-slate-500">
            There are no pending approvals. Critical tool actions will appear here when a run requires human review.
          </CardContent>
        </Card>
      ) : null}
      <div className="grid gap-4 xl:grid-cols-2">
        {pendingApprovals.map((approval) => (
          <ApprovalCard key={approval.id} approval={approval} onUpdated={handleUpdated} />
        ))}
      </div>
    </div>
  );
}
