'use client';

import { useEffect, useState } from 'react';
import { Database, Loader2, Plus, Search, Trash2, X } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { api } from '@/lib/api';
import type { ClientDataRecord } from '@/types';

const RECORD_TYPES = ['customer', 'invoice', 'support_ticket', 'task', 'contract', 'company_note', 'product_usage'];

const TYPE_COLORS: Record<string, string> = {
  customer: 'bg-blue-100 text-blue-800',
  invoice: 'bg-green-100 text-green-800',
  support_ticket: 'bg-red-100 text-red-800',
  task: 'bg-yellow-100 text-yellow-800',
  contract: 'bg-purple-100 text-purple-800',
  company_note: 'bg-slate-100 text-slate-800',
  product_usage: 'bg-teal-100 text-teal-800',
};

function TypeBadge({ type }: { type: string }) {
  const cls = TYPE_COLORS[type] ?? 'bg-slate-100 text-slate-700';
  return (
    <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${cls}`}>
      {type.replace('_', ' ')}
    </span>
  );
}

export default function DataPage() {
  const [records, setRecords] = useState<ClientDataRecord[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [typeFilter, setTypeFilter] = useState('');
  const [search, setSearch] = useState('');
  const [searchInput, setSearchInput] = useState('');

  // Create form
  const [showCreate, setShowCreate] = useState(false);
  const [createType, setCreateType] = useState('customer');
  const [createTitle, setCreateTitle] = useState('');
  const [createContent, setCreateContent] = useState('');
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  // Delete
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.getClientData({
        type: typeFilter || undefined,
        search: search || undefined,
        limit: 100,
      });
      setRecords(result.items);
      setTotal(result.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load records.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [typeFilter, search]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSearch(searchInput);
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createTitle.trim()) return;
    setCreating(true);
    setCreateError(null);
    try {
      const record = await api.createClientData({
        type: createType,
        title: createTitle,
        content: createContent || undefined,
      });
      setRecords((prev) => [record, ...prev]);
      setTotal((t) => t + 1);
      setCreateTitle('');
      setCreateContent('');
      setShowCreate(false);
    } catch (err) {
      setCreateError(err instanceof Error ? err.message : 'Failed to create record.');
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this record? This cannot be undone.')) return;
    setDeletingId(id);
    try {
      await api.deleteClientData(id);
      setRecords((prev) => prev.filter((r) => r.id !== id));
      setTotal((t) => t - 1);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete record.');
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-950">Client Data</h1>
          <p className="text-sm text-slate-500">
            {total} record{total !== 1 ? 's' : ''} in your workspace
          </p>
        </div>
        <Button onClick={() => setShowCreate((v) => !v)}>
          <Plus className="mr-2 h-4 w-4" />
          New record
        </Button>
      </div>

      {showCreate ? (
        <Card className="border-blue-200 bg-blue-50/40">
          <CardHeader>
            <CardTitle className="text-lg">Create record</CardTitle>
          </CardHeader>
          <CardContent>
            <form className="space-y-4" onSubmit={handleCreate}>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-1">
                  <Label htmlFor="new-type">Type</Label>
                  <select
                    id="new-type"
                    value={createType}
                    onChange={(e) => setCreateType(e.target.value)}
                    className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm"
                  >
                    {RECORD_TYPES.map((t) => (
                      <option key={t} value={t}>
                        {t.replace('_', ' ')}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="space-y-1">
                  <Label htmlFor="new-title">Title *</Label>
                  <Input
                    id="new-title"
                    value={createTitle}
                    onChange={(e) => setCreateTitle(e.target.value)}
                    required
                    placeholder="Record title"
                  />
                </div>
              </div>
              <div className="space-y-1">
                <Label htmlFor="new-content">Content</Label>
                <textarea
                  id="new-content"
                  value={createContent}
                  onChange={(e) => setCreateContent(e.target.value)}
                  rows={3}
                  className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground"
                  placeholder="Optional description or notes"
                />
              </div>
              {createError ? <p className="text-sm text-red-600">{createError}</p> : null}
              <div className="flex gap-2">
                <Button type="submit" disabled={creating}>
                  {creating ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                  Create
                </Button>
                <Button type="button" variant="ghost" onClick={() => setShowCreate(false)}>
                  <X className="mr-2 h-4 w-4" />
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      ) : null}

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <form onSubmit={handleSearch} className="flex gap-2">
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <Input
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Search by title…"
              className="w-56 pl-9"
            />
          </div>
          <Button type="submit" variant="secondary" size="sm">
            Search
          </Button>
          {search ? (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => {
                setSearch('');
                setSearchInput('');
              }}
            >
              Clear
            </Button>
          ) : null}
        </form>

        <div className="flex flex-wrap gap-2">
          <Button
            variant={typeFilter === '' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setTypeFilter('')}
          >
            All
          </Button>
          {RECORD_TYPES.map((t) => (
            <Button
              key={t}
              variant={typeFilter === t ? 'default' : 'outline'}
              size="sm"
              onClick={() => setTypeFilter(t)}
            >
              {t.replace('_', ' ')}
            </Button>
          ))}
        </div>
      </div>

      {/* Records */}
      {loading ? (
        <div className="flex items-center gap-2 text-sm text-slate-500">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading records…
        </div>
      ) : error ? (
        <p className="text-sm text-red-600">{error}</p>
      ) : records.length === 0 ? (
        <Card className="border-dashed border-slate-300">
          <CardContent className="flex flex-col items-center gap-3 py-12 text-center">
            <Database className="h-8 w-8 text-slate-400" />
            <p className="text-slate-500">No records found. Try adjusting your filters or create a new record.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {records.map((record) => (
            <Card key={record.id} className="border-slate-200">
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between gap-2">
                  <TypeBadge type={record.type} />
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7 text-slate-400 hover:text-red-500"
                    disabled={deletingId === record.id}
                    onClick={() => handleDelete(record.id)}
                    title="Delete record"
                  >
                    {deletingId === record.id ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                      <Trash2 className="h-3.5 w-3.5" />
                    )}
                  </Button>
                </div>
                <CardTitle className="mt-1 text-base leading-snug">{record.title}</CardTitle>
              </CardHeader>
              {record.content ? (
                <CardContent className="pt-0">
                  <CardDescription className="line-clamp-3 text-xs">{record.content}</CardDescription>
                </CardContent>
              ) : null}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
