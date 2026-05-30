import { Key } from 'lucide-react';

import { Card, CardContent } from '@/components/ui/card';

export default function ApiKeysPage() {
  return (
    <Card className="border-slate-200">
      <CardContent className="flex min-h-[360px] flex-col items-center justify-center gap-3 p-8 text-center">
        <div className="rounded-full bg-slate-100 p-3 text-slate-700">
          <Key className="h-6 w-6" />
        </div>
        <h2 className="text-xl font-semibold text-slate-950">API Keys</h2>
        <p className="max-w-md text-sm text-slate-500">
          Workspace API keys will appear here once key management is enabled.
        </p>
      </CardContent>
    </Card>
  );
}
