import { CheckCircle2, Clock3, ShieldAlert, XCircle } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { ToolCallResult } from '@/types';

const statusConfig: Record<
  ToolCallResult['status'],
  { label: string; variant: 'default' | 'destructive' | 'secondary' | 'success' | 'warning'; icon: typeof Clock3 }
> = {
  pending: { label: 'Pending', variant: 'warning', icon: Clock3 },
  approved: { label: 'Approved', variant: 'success', icon: CheckCircle2 },
  rejected: { label: 'Rejected', variant: 'destructive', icon: XCircle },
  executed: { label: 'Executed', variant: 'success', icon: CheckCircle2 },
  failed: { label: 'Failed', variant: 'destructive', icon: XCircle },
  blocked: { label: 'Blocked', variant: 'destructive', icon: ShieldAlert },
  pending_approval: { label: 'Pending approval', variant: 'warning', icon: ShieldAlert },
};

export function ToolCallCard({ toolCall }: { toolCall: ToolCallResult }) {
  const config = statusConfig[toolCall.status];
  const Icon = config.icon;

  return (
    <Card className="border-slate-200 bg-white/90 shadow-none">
      <CardHeader className="flex flex-row items-start justify-between gap-4 pb-4">
        <div>
          <CardTitle className="text-base">{toolCall.tool_name}</CardTitle>
          <p className="mt-1 text-sm text-slate-500">Agent tool execution metadata</p>
        </div>
        <Badge variant={config.variant} className="gap-1">
          <Icon className="h-3.5 w-3.5" />
          {config.label}
        </Badge>
      </CardHeader>
      <CardContent className="space-y-4 text-sm">
        <div>
          <p className="mb-2 font-medium text-slate-700">Arguments</p>
          <pre className="overflow-x-auto rounded-lg bg-slate-950 p-3 text-xs text-slate-100">
            {JSON.stringify(toolCall.arguments, null, 2)}
          </pre>
        </div>

        {toolCall.result !== null ? (
          <div>
            <p className="mb-2 font-medium text-slate-700">Result</p>
            <pre className="overflow-x-auto rounded-lg bg-slate-100 p-3 text-xs text-slate-700">
              {JSON.stringify(toolCall.result, null, 2)}
            </pre>
          </div>
        ) : null}

        {toolCall.requires_approval ? (
          <div className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-amber-800">
            This action requires human approval before execution can continue.
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
