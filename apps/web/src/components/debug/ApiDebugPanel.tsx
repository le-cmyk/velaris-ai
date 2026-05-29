'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { Loader2, RefreshCcw } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { api, type ApiHealthDebugResult } from '@/lib/api';

interface ApiDebugPanelProps {
  forceVisible?: boolean;
  compact?: boolean;
}

const initialState: ApiHealthDebugResult = {
  configuredApiUrl: '(missing)',
  requestUrl: null,
  status: null,
  statusText: null,
  data: null,
  error: null,
  checkedAt: '',
};

export function ApiDebugPanel({ forceVisible = false, compact = false }: ApiDebugPanelProps) {
  const isVisible = forceVisible || process.env.NODE_ENV !== 'production';
  const [result, setResult] = useState<ApiHealthDebugResult>(initialState);
  const [loading, setLoading] = useState(false);

  const runCheck = useCallback(async () => {
    setLoading(true);

    try {
      const nextResult = await api.getHealthDebug();
      setResult(nextResult);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!isVisible) {
      return;
    }

    void runCheck();
  }, [isVisible, runCheck]);

  const formattedJson = useMemo(() => {
    if (result.data == null) {
      return 'No JSON response yet.';
    }

    return JSON.stringify(result.data, null, 2);
  }, [result.data]);

  if (!isVisible) {
    return null;
  }

  return (
    <Card className="border-slate-200 bg-slate-50/80">
      <CardHeader className={compact ? 'space-y-2 p-4' : undefined}>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <CardTitle className={compact ? 'text-lg' : undefined}>API debug</CardTitle>
            <CardDescription>
              Frontend connectivity diagnostics for <code className="rounded bg-slate-200 px-1 py-0.5">NEXT_PUBLIC_API_URL</code>
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Button type="button" variant="outline" size="sm" onClick={() => void runCheck()} disabled={loading}>
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCcw className="h-4 w-4" />}
              Refresh
            </Button>
            {!forceVisible ? (
              <Button asChild type="button" variant="ghost" size="sm">
                <Link href="/debug-api">Open full page</Link>
              </Button>
            ) : null}
          </div>
        </div>
      </CardHeader>
      <CardContent className={compact ? 'space-y-3 p-4 pt-0' : 'space-y-4'}>
        <div className="grid gap-3 text-sm md:grid-cols-2">
          <div className="rounded-lg border border-slate-200 bg-white p-3">
            <p className="font-medium text-slate-900">Configured API URL</p>
            <p className="mt-1 break-all font-mono text-xs text-slate-600">{result.configuredApiUrl}</p>
          </div>
          <div className="rounded-lg border border-slate-200 bg-white p-3">
            <p className="font-medium text-slate-900">Health status</p>
            <p className="mt-1 text-slate-600">
              {result.status != null ? `${result.status}${result.statusText ? ` ${result.statusText}` : ''}` : 'No response yet'}
            </p>
          </div>
          <div className="rounded-lg border border-slate-200 bg-white p-3 md:col-span-2">
            <p className="font-medium text-slate-900">Health request URL</p>
            <p className="mt-1 break-all font-mono text-xs text-slate-600">{result.requestUrl ?? 'Unavailable'}</p>
          </div>
          <div className="rounded-lg border border-slate-200 bg-white p-3 md:col-span-2">
            <p className="font-medium text-slate-900">Last checked</p>
            <p className="mt-1 text-slate-600">{result.checkedAt ? new Date(result.checkedAt).toLocaleString() : 'Not checked yet'}</p>
          </div>
        </div>

        {result.error ? (
          <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            <p className="font-medium">Request error</p>
            <p className="mt-1 break-words">{result.error}</p>
          </div>
        ) : null}

        <div className="rounded-lg border border-slate-200 bg-slate-950 p-3">
          <p className="text-sm font-medium text-white">/health response JSON</p>
          <pre className="mt-2 overflow-x-auto whitespace-pre-wrap break-words text-xs text-slate-200">{formattedJson}</pre>
        </div>
      </CardContent>
    </Card>
  );
}
