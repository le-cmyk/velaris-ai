'use client';

import { useEffect, useState } from 'react';
import { Loader2 } from 'lucide-react';

import { Card, CardContent } from '@/components/ui/card';
import { api } from '@/lib/api';
import type { AuditLogEntry } from '@/types';

export default function AuditLogsPage() {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const result = await api.getAuditLogs();
        setLogs(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unable to load audit logs.');
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, []);

  return (
    <Card className="border-slate-200">
      <CardContent className="space-y-4 p-0">
        {loading ? (
          <div className="flex items-center gap-2 px-6 pt-6 text-sm text-slate-500">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading audit history...
          </div>
        ) : null}
        {error ? <p className="px-6 pt-6 text-sm text-red-600">{error}</p> : null}
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-6 py-3 text-left font-medium text-slate-500">Action</th>
                <th className="px-6 py-3 text-left font-medium text-slate-500">Resource</th>
                <th className="px-6 py-3 text-left font-medium text-slate-500">Details</th>
                <th className="px-6 py-3 text-left font-medium text-slate-500">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {logs.length > 0 ? (
                logs.map((entry) => (
                  <tr key={entry.id}>
                    <td className="px-6 py-4 font-medium text-slate-900">{entry.action}</td>
                    <td className="px-6 py-4 text-slate-600">
                      {entry.resource_type}
                      {entry.resource_id ? ` · ${entry.resource_id}` : ''}
                    </td>
                    <td className="max-w-md px-6 py-4 text-slate-500">{JSON.stringify(entry.details ?? {})}</td>
                    <td className="px-6 py-4 text-slate-500">{new Date(entry.created_at).toLocaleString()}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={4} className="px-6 py-12 text-center text-slate-500">
                    No audit log entries are available yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
