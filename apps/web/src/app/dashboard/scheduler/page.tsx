import { Clock } from 'lucide-react';

import { Card, CardContent } from '@/components/ui/card';

export default function SchedulerPage() {
  return (
    <Card className="border-slate-200">
      <CardContent className="flex min-h-[360px] flex-col items-center justify-center gap-3 p-8 text-center">
        <div className="rounded-full bg-amber-100 p-3 text-amber-700">
          <Clock className="h-6 w-6" />
        </div>
        <h2 className="text-xl font-semibold text-slate-950">Scheduler</h2>
        <p className="max-w-md text-sm text-slate-500">
          Scheduled jobs will appear here as they are configured.
        </p>
      </CardContent>
    </Card>
  );
}

