import { Badge } from '@/components/ui/badge';

interface ExecutionTimelineProps {
  intent: string;
  executionPlan: Record<string, unknown> | null;
  toolCallsCount: number;
}

export function ExecutionTimeline({ intent, executionPlan, toolCallsCount }: ExecutionTimelineProps) {
  const steps =
    executionPlan &&
    typeof executionPlan === 'object' &&
    Array.isArray((executionPlan as { steps?: unknown }).steps)
      ? ((executionPlan as { steps: unknown[] }).steps.filter((step) => typeof step === 'string') as string[])
      : [];

  const items = [
    {
      title: 'Intent classification',
      description: intent,
    },
    {
      title: 'Execution plan',
      description: steps.length > 0 ? steps.join(' · ') : 'No plan steps were returned for this run.',
    },
    {
      title: 'Tool calls',
      description: `${toolCallsCount} tool call${toolCallsCount === 1 ? '' : 's'} evaluated during execution.`,
    },
    {
      title: 'Response',
      description: 'The assistant synthesized execution results into the final response below.',
    },
  ];

  return (
    <div className="space-y-3">
      {items.map((item, index) => (
        <div key={item.title} className="flex gap-3">
          <div className="flex flex-col items-center">
            <Badge variant="secondary" className="h-7 w-7 justify-center rounded-full p-0 text-xs">
              {index + 1}
            </Badge>
            {index < items.length - 1 ? <div className="mt-2 h-full w-px bg-slate-200" /> : null}
          </div>
          <div className="pb-4">
            <p className="font-medium text-slate-900">{item.title}</p>
            <p className="text-sm text-slate-500">{item.description}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
