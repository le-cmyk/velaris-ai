'use client';

import { useEffect, useMemo, useState } from 'react';
import { Bot, CheckCircle2, Copy, Loader2, Play, Plus, Route, ShieldCheck } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { api } from '@/lib/api';
import { getToken } from '@/lib/auth';
import type { ClientEndpoint, ClientEndpointMethod, ClientEndpointMode } from '@/types';

const defaultConfigByMode: Record<ClientEndpointMode, string> = {
  agent_task: JSON.stringify(
    {
      instruction: 'Inspect the request, choose the right Velaris data/tools/functions, perform the backend work, and return an API-ready response.',
      allowed_tools: ['data_query', 'client_data_create'],
      response: 'Return concise JSON for the calling application.',
    },
    null,
    2,
  ),
  data_query: JSON.stringify(
    {
      table: 'customers',
      select: ['id', 'name', 'email', 'status'],
      allowed_filter_fields: ['status', 'country', 'tier'],
      limit: 50,
    },
    null,
    2,
  ),
  client_data_create: JSON.stringify(
    {
      type: 'lead',
      title_field: 'company',
      content_field: 'notes',
      metadata_field: 'metadata',
    },
    null,
    2,
  ),
};

function prettyJson(value: unknown): string {
  return JSON.stringify(value, null, 2);
}

function authHeaderPreview(token: string | null): string {
  if (!token) return 'Authorization: Bearer <token>';
  return `Authorization: Bearer ${token.slice(0, 18)}...${token.slice(-8)}`;
}

