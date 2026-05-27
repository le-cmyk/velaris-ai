'use client';

import { useEffect, useState } from 'react';
import { Loader2 } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { api } from '@/lib/api';
import { getUser } from '@/lib/auth';
import type { ToolInfo, WorkspaceInfo } from '@/types';

export default function SettingsPage() {
  const user = getUser();
  const [workspace, setWorkspace] = useState<WorkspaceInfo | null>(null);
  const [tools, setTools] = useState<ToolInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const [workspaceResult, toolsResult] = await Promise.all([api.getWorkspace(), api.getTools()]);
        setWorkspace(workspaceResult);
        setTools(toolsResult);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unable to load settings.');
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, []);

  return (
    <div className="grid gap-4 xl:grid-cols-[1fr,1.2fr]">
      <Card className="border-slate-200">
        <CardHeader>
          <CardTitle>User profile</CardTitle>
          <CardDescription>Current authenticated workspace identity.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 text-sm">
          <div>
            <p className="text-slate-500">Full name</p>
            <p className="font-medium text-slate-950">{user?.full_name ?? 'Velaris User'}</p>
          </div>
          <div>
            <p className="text-slate-500">Email</p>
            <p className="font-medium text-slate-950">{user?.email ?? 'demo@velaris.ai'}</p>
          </div>
          <div>
            <p className="text-slate-500">Workspace ID</p>
            <p className="font-medium text-slate-950">{user?.workspace_id ?? 'default-workspace'}</p>
          </div>
          <Separator />
          <div>
            <p className="text-slate-500">Workspace name</p>
            <p className="font-medium text-slate-950">{workspace?.name ?? 'Loading workspace...'}</p>
          </div>
          {loading ? (
            <div className="flex items-center gap-2 text-slate-500">
              <Loader2 className="h-4 w-4 animate-spin" />
              Syncing workspace settings...
            </div>
          ) : null}
          {error ? <p className="text-red-600">{error}</p> : null}
        </CardContent>
      </Card>

      <Card className="border-slate-200">
        <CardHeader>
          <CardTitle>Connected tools</CardTitle>
          <CardDescription>Tool availability and approval requirements.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {tools.length > 0 ? (
            tools.map((tool) => (
              <div key={tool.name} className="rounded-xl border border-slate-200 p-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="font-medium text-slate-950">{tool.name}</p>
                    <p className="mt-1 text-sm text-slate-500">{tool.description}</p>
                  </div>
                  <div className="flex gap-2">
                    <Badge variant={tool.enabled ? 'success' : 'secondary'}>{tool.enabled ? 'Enabled' : 'Disabled'}</Badge>
                    <Badge variant={tool.requires_approval ? 'warning' : 'secondary'}>
                      {tool.requires_approval ? 'Approval required' : 'Auto-approved'}
                    </Badge>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="rounded-xl border border-dashed border-slate-300 p-8 text-center text-sm text-slate-500">
              No tools were returned by the API.
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
