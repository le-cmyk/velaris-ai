'use client';

import { useState } from 'react';
import { Check, Loader2, X } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { api } from '@/lib/api';
import type { ApprovalRequest } from '@/types';

interface ApprovalCardProps {
  approval: ApprovalRequest;
  onUpdated?: (approval: ApprovalRequest) => void;
}

export function ApprovalCard({ approval, onUpdated }: ApprovalCardProps) {
  const [currentApproval, setCurrentApproval] = useState(approval);
  const [loading, setLoading] = useState<'approve' | 'reject' | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleAction = async (action: 'approve' | 'reject') => {
    setLoading(action);
    setError(null);

    try {
      const actionResult =
        action === 'approve'
          ? await api.approveAction(currentApproval.id)
          : await api.rejectAction(currentApproval.id);
      const updated = { ...currentApproval, id: actionResult.approval_id, status: actionResult.status };
      setCurrentApproval(updated);
      onUpdated?.(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to update approval status.');
    } finally {
      setLoading(null);
    }
  };

  return (
    <Card className="border-slate-200">
      <CardHeader className="flex flex-row items-start justify-between gap-4">
        <div>
          <CardTitle className="text-lg">{currentApproval.requested_action}</CardTitle>
          <p className="mt-2 text-sm text-slate-500">Run ID: {currentApproval.run_id}</p>
        </div>
        <Badge variant={currentApproval.status === 'pending' ? 'warning' : currentApproval.status === 'approved' ? 'success' : 'destructive'}>
          {currentApproval.status}
        </Badge>
      </CardHeader>
      <CardContent className="space-y-3 text-sm text-slate-600">
        <div>
          <p className="font-medium text-slate-900">Tool Call ID</p>
          <p>{currentApproval.tool_call_id}</p>
        </div>
        <div>
          <p className="font-medium text-slate-900">Reason</p>
          <p>{currentApproval.reason ?? 'No explicit reason was provided.'}</p>
        </div>
        <div>
          <p className="font-medium text-slate-900">Requested</p>
          <p>{new Date(currentApproval.created_at).toLocaleString()}</p>
        </div>
        {error ? <p className="text-red-600">{error}</p> : null}
      </CardContent>
      <CardFooter className="gap-3">
        <Button
          onClick={() => void handleAction('approve')}
          disabled={currentApproval.status !== 'pending' || loading !== null}
          className="gap-2"
        >
          {loading === 'approve' ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />}
          Approve
        </Button>
        <Button
          variant="outline"
          onClick={() => void handleAction('reject')}
          disabled={currentApproval.status !== 'pending' || loading !== null}
          className="gap-2"
        >
          {loading === 'reject' ? <Loader2 className="h-4 w-4 animate-spin" /> : <X className="h-4 w-4" />}
          Reject
        </Button>
      </CardFooter>
    </Card>
  );
}