export default function RoutesPage() {
  const [endpoints, setEndpoints] = useState<ClientEndpoint[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<string>('No test run yet.');

  const [name, setName] = useState('Smart Support Triage');
  const [method, setMethod] = useState<ClientEndpointMethod>('POST');
  const [path, setPath] = useState('/support/triage');
  const [mode, setMode] = useState<ClientEndpointMode>('agent_task');
  const [description, setDescription] = useState('Agent-backed route for support triage requests.');
  const [configText, setConfigText] = useState(defaultConfigByMode.agent_task);
  const [queryString, setQueryString] = useState('');
  const [requestBody, setRequestBody] = useState(prettyJson({ subject: 'Login is broken', priority: 'high' }));

  const selectedEndpoint = useMemo(
    () => endpoints.find((endpoint) => endpoint.id === selectedId) ?? endpoints[0] ?? null,
    [endpoints, selectedId],
  );
  const token = typeof window === 'undefined' ? null : getToken();

  const loadEndpoints = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.clientEndpoints.list();
      setEndpoints(result.items);
      setSelectedId((current) => current ?? result.items[0]?.id ?? null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load routes.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadEndpoints();
  }, []);

  const handleModeChange = (nextMode: ClientEndpointMode) => {
    setMode(nextMode);
    setConfigText(defaultConfigByMode[nextMode]);
    if (nextMode === 'data_query') {
      setMethod('GET');
      setPath('/customers/search');
      setDescription('Deterministic data route backed by the Velaris data catalog.');
      setRequestBody('{}');
    } else if (nextMode === 'client_data_create') {
      setMethod('POST');
      setPath('/leads');
      setDescription('Simple write route that creates flexible client data records.');
      setRequestBody(prettyJson({ company: 'Acme', notes: 'Interested in Velaris', metadata: { source: 'route-console' } }));
    } else {
      setMethod('POST');
      setPath('/support/triage');
      setDescription('Agent-backed route for support triage requests.');
      setRequestBody(prettyJson({ subject: 'Login is broken', priority: 'high' }));
    }
  };

  const createRoute = async () => {
    setSaving(true);
    setError(null);
    try {
      const parsedConfig = JSON.parse(configText) as Record<string, unknown>;
      const endpoint = await api.clientEndpoints.create({
        name,
        method,
        path,
        mode,
        description,
        config: parsedConfig,
      });
      await loadEndpoints();
      setSelectedId(endpoint.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to create route.');
    } finally {
      setSaving(false);
    }
  };

  const toggleRoute = async (endpoint: ClientEndpoint) => {
    setError(null);
    try {
      const updated = await api.clientEndpoints.update(endpoint.id, { is_active: !endpoint.is_active });
      setEndpoints((current) => current.map((item) => (item.id === updated.id ? updated : item)));
      setSelectedId(updated.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to update route.');
    }
  };

  const testRoute = async (endpoint: ClientEndpoint) => {
    setTesting(true);
    setError(null);
    try {
      const result = await api.clientEndpoints.execute(endpoint, {
        query: queryString,
        body: requestBody,
      });
      setTestResult(prettyJson(result));
    } catch (err) {
      setTestResult(err instanceof Error ? err.message : 'Route test failed.');
    } finally {
      setTesting(false);
    }
  };

  const callPath = selectedEndpoint ? `/client-api${selectedEndpoint.path}` : '/client-api/<route>';
  const curlExample = selectedEndpoint
    ? [
        `curl -X ${selectedEndpoint.method} "$API_URL${callPath}${queryString ? `?${queryString}` : ''}"`,
        `  -H "${authHeaderPreview(token)}"`,
        selectedEndpoint.method === 'GET' || selectedEndpoint.method === 'DELETE'
          ? ''
          : `  -H "Content-Type: application/json" \\\n  -d '${requestBody.replace(/\n/g, '')}'`,
      ].filter(Boolean).join(' \\\n')
    : 'Create or select a route to see a request example.';

  return (
    <div className="space-y-4">
      <div className="grid gap-4 xl:grid-cols-[1.15fr,0.85fr]">
        <Card className="border-slate-200">
          <CardHeader>
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Route className="h-5 w-5 text-blue-600" />
                  Agent route console
                </CardTitle>
                <CardDescription>
                  Create client API contracts that Velaris can execute with an agent, a structured data query, or a simple write handler.
                </CardDescription>
              </div>
              <Badge variant="secondary">Calls require Bearer auth</Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-3 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="route-name">Route name</Label>
                <Input id="route-name" value={name} onChange={(event) => setName(event.target.value)} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="route-path">Client path</Label>
                <Input id="route-path" value={path} onChange={(event) => setPath(event.target.value)} />
              </div>
            </div>

            <div className="grid gap-3 md:grid-cols-3">
              <div className="space-y-2">
                <Label htmlFor="route-method">Method</Label>
                <select
                  id="route-method"
                  value={method}
                  onChange={(event) => setMethod(event.target.value as ClientEndpointMethod)}
                  className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                >
                  {(['GET', 'POST', 'PATCH', 'PUT', 'DELETE'] as ClientEndpointMethod[]).map((item) => (
                    <option key={item} value={item}>{item}</option>
                  ))}
                </select>
              </div>
              <div className="space-y-2 md:col-span-2">
                <Label htmlFor="route-mode">Execution mode</Label>
                <select
                  id="route-mode"
                  value={mode}
                  onChange={(event) => handleModeChange(event.target.value as ClientEndpointMode)}
                  className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                >
                  <option value="agent_task">agent_task - API request becomes an agent run</option>
                  <option value="data_query">data_query - deterministic workspace data read</option>
                  <option value="client_data_create">client_data_create - simple record creation</option>
                </select>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="route-description">Agent-facing purpose</Label>
              <Input id="route-description" value={description} onChange={(event) => setDescription(event.target.value)} />
            </div>

            <div className="space-y-2">
              <Label htmlFor="route-config">Route config JSON</Label>
              <textarea
                id="route-config"
                value={configText}
                onChange={(event) => setConfigText(event.target.value)}
                className="min-h-56 w-full rounded-md border border-input bg-background p-3 font-mono text-xs"
              />
            </div>

            {error ? <p className="text-sm text-red-600">{error}</p> : null}

            <Button onClick={() => void createRoute()} disabled={saving} className="gap-2">
              {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
              Create route
            </Button>
          </CardContent>
        </Card>

        <Card className="border-slate-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ShieldCheck className="h-5 w-5 text-emerald-600" />
              Token and authentication
            </CardTitle>
            <CardDescription>
              Runtime routes use the same JWT Bearer token as the rest of Velaris.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
              <p className="font-medium text-slate-950">Current browser token</p>
              <p className="mt-2 break-all font-mono text-xs text-slate-600">{authHeaderPreview(token)}</p>
            </div>
            <div className="space-y-2">
              <p className="font-medium text-slate-950">How calls are authenticated</p>
              <p className="text-slate-500">
                A client first logs in with `/auth/login`, stores the returned `access_token`, then calls `/client-api/...` with `Authorization: Bearer &lt;token&gt;`.
              </p>
              <p className="text-slate-500">
                Velaris decodes the token, identifies the workspace, and executes the route only against that workspace.
              </p>
            </div>
            <Separator />
            <div className="space-y-2">
              <p className="font-medium text-slate-950">Agent route creation language</p>
              <p className="text-slate-500">
                Users can ask the agent to “create a route”, “make an endpoint”, or “add an API for leads.” The agent now treats that as `create_client_endpoint`.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 xl:grid-cols-[0.95fr,1.05fr]">
        <Card className="border-slate-200">
          <CardHeader>
            <CardTitle>Created routes</CardTitle>
            <CardDescription>Select a route to inspect its contract and test it.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {loading ? (
              <div className="flex items-center gap-2 text-sm text-slate-500">
                <Loader2 className="h-4 w-4 animate-spin" />
                Loading routes...
              </div>
            ) : endpoints.length > 0 ? (
              endpoints.map((endpoint) => (
                <button
                  key={endpoint.id}
                  type="button"
                  onClick={() => setSelectedId(endpoint.id)}
                  className={`w-full rounded-xl border p-4 text-left transition ${
                    selectedEndpoint?.id === endpoint.id ? 'border-blue-300 bg-blue-50' : 'border-slate-200 hover:bg-slate-50'
                  }`}
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div>
                      <p className="font-medium text-slate-950">{endpoint.name}</p>
                      <p className="mt-1 font-mono text-xs text-slate-500">{endpoint.method} /client-api{endpoint.path}</p>
                    </div>
                    <div className="flex gap-2">
                      <Badge variant={endpoint.is_active ? 'success' : 'secondary'}>{endpoint.is_active ? 'Active' : 'Disabled'}</Badge>
                      <Badge variant="secondary">{endpoint.mode}</Badge>
                    </div>
                  </div>
                </button>
              ))
            ) : (
              <div className="rounded-xl border border-dashed border-slate-300 p-8 text-center text-sm text-slate-500">
                No client routes yet. Create the first one above.
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="border-slate-200">
          <CardHeader>
            <CardTitle>Inspect and test</CardTitle>
            <CardDescription>See what the agent created, then call the actual route.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {selectedEndpoint ? (
              <>
                <div className="grid gap-3 md:grid-cols-3">
                  <div className="rounded-lg border border-slate-200 p-3">
                    <p className="text-xs uppercase tracking-wide text-slate-400">Endpoint</p>
                    <p className="mt-1 font-mono text-sm text-slate-950">{selectedEndpoint.method} {callPath}</p>
                  </div>
                  <div className="rounded-lg border border-slate-200 p-3">
                    <p className="text-xs uppercase tracking-wide text-slate-400">Mode</p>
                    <p className="mt-1 text-sm font-medium text-slate-950">{selectedEndpoint.mode}</p>
                  </div>
                  <div className="rounded-lg border border-slate-200 p-3">
                    <p className="text-xs uppercase tracking-wide text-slate-400">State</p>
                    <p className="mt-1 text-sm font-medium text-slate-950">{selectedEndpoint.is_active ? 'Active' : 'Disabled'}</p>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Created config</Label>
                  <pre className="max-h-64 overflow-auto rounded-lg bg-slate-950 p-3 text-xs text-slate-100">{prettyJson(selectedEndpoint.config)}</pre>
                </div>

                <div className="grid gap-3 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="test-query">Query string</Label>
                    <Input id="test-query" value={queryString} onChange={(event) => setQueryString(event.target.value)} placeholder="status=active" />
                  </div>
                  <div className="space-y-2">
                    <Label>Controls</Label>
                    <div className="flex gap-2">
                      <Button onClick={() => void testRoute(selectedEndpoint)} disabled={testing || !selectedEndpoint.is_active} className="gap-2">
                        {testing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
                        Test route
                      </Button>
                      <Button variant="outline" onClick={() => void toggleRoute(selectedEndpoint)}>
                        {selectedEndpoint.is_active ? 'Disable' : 'Enable'}
                      </Button>
                    </div>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="test-body">Request body</Label>
                  <textarea
                    id="test-body"
                    value={requestBody}
                    onChange={(event) => setRequestBody(event.target.value)}
                    className="min-h-32 w-full rounded-md border border-input bg-background p-3 font-mono text-xs"
                  />
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between gap-2">
                    <Label>Request example</Label>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => void navigator.clipboard.writeText(curlExample)}
                      className="gap-2"
                    >
                      <Copy className="h-4 w-4" />
                      Copy
                    </Button>
                  </div>
                  <pre className="overflow-auto rounded-lg bg-slate-950 p-3 text-xs text-slate-100">{curlExample}</pre>
                </div>

                <div className="space-y-2">
                  <Label>Test response</Label>
                  <pre className="min-h-32 overflow-auto rounded-lg bg-slate-950 p-3 text-xs text-slate-100">{testResult}</pre>
                </div>
              </>
            ) : (
              <div className="flex min-h-[320px] flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-slate-300 p-8 text-center text-sm text-slate-500">
                <Bot className="h-6 w-6" />
                Create a route to inspect and test it here.
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="flex items-start gap-2 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800">
        <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />
        <p>
          Route calls are not public by default. The same Velaris JWT controls access, and every runtime route resolves the workspace from the token before executing.
        </p>
      </div>
    </div>
  );
}
