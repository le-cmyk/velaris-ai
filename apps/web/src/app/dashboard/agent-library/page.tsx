import { Bot } from 'lucide-react';

import { Card, CardContent } from '@/components/ui/card';

export default function AgentLibraryPage() {
  return (
    <Card className="border-slate-200">
      <CardContent className="flex min-h-[360px] flex-col items-center justify-center gap-3 p-8 text-center">
        <div className="rounded-full bg-blue-100 p-3 text-blue-700">
          <Bot className="h-6 w-6" />
        </div>
        <h2 className="text-xl font-semibold text-slate-950">Agent Library</h2>
        <p className="max-w-md text-sm text-slate-500">
          Agent templates will appear here as they are added to this workspace.
        </p>
      </CardContent>
    </Card>
  );
}

