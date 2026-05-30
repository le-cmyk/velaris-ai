import { BarChart3 } from 'lucide-react';

import { Card, CardContent } from '@/components/ui/card';

export default function DashboardsPage() {
  return (
    <Card className="border-slate-200">
      <CardContent className="flex min-h-[360px] flex-col items-center justify-center gap-3 p-8 text-center">
        <div className="rounded-full bg-violet-100 p-3 text-violet-700">
          <BarChart3 className="h-6 w-6" />
        </div>
        <h2 className="text-xl font-semibold text-slate-950">Dashboards</h2>
        <p className="max-w-md text-sm text-slate-500">
          Workspace dashboards will appear here as they are created.
        </p>
      </CardContent>
    </Card>
  );
}

