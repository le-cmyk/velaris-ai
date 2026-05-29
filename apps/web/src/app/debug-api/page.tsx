import Link from 'next/link';

import { ApiDebugPanel } from '@/components/debug/ApiDebugPanel';
import { Button } from '@/components/ui/button';

export default function DebugApiPage() {
  return (
    <main className="min-h-screen bg-slate-950 px-6 py-10 text-slate-50 sm:px-10">
      <div className="mx-auto flex w-full max-w-4xl flex-col gap-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-sm uppercase tracking-[0.3em] text-blue-200">Velaris AI</p>
            <h1 className="mt-2 text-3xl font-semibold">Frontend API debug</h1>
            <p className="mt-2 max-w-2xl text-sm text-slate-300">
              Use this page on Vercel to confirm the frontend can reach the configured backend health endpoint.
            </p>
          </div>
          <Button asChild variant="secondary">
            <Link href="/login">Back to login</Link>
          </Button>
        </div>

        <ApiDebugPanel forceVisible />
      </div>
    </main>
  );
}
