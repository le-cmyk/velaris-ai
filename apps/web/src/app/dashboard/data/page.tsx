'use client';

import { useEffect, useState } from 'react';
import { Database, Loader2, Plus, Search, Trash2, X } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { api } from '@/lib/api';
import type { ClientDataRecord } from '@/types';

const RECORD_TYPES = ['customer', 'invoice', 'support_ticket', 'task', 'contract', 'company_note', 'product_usage'];

const TYPE_LABELS: Record<string, string> = {
  customer: 'Customers',
  invoice: 'Invoices',
  support_ticket: 'Support Tickets',
  task: 'Tasks',
  contract: 'Contracts',
  company_note: 'Company Notes',
  product_usage: 'Product Usage',
};

const TYPE_COLORS: Record<string, string> = {
  customer: 'bg-blue-100 text-blue-800',
  invoice: 'bg-green-100 text-green-800',
  support_ticket: 'bg-red-100 text-red-800',
  task: 'bg-yellow-100 text-yellow-800',
  contract: 'bg-purple-100 text-purple-800',
  company_note: 'bg-slate-100 text-slate-800',
  product_usage: 'bg-teal-100 text-teal-800',
};

const TYPE_ACCENT: Record<string, string> = {
  customer: 'border-blue-400 text-blue-700 bg-blue-50',
  invoice: 'border-green-400 text-green-700 bg-green-50',
  support_ticket: 'border-red-400 text-red-700 bg-red-50',
  task: 'border-yellow-400 text-yellow-700 bg-yellow-50',
  contract: 'border-purple-400 text-purple-700 bg-purple-50',
  company_note: 'border-slate-400 text-slate-700 bg-slate-50',
  product_usage: 'border-teal-400 text-teal-700 bg-teal-50',
};

