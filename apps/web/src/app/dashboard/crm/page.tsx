import { Users } from 'lucide-react';

import { Card, CardContent } from '@/components/ui/card';

export default function CrmPage() {
  return (
    <Card className="border-slate-200">
      <CardContent className="flex min-h-[360px] flex-col items-center justify-center gap-3 p-8 text-center">
        <div className="rounded-full bg-emerald-100 p-3 text-emerald-700">
          <Users className="h-6 w-6" />
        </div>
        <h2 className="text-xl font-semibold text-slate-950">CRM</h2>
        <p className="max-w-md text-sm text-slate-500">
          Customer, deal, invoice, and support records will appear here as the CRM workspace grows.
        </p>
      </CardContent>
    </Card>
  );
}