function TypeBadge({ type }: { type: string }) {
  const cls = TYPE_COLORS[type] ?? 'bg-slate-100 text-slate-700';
  return (
    <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${cls}`}>
      {TYPE_LABELS[type] ?? type.replace(/_/g, ' ')}
    </span>
  );
}

export default function DataPage() {
  const [allRecords, setAllRecords] = useState<ClientDataRecord[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [activeTab, setActiveTab] = useState<string>('all');
  const [search, setSearch] = useState('');
  const [searchInput, setSearchInput] = useState('');

  // Create form
  const [showCreate, setShowCreate] = useState(false);
  const [createType, setCreateType] = useState('customer');
  const [createTitle, setCreateTitle] = useState('');
  const [createContent, setCreateContent] = useState('');
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  const [deletingId, setDeletingId] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      // Fetch all pages (API max is 200 per request)
      let allItems: ClientDataRecord[] = [];
      let skip = 0;
      const pageSize = 200;
      while (true) {
        const result = await api.getClientData({ limit: pageSize, skip } as never);
        allItems = [...allItems, ...result.items];
        if (allItems.length >= result.total || result.items.length < pageSize) break;
        skip += pageSize;
      }
      setAllRecords(allItems);
      setTotal(allItems.length);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load records.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { void load(); }, []);

  const countFor = (type: string) =>
    type === 'all' ? allRecords.length : allRecords.filter((r) => r.type === type).length;

  const visibleRecords = allRecords.filter((r) => {
    const matchesTab = activeTab === 'all' || r.type === activeTab;
    const matchesSearch = !search || r.title.toLowerCase().includes(search.toLowerCase());
    return matchesTab && matchesSearch;
  });

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
      setAllRecords((prev) => [record, ...prev]);
      setTotal((t) => t + 1);
      setActiveTab(createType);
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
    if (!confirm('Delete this record? This cannot be undone.')) return;
    setDeletingId(id);
    try {
      await api.deleteClientData(id);
      setAllRecords((prev) => prev.filter((r) => r.id !== id));
      setTotal((t) => t - 1);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete record.');
    } finally {
      setDeletingId(null);
    }
  };

  const tabs = [{ key: 'all', label: 'All' }, ...RECORD_TYPES.map((t) => ({ key: t, label: TYPE_LABELS[t] ?? t }))];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-950">Client Data</h1>
          <p className="text-sm text-slate-500">{total} records in your workspace</p>
        </div>
        <Button onClick={() => setShowCreate((v) => !v)}>
          <Plus className="mr-2 h-4 w-4" />
          New record
        </Button>
      </div>

      {/* Create form */}
      {showCreate && (
        <Card className="border-blue-200 bg-blue-50/40">
          <CardContent className="pt-5">
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
                      <option key={t} value={t}>{TYPE_LABELS[t] ?? t}</option>
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
              {createError && <p className="text-sm text-red-600">{createError}</p>}
              <div className="flex gap-2">
                <Button type="submit" disabled={creating}>
                  {creating && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  Create
                </Button>
                <Button type="button" variant="ghost" onClick={() => setShowCreate(false)}>
                  <X className="mr-2 h-4 w-4" /> Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Tab navigation */}
      <div className="border-b border-slate-200">
        <nav className="-mb-px flex gap-1 overflow-x-auto">
          {tabs.map((tab) => {
            const count = countFor(tab.key);
            const isActive = activeTab === tab.key;
            const accent = tab.key !== 'all' ? TYPE_ACCENT[tab.key] : '';
            return (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`
                  flex shrink-0 items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-medium transition-colors
                  ${isActive
                    ? tab.key === 'all'
                      ? 'border-slate-900 text-slate-900'
                      : `border-current ${accent}`
                    : 'border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700'
                  }
                `}
              >
                {tab.label}
                <span className={`
                  rounded-full px-1.5 py-0.5 text-xs font-semibold
                  ${isActive
                    ? tab.key === 'all' ? 'bg-slate-900 text-white' : 'bg-current/10'
                    : 'bg-slate-100 text-slate-500'
                  }
                `}>
                  {count}
                </span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Search bar */}
      <form onSubmit={handleSearch} className="flex gap-2">
        <div className="relative">
          <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <Input
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search by title…"
            className="w-64 pl-9"
          />
        </div>
        <Button type="submit" variant="secondary" size="sm">Search</Button>
        {search && (
          <Button type="button" variant="ghost" size="sm" onClick={() => { setSearch(''); setSearchInput(''); }}>
            Clear
          </Button>
        )}
      </form>

      {/* Table */}
      {loading ? (
        <div className="flex items-center gap-2 text-sm text-slate-500">
          <Loader2 className="h-4 w-4 animate-spin" /> Loading records…
        </div>
      ) : error ? (
        <p className="text-sm text-red-600">{error}</p>
      ) : visibleRecords.length === 0 ? (
        <div className="flex flex-col items-center gap-3 rounded-xl border border-dashed border-slate-300 py-16 text-center">
          <Database className="h-8 w-8 text-slate-400" />
          <p className="text-slate-500">No records found. Try adjusting your search or create a new record.</p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
          <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50 text-xs font-semibold uppercase tracking-wide text-slate-500">
                <th className="px-4 py-3 text-left">Title</th>
                {activeTab === 'all' && <th className="px-4 py-3 text-left">Type</th>}
                <th className="px-4 py-3 text-left">Content</th>
                <th className="w-10 px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {visibleRecords.map((record) => (
                <tr key={record.id} className="group hover:bg-slate-50 transition-colors">
                  <td className="max-w-xs px-4 py-3 font-medium text-slate-900">
                    <span className="line-clamp-1">{record.title}</span>
                  </td>
                  {activeTab === 'all' && (
                    <td className="px-4 py-3">
                      <TypeBadge type={record.type} />
                    </td>
                  )}
                  <td className="max-w-sm px-4 py-3 text-slate-500">
                    <span className="line-clamp-1">{record.content ?? '—'}</span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      disabled={deletingId === record.id}
                      onClick={() => handleDelete(record.id)}
                      className="invisible rounded p-1 text-slate-400 hover:bg-red-50 hover:text-red-500 group-hover:visible transition-colors"
                      title="Delete record"
                    >
                      {deletingId === record.id
                        ? <Loader2 className="h-4 w-4 animate-spin" />
                        : <Trash2 className="h-4 w-4" />}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          </div>
          <div className="border-t border-slate-100 px-4 py-2 text-xs text-slate-400">
            Showing {visibleRecords.length} record{visibleRecords.length !== 1 ? 's' : ''}
          </div>
        </div>
      )}
    </div>
  );
}
