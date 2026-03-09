'use client';


import { useState, useEffect, useCallback, useRef } from 'react';
import { fetchWithAuth } from '@/lib/api/client';
import {
  LayoutDashboard, Database, Terminal, Users, HardDrive,
  FileText, Zap, Sparkles, KeyRound, RefreshCw, Trash2,
  ChevronRight, Table, AlertCircle, Loader2, Server,
  Play, Plus, X, Eye, EyeOff, Copy, Check, ExternalLink,
  FolderOpen, File, ChevronDown, ChevronUp, Search,
} from 'lucide-react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';

// ── Types ─────────────────────────────────────────────────────────────────────

interface CloudDashboardProps {
  projectId: string;
  supabaseRef: string;
}

type Section =
  | 'overview' | 'database' | 'sql' | 'users'
  | 'storage' | 'logs' | 'functions' | 'ai' | 'secrets';

const SECTIONS: { id: Section; label: string; icon: React.ElementType; color: string }[] = [
  { id: 'overview',   label: 'Overview',        icon: LayoutDashboard, color: 'text-slate-300' },
  { id: 'database',   label: 'Database',         icon: Database,        color: 'text-emerald-400' },
  { id: 'sql',        label: 'SQL Editor',       icon: Terminal,        color: 'text-cyan-400' },
  { id: 'users',      label: 'Users',            icon: Users,           color: 'text-blue-400' },
  { id: 'storage',    label: 'Storage',          icon: HardDrive,       color: 'text-amber-400' },
  { id: 'logs',       label: 'Logs',             icon: FileText,        color: 'text-orange-400' },
  { id: 'functions',  label: 'Edge Functions',   icon: Zap,             color: 'text-yellow-400' },
  { id: 'ai',         label: 'AI',               icon: Sparkles,        color: 'text-violet-400' },
  { id: 'secrets',    label: 'Secrets',          icon: KeyRound,        color: 'text-rose-400' },
];

// ── Shared micro-components ───────────────────────────────────────────────────

function Err({ msg }: { msg: string }) {
  return (
    <div className="flex items-start gap-2 rounded-lg bg-red-500/10 border border-red-500/20 px-3 py-2.5 text-xs text-red-400">
      <AlertCircle className="h-3.5 w-3.5 mt-0.5 shrink-0" />
      <span className="break-words">{msg}</span>
    </div>
  );
}

function Spin({ label = 'Loading…' }: { label?: string }) {
  return (
    <div className="flex items-center gap-2 text-slate-500 text-xs py-8 justify-center">
      <Loader2 className="h-4 w-4 animate-spin" />
      {label}
    </div>
  );
}

function Empty({ icon: Icon, msg }: { icon: React.ElementType; msg: string }) {
  return (
    <div className="flex flex-col items-center gap-2 py-12 text-slate-600">
      <Icon className="h-7 w-7 opacity-30" />
      <span className="text-xs">{msg}</span>
    </div>
  );
}

function SectionHeader({ title, action }: { title: string; action?: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between mb-3 shrink-0">
      <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">{title}</h3>
      {action}
    </div>
  );
}

function RefreshBtn({ onClick }: { onClick: () => void }) {
  return (
    <button onClick={onClick} className="text-slate-600 hover:text-slate-300 transition-colors" title="Refresh">
      <RefreshCw className="h-3.5 w-3.5" />
    </button>
  );
}

function StatCard({ label, value, icon: Icon, color }: { label: string; value: number | string; icon: React.ElementType; color: string }) {
  return (
    <div className="rounded-lg border border-slate-700/50 bg-slate-800/40 px-4 py-3 flex items-center gap-3">
      <div className={`${color} opacity-60`}><Icon className="h-5 w-5" /></div>
      <div>
        <div className="text-lg font-bold text-white leading-none">{value}</div>
        <div className="text-[10px] text-slate-500 mt-0.5">{label}</div>
      </div>
    </div>
  );
}

// ── 1. OVERVIEW ───────────────────────────────────────────────────────────────

function OverviewSection({ projectId, supabaseRef }: { projectId: string; supabaseRef: string }) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true); setErr(null);
    try {
      const d = await fetchWithAuth(`/cloud/${projectId}/overview`);
      setData(d);
    } catch (e: any) { setErr(e.message); }
    finally { setLoading(false); }
  }, [projectId]);

  useEffect(() => { load(); }, [load]);

  if (loading) return <Spin label="Loading overview…" />;
  if (err) return <Err msg={err} />;

  return (
    <div className="space-y-4">
      <SectionHeader title="Project Overview" action={<RefreshBtn onClick={load} />} />

      <div className="grid grid-cols-2 gap-2">
        <StatCard label="Tables"         value={data?.table_count ?? 0}    icon={Database}   color="text-emerald-400" />
        <StatCard label="Auth Users"     value={data?.user_count ?? 0}     icon={Users}      color="text-blue-400" />
        <StatCard label="Buckets"        value={data?.bucket_count ?? 0}   icon={HardDrive}  color="text-amber-400" />
        <StatCard label="Edge Functions" value={data?.function_count ?? 0} icon={Zap}        color="text-yellow-400" />
      </div>

      <div className="rounded-lg border border-slate-700/50 bg-slate-800/30 px-4 py-3 space-y-2">
        <p className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider">Project Details</p>
        <div className="flex items-center justify-between text-xs">
          <span className="text-slate-500">Ref</span>
          <span className="font-mono text-slate-300">{supabaseRef}</span>
        </div>
        <div className="flex items-center justify-between text-xs">
          <span className="text-slate-500">URL</span>
          <a
            href={`https://${supabaseRef}.supabase.co`}
            target="_blank"
            rel="noreferrer"
            className="text-blue-400 hover:text-blue-300 flex items-center gap-1 transition-colors"
          >
            Open <ExternalLink className="h-3 w-3" />
          </a>
        </div>
        <div className="flex items-center justify-between text-xs">
          <span className="text-slate-500">Dashboard</span>
          <a
            href={`https://supabase.com/dashboard/project/${supabaseRef}`}
            target="_blank"
            rel="noreferrer"
            className="text-blue-400 hover:text-blue-300 flex items-center gap-1 transition-colors"
          >
            Supabase Studio <ExternalLink className="h-3 w-3" />
          </a>
        </div>
      </div>
    </div>
  );
}

// ── 2. DATABASE ───────────────────────────────────────────────────────────────

const PAGE = 50;

function DatabaseSection({ projectId }: { projectId: string }) {
  const [tables, setTables] = useState<any[]>([]);
  const [sel, setSel] = useState<string | null>(null);
  const [rows, setRows] = useState<any[]>([]);
  const [cols, setCols] = useState<string[]>([]);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(false);
  const [rowsLoading, setRowsLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [rowErr, setRowErr] = useState<string | null>(null);
  const [showInsert, setShowInsert] = useState(false);
  const [insertJson, setInsertJson] = useState('{\n  \n}');
  const [editingRow, setEditingRow] = useState<{ id: string; data: any } | null>(null);

  const loadTables = useCallback(async () => {
    setLoading(true); setErr(null);
    try {
      const d = await fetchWithAuth(`/cloud/${projectId}/tables`);
      setTables(d.tables || []);
    } catch (e: any) { setErr(e.message); }
    finally { setLoading(false); }
  }, [projectId]);

  const loadRows = useCallback(async (table: string, off = 0) => {
    setRowsLoading(true); setRowErr(null);
    try {
      const d = await fetchWithAuth(`/cloud/${projectId}/tables/${table}/rows?limit=${PAGE}&offset=${off}`);
      const r = d.rows || [];
      setRows(r);
      setCols(r.length > 0 ? Object.keys(r[0]) : (tables.find(t => t.name === table)?.columns || []));
      setOffset(off);
    } catch (e: any) { setRowErr(e.message); }
    finally { setRowsLoading(false); }
  }, [projectId, tables]);

  const handleInsert = async () => {
    if (!sel) return;
    try {
      const parsed = JSON.parse(insertJson);
      await fetchWithAuth(`/cloud/${projectId}/tables/${sel}/rows`, {
        method: 'POST', body: JSON.stringify({ data: parsed }),
      });
      setShowInsert(false);
      setInsertJson('{\n  \n}');
      loadRows(sel, offset);
    } catch (e: any) { alert(e.message); }
  };

  const handleDelete = async (rowId: unknown) => {
    if (!sel || !confirm('Delete this row?')) return;
    try {
      await fetchWithAuth(`/cloud/${projectId}/tables/${sel}/rows/${rowId}`, { method: 'DELETE' });
      loadRows(sel, offset);
    } catch (e: any) { alert(e.message); }
  };

  const handleUpdate = async () => {
    if (!sel || !editingRow) return;
    try {
      await fetchWithAuth(`/cloud/${projectId}/tables/${sel}/rows/${editingRow.id}`, {
        method: 'PATCH', body: JSON.stringify({ data: editingRow.data }),
      });
      setEditingRow(null);
      loadRows(sel, offset);
    } catch (e: any) { alert(e.message); }
  };

  useEffect(() => { loadTables(); }, [loadTables]);

  const renderCellValue = (v: unknown) => {
    if (v === null || v === undefined) return <span className="text-slate-600 italic">null</span>;
    if (typeof v === 'boolean') return <span className={v ? 'text-emerald-400' : 'text-slate-500'}>{String(v)}</span>;
    if (typeof v === 'object') return <span className="text-violet-300 font-mono">{JSON.stringify(v).slice(0, 60)}</span>;
    const s = String(v);
    return <span title={s}>{s.length > 60 ? s.slice(0, 60) + '…' : s}</span>;
  };

  if (loading) return <Spin label="Loading tables…" />;
  if (err) return <Err msg={err} />;

  return (
    <div className="flex h-full gap-0 min-h-0">
      {/* Sidebar */}
      <div className="w-40 shrink-0 border-r border-slate-700/40 pr-1 flex flex-col">
        <div className="flex items-center justify-between px-2 py-1.5 mb-1">
          <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">Tables</span>
          <RefreshBtn onClick={loadTables} />
        </div>
        <ScrollArea className="flex-1">
          {tables.length === 0
            ? <p className="px-2 text-[10px] text-slate-600 italic">No tables</p>
            : tables.map(t => (
              <button
                key={t.name}
                onClick={() => { setSel(t.name); loadRows(t.name, 0); setShowInsert(false); }}
                className={`w-full flex items-center gap-1.5 px-2 py-1.5 rounded text-xs text-left transition-colors ${
                  sel === t.name
                    ? 'bg-emerald-600/20 text-emerald-300 font-medium'
                    : 'text-slate-400 hover:bg-slate-700/40 hover:text-slate-200'
                }`}
              >
                <Table className="h-3 w-3 shrink-0" />
                <span className="truncate">{t.name}</span>
              </button>
            ))
          }
        </ScrollArea>
      </div>

      {/* Main panel */}
      <div className="flex-1 min-w-0 pl-3 flex flex-col min-h-0">
        {!sel ? (
          <Empty icon={Database} msg="Select a table" />
        ) : rowsLoading ? (
          <Spin label={`Loading ${sel}…`} />
        ) : (
          <>
            {/* Table toolbar */}
            <div className="flex items-center justify-between mb-2 shrink-0">
              <span className="text-xs font-semibold text-slate-200">{sel}</span>
              <div className="flex items-center gap-2">
                <span className="text-[10px] text-slate-600">{rows.length} rows</span>
                <button
                  onClick={() => setShowInsert(!showInsert)}
                  className="flex items-center gap-1 text-[10px] px-2 py-1 rounded bg-emerald-600/20 text-emerald-400 hover:bg-emerald-600/30 transition-colors"
                >
                  <Plus className="h-3 w-3" /> Insert
                </button>
                <RefreshBtn onClick={() => loadRows(sel, offset)} />
              </div>
            </div>

            {rowErr && <Err msg={rowErr} />}

            {/* Insert form */}
            {showInsert && (
              <div className="mb-2 rounded-lg border border-slate-700/60 bg-slate-800/60 p-3 shrink-0">
                <p className="text-[10px] text-slate-500 mb-1.5 font-semibold uppercase">New Row (JSON)</p>
                <Textarea
                  value={insertJson}
                  onChange={e => setInsertJson(e.target.value)}
                  className="font-mono text-[10px] bg-slate-900/60 border-slate-700 text-slate-300 h-20 resize-none"
                />
                <div className="flex gap-2 mt-2">
                  <Button size="sm" onClick={handleInsert} className="h-6 text-[10px] bg-emerald-600/80 hover:bg-emerald-600 text-white">Insert</Button>
                  <Button size="sm" variant="ghost" onClick={() => setShowInsert(false)} className="h-6 text-[10px] text-slate-400">Cancel</Button>
                </div>
              </div>
            )}

            {/* Edit row modal */}
            {editingRow && (
              <div className="mb-2 rounded-lg border border-blue-500/30 bg-slate-800/60 p-3 shrink-0">
                <p className="text-[10px] text-blue-400 mb-1.5 font-semibold uppercase">Edit Row {editingRow.id}</p>
                <Textarea
                  value={JSON.stringify(editingRow.data, null, 2)}
                  onChange={e => { try { setEditingRow({ ...editingRow, data: JSON.parse(e.target.value) }); } catch {} }}
                  className="font-mono text-[10px] bg-slate-900/60 border-slate-700 text-slate-300 h-24 resize-none"
                />
                <div className="flex gap-2 mt-2">
                  <Button size="sm" onClick={handleUpdate} className="h-6 text-[10px] bg-blue-600/80 hover:bg-blue-600 text-white">Save</Button>
                  <Button size="sm" variant="ghost" onClick={() => setEditingRow(null)} className="h-6 text-[10px] text-slate-400">Cancel</Button>
                </div>
              </div>
            )}

            {/* Rows table */}
            {rows.length === 0 ? (
              <Empty icon={Table} msg="No rows yet" />
            ) : (
              <ScrollArea className="flex-1 min-h-0">
                <div className="overflow-x-auto">
                  <table className="w-full text-[11px]">
                    <thead>
                      <tr className="border-b border-slate-700/60">
                        {cols.map(c => (
                          <th key={c} className="px-2 py-1.5 text-left text-slate-500 font-medium whitespace-nowrap">{c}</th>
                        ))}
                        <th className="px-2 py-1.5 text-right text-slate-500 font-medium">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {rows.map((row, i) => (
                        <tr key={i} className="border-b border-slate-800/50 hover:bg-slate-800/25 transition-colors group">
                          {cols.map(c => (
                            <td key={c} className="px-2 py-1.5 text-slate-300 max-w-[160px] truncate">
                              {renderCellValue(row[c])}
                            </td>
                          ))}
                          <td className="px-2 py-1.5 text-right">
                            <div className="flex items-center justify-end gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                              <button
                                onClick={() => setEditingRow({ id: row['id'], data: { ...row } })}
                                className="text-blue-500/70 hover:text-blue-400 transition-colors"
                                title="Edit"
                              >
                                <Terminal className="h-3 w-3" />
                              </button>
                              <button
                                onClick={() => handleDelete(row['id'])}
                                className="text-red-500/70 hover:text-red-400 transition-colors"
                                title="Delete"
                              >
                                <Trash2 className="h-3 w-3" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </ScrollArea>
            )}

            {/* Pagination */}
            {rows.length === PAGE && (
              <div className="flex items-center gap-2 mt-2 shrink-0">
                <Button variant="outline" size="sm" disabled={offset === 0} onClick={() => loadRows(sel, Math.max(0, offset - PAGE))} className="h-6 text-[10px] border-slate-700 text-slate-400">← Prev</Button>
                <span className="text-[10px] text-slate-600">{offset + 1}–{offset + rows.length}</span>
                <Button variant="outline" size="sm" onClick={() => loadRows(sel, offset + PAGE)} className="h-6 text-[10px] border-slate-700 text-slate-400">Next →</Button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

// ── 3. SQL EDITOR ─────────────────────────────────────────────────────────────

const SQL_EXAMPLES = [
  'SELECT * FROM auth.users LIMIT 10;',
  'SELECT table_name FROM information_schema.tables WHERE table_schema = \'public\';',
  'SELECT COUNT(*) FROM your_table;',
];

function SqlSection({ projectId }: { projectId: string }) {
  const [sql, setSql] = useState('-- Write SQL here\nSELECT 1;');
  const [result, setResult] = useState<any>(null);
  const [running, setRunning] = useState(false);

  const run = async () => {
    setRunning(true); setResult(null);
    try {
      const d = await fetchWithAuth(`/cloud/${projectId}/sql`, {
        method: 'POST', body: JSON.stringify({ sql }),
      });
      setResult(d);
    } catch (e: any) {
      setResult({ error: e.message, rows: [], columns: [], row_count: 0 });
    } finally { setRunning(false); }
  };

  return (
    <div className="flex flex-col h-full gap-2 min-h-0">
      {/* Editor */}
      <div className="shrink-0">
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider">Query</span>
          <div className="flex items-center gap-2">
            <select
              className="text-[10px] bg-slate-800 border border-slate-700 text-slate-400 rounded px-1.5 py-0.5"
              onChange={e => { if (e.target.value) setSql(e.target.value); }}
              defaultValue=""
            >
              <option value="" disabled>Examples…</option>
              {SQL_EXAMPLES.map((ex, i) => (
                <option key={i} value={ex}>{ex.slice(0, 50)}…</option>
              ))}
            </select>
            <Button
              size="sm" onClick={run} disabled={running}
              className="h-6 text-[10px] bg-cyan-600/80 hover:bg-cyan-600 text-white flex items-center gap-1"
            >
              {running ? <Loader2 className="h-3 w-3 animate-spin" /> : <Play className="h-3 w-3" />}
              Run
            </Button>
          </div>
        </div>
        <Textarea
          value={sql}
          onChange={e => setSql(e.target.value)}
          onKeyDown={e => { if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') run(); }}
          className="font-mono text-xs bg-slate-900/80 border-slate-700/60 text-slate-200 h-28 resize-none focus:ring-1 focus:ring-cyan-500/40"
          placeholder="-- Ctrl+Enter to run"
          spellCheck={false}
        />
        <p className="text-[10px] text-slate-600 mt-1">Ctrl/Cmd + Enter to run</p>
      </div>

      {/* Results */}
      <div className="flex-1 min-h-0 rounded-lg border border-slate-700/40 bg-slate-900/60 overflow-hidden">
        {!result ? (
          <Empty icon={Terminal} msg="Run a query to see results" />
        ) : result.error ? (
          <div className="p-3">
            <p className="text-[10px] text-rose-400 font-semibold uppercase mb-1.5">Error</p>
            <pre className="text-[10px] text-rose-300 whitespace-pre-wrap break-words font-mono">{result.error}</pre>
          </div>
        ) : result.rows.length === 0 ? (
          <div className="p-3">
            <p className="text-[10px] text-slate-500">Query ran successfully — 0 rows returned.</p>
          </div>
        ) : (
          <>
            <div className="px-3 py-1.5 border-b border-slate-700/40 flex items-center justify-between">
              <span className="text-[10px] text-slate-500">{result.row_count} row{result.row_count !== 1 ? 's' : ''}</span>
            </div>
            <ScrollArea className="h-full">
              <div className="overflow-x-auto">
                <table className="w-full text-[10px]">
                  <thead>
                    <tr className="border-b border-slate-700/40">
                      {result.columns.map((c: string) => (
                        <th key={c} className="px-2 py-1.5 text-left text-slate-500 font-medium whitespace-nowrap">{c}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {result.rows.map((row: any, i: number) => (
                      <tr key={i} className="border-b border-slate-800/50 hover:bg-slate-800/20">
                        {result.columns.map((c: string) => (
                          <td key={c} className="px-2 py-1.5 text-slate-300 font-mono max-w-[200px] truncate">
                            {row[c] === null ? <span className="text-slate-600 italic">null</span> : String(row[c])}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </ScrollArea>
          </>
        )}
      </div>
    </div>
  );
}

// ── 4. USERS ──────────────────────────────────────────────────────────────────

function UsersSection({ projectId }: { projectId: string }) {
  const [users, setUsers] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [search, setSearch] = useState('');

  const load = useCallback(async (p = 1) => {
    setLoading(true); setErr(null);
    try {
      const d = await fetchWithAuth(`/cloud/${projectId}/users?page=${p}&per_page=50`);
      setUsers(d.users || []);
      setTotal(d.total || 0);
      setPage(p);
    } catch (e: any) { setErr(e.message); }
    finally { setLoading(false); }
  }, [projectId]);

  useEffect(() => { load(1); }, [load]);

  const handleDelete = async (uid: string, email?: string) => {
    if (!confirm(`Delete ${email || uid}? Cannot be undone.`)) return;
    try {
      await fetchWithAuth(`/cloud/${projectId}/users/${uid}`, { method: 'DELETE' });
      load(page);
    } catch (e: any) { alert(e.message); }
  };

  const fmt = (iso?: string) => iso ? new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: '2-digit', hour: '2-digit', minute: '2-digit' }) : '—';

  const filtered = users.filter(u => !search || u.email?.toLowerCase().includes(search.toLowerCase()) || u.id?.includes(search));

  return (
    <div className="flex flex-col h-full gap-2 min-h-0">
      <div className="flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500">{total} users</span>
          <div className="relative">
            <Search className="h-3 w-3 absolute left-2 top-1/2 -translate-y-1/2 text-slate-600" />
            <Input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search…"
              className="h-6 w-48 text-[10px] pl-6 bg-slate-800/60 border-slate-700 text-slate-300 placeholder:text-slate-600" />
          </div>
        </div>
        <RefreshBtn onClick={() => load(page)} />
      </div>

      {loading ? <Spin label="Loading users…" /> : err ? <Err msg={err} /> : (
        <ScrollArea className="flex-1 min-h-0">
          {filtered.length === 0 ? <Empty icon={Users} msg={search ? 'No matches' : 'No users yet'} /> : (
            <table className="w-full text-[11px]">
              <thead>
                <tr className="border-b border-slate-700/60">
                  {['Email', 'ID', 'Signed up', 'Last login', 'Status', ''].map(h => (
                    <th key={h} className={`px-2 py-1.5 text-left text-slate-500 font-medium ${h === '' ? 'text-right' : ''}`}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map(u => (
                  <tr key={u.id} className="border-b border-slate-800/50 hover:bg-slate-800/25 group">
                    <td className="px-2 py-1.5 text-slate-200 font-medium">{u.email || <span className="text-slate-600 italic">no email</span>}</td>
                    <td className="px-2 py-1.5 text-slate-500 font-mono text-[10px]">{u.id?.slice(0, 8)}…</td>
                    <td className="px-2 py-1.5 text-slate-400">{fmt(u.created_at)}</td>
                    <td className="px-2 py-1.5 text-slate-400">{fmt(u.last_sign_in_at)}</td>
                    <td className="px-2 py-1.5">
                      <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[9px] font-medium ${
                        u.confirmed_at ? 'bg-emerald-500/10 text-emerald-400' : 'bg-amber-500/10 text-amber-400'
                      }`}>
                        <span className={`h-1 w-1 rounded-full ${u.confirmed_at ? 'bg-emerald-400' : 'bg-amber-400'}`} />
                        {u.confirmed_at ? 'Verified' : 'Pending'}
                      </span>
                    </td>
                    <td className="px-2 py-1.5 text-right">
                      <button onClick={() => handleDelete(u.id, u.email)}
                        className="opacity-0 group-hover:opacity-100 text-red-500/70 hover:text-red-400 transition-all">
                        <Trash2 className="h-3 w-3" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </ScrollArea>
      )}

      {!loading && total > 50 && (
        <div className="flex items-center gap-2 shrink-0">
          <Button variant="outline" size="sm" disabled={page === 1} onClick={() => load(page - 1)} className="h-6 text-[10px] border-slate-700 text-slate-400">← Prev</Button>
          <span className="text-[10px] text-slate-600">Page {page} of {Math.ceil(total / 50)}</span>
          <Button variant="outline" size="sm" disabled={page * 50 >= total} onClick={() => load(page + 1)} className="h-6 text-[10px] border-slate-700 text-slate-400">Next →</Button>
        </div>
      )}
    </div>
  );
}

// ── 5. STORAGE ────────────────────────────────────────────────────────────────

function StorageSection({ projectId }: { projectId: string }) {
  const [buckets, setBuckets] = useState<any[]>([]);
  const [selBucket, setSelBucket] = useState<string | null>(null);
  const [files, setFiles] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [filesLoading, setFilesLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const loadBuckets = useCallback(async () => {
    setLoading(true); setErr(null);
    try {
      const d = await fetchWithAuth(`/cloud/${projectId}/storage/buckets`);
      setBuckets(d.buckets || []);
    } catch (e: any) { setErr(e.message); }
    finally { setLoading(false); }
  }, [projectId]);

  const loadFiles = useCallback(async (bucket: string) => {
    setFilesLoading(true);
    try {
      const d = await fetchWithAuth(`/cloud/${projectId}/storage/${bucket}/files`);
      setFiles(d.files || []);
    } catch (e: any) { setErr(e.message); }
    finally { setFilesLoading(false); }
  }, [projectId]);

  const handleSignedUrl = async (bucket: string, path: string) => {
    try {
      const d = await fetchWithAuth(`/cloud/${projectId}/storage/${bucket}/sign?path=${encodeURIComponent(path)}`);
      window.open(d.url, '_blank');
    } catch (e: any) { alert(e.message); }
  };

  const handleDeleteFile = async (path: string) => {
    if (!selBucket || !confirm(`Delete ${path}?`)) return;
    try {
      await fetchWithAuth(`/cloud/${projectId}/storage/${selBucket}/files?path=${encodeURIComponent(path)}`, { method: 'DELETE' });
      loadFiles(selBucket);
    } catch (e: any) { alert(e.message); }
  };

  useEffect(() => { loadBuckets(); }, [loadBuckets]);

  const fmtSize = (bytes?: number) => {
    if (!bytes) return '—';
    if (bytes < 1024) return `${bytes}B`;
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)}KB`;
    return `${(bytes / 1048576).toFixed(1)}MB`;
  };

  return (
    <div className="flex h-full gap-0 min-h-0">
      {/* Bucket sidebar */}
      <div className="w-40 shrink-0 border-r border-slate-700/40 pr-1">
        <div className="flex items-center justify-between px-2 py-1.5 mb-1">
          <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">Buckets</span>
          <RefreshBtn onClick={loadBuckets} />
        </div>
        {loading ? <Spin /> : err ? <Err msg={err} /> : buckets.length === 0
          ? <p className="px-2 text-[10px] text-slate-600 italic">No buckets</p>
          : buckets.map(b => (
            <button key={b.id || b.name}
              onClick={() => { setSelBucket(b.name); loadFiles(b.name); }}
              className={`w-full flex items-center gap-1.5 px-2 py-1.5 rounded text-xs text-left transition-colors ${
                selBucket === b.name ? 'bg-amber-600/20 text-amber-300 font-medium' : 'text-slate-400 hover:bg-slate-700/40 hover:text-slate-200'
              }`}
            >
              <HardDrive className="h-3 w-3 shrink-0" />
              <span className="truncate">{b.name}</span>
              {b.public && <span className="ml-auto text-[8px] text-slate-600">pub</span>}
            </button>
          ))
        }
      </div>

      {/* Files */}
      <div className="flex-1 min-w-0 pl-3 flex flex-col min-h-0">
        {!selBucket ? <Empty icon={HardDrive} msg="Select a bucket" /> : filesLoading ? <Spin label="Loading files…" /> : (
          <>
            <div className="flex items-center justify-between mb-2 shrink-0">
              <span className="text-xs font-semibold text-slate-200">{selBucket}</span>
              <div className="flex items-center gap-2">
                <span className="text-[10px] text-slate-600">{files.length} files</span>
                <RefreshBtn onClick={() => loadFiles(selBucket)} />
              </div>
            </div>
            {files.length === 0 ? <Empty icon={File} msg="No files in this bucket" /> : (
              <ScrollArea className="flex-1 min-h-0">
                <table className="w-full text-[11px]">
                  <thead>
                    <tr className="border-b border-slate-700/60">
                      <th className="px-2 py-1.5 text-left text-slate-500 font-medium">Name</th>
                      <th className="px-2 py-1.5 text-left text-slate-500 font-medium">Size</th>
                      <th className="px-2 py-1.5 text-left text-slate-500 font-medium">Type</th>
                      <th className="px-2 py-1.5 text-right text-slate-500 font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {files.map((f, i) => (
                      <tr key={i} className="border-b border-slate-800/50 hover:bg-slate-800/25 group">
                        <td className="px-2 py-1.5 text-slate-300">
                          <div className="flex items-center gap-1.5">
                            {f.id ? <File className="h-3 w-3 text-slate-500 shrink-0" /> : <FolderOpen className="h-3 w-3 text-amber-500 shrink-0" />}
                            <span className="truncate max-w-[160px]">{f.name}</span>
                          </div>
                        </td>
                        <td className="px-2 py-1.5 text-slate-500">{fmtSize(f.metadata?.size)}</td>
                        <td className="px-2 py-1.5 text-slate-500 truncate max-w-[80px]">{f.metadata?.mimetype || '—'}</td>
                        <td className="px-2 py-1.5 text-right">
                          <div className="flex items-center justify-end gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                            {f.id && (
                              <button onClick={() => handleSignedUrl(selBucket, f.name)} className="text-blue-500/70 hover:text-blue-400" title="Open">
                                <ExternalLink className="h-3 w-3" />
                              </button>
                            )}
                            <button onClick={() => handleDeleteFile(f.name)} className="text-red-500/70 hover:text-red-400" title="Delete">
                              <Trash2 className="h-3 w-3" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </ScrollArea>
            )}
          </>
        )}
      </div>
    </div>
  );
}

// ── 6. LOGS ───────────────────────────────────────────────────────────────────

const LOG_TYPES = ['api', 'auth', 'storage', 'realtime', 'postgrest'] as const;
type LogType = typeof LOG_TYPES[number];
const LOG_COLORS: Record<LogType, string> = {
  api: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
  auth: 'text-purple-400 bg-purple-500/10 border-purple-500/20',
  storage: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
  realtime: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
  postgrest: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20',
};

function LogsSection({ projectId }: { projectId: string }) {
  const [logType, setLogType] = useState<LogType>('api');
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const load = useCallback(async (t: LogType) => {
    setLoading(true); setErr(null);
    try {
      const d = await fetchWithAuth(`/cloud/${projectId}/logs?log_type=${t}&limit=100`);
      setLogs(d.logs || []);
    } catch (e: any) { setErr(e.message); }
    finally { setLoading(false); }
  }, [projectId]);

  useEffect(() => { load(logType); }, [load, logType]);

  const fmtTs = (ts?: string) => {
    if (!ts) return '';
    try { return new Date(ts).toISOString().replace('T', ' ').slice(0, 19); }
    catch { return ts; }
  };

  return (
    <div className="flex flex-col h-full gap-2 min-h-0">
      <div className="flex items-center justify-between shrink-0">
        <div className="flex items-center gap-1">
          {LOG_TYPES.map(t => (
            <button key={t} onClick={() => { setLogType(t); load(t); }}
              className={`px-2.5 py-0.5 rounded text-[10px] font-medium border transition-colors ${
                logType === t ? LOG_COLORS[t] : 'text-slate-600 hover:text-slate-400 border-transparent'
              }`}
            >{t}</button>
          ))}
        </div>
        <RefreshBtn onClick={() => load(logType)} />
      </div>

      {loading ? <Spin label="Fetching logs…" /> : err ? <Err msg={err} /> : logs.length === 0
        ? <Empty icon={FileText} msg="No logs for this type" />
        : (
          <ScrollArea className="flex-1 min-h-0 font-mono">
            <div className="space-y-px">
              {logs.map((log, i) => (
                <div key={i} className="flex items-start gap-3 px-2 py-1 rounded hover:bg-slate-800/30 text-[10px] transition-colors">
                  <span className="shrink-0 text-slate-700 w-32">{fmtTs(log.timestamp)}</span>
                  <span className="flex-1 text-slate-300 break-words leading-relaxed">
                    {typeof log.event_message === 'string' ? log.event_message : JSON.stringify(log)}
                  </span>
                </div>
              ))}
            </div>
          </ScrollArea>
        )
      }
    </div>
  );
}

// ── 7. EDGE FUNCTIONS ─────────────────────────────────────────────────────────

function FunctionsSection({ projectId }: { projectId: string }) {
  const [fns, setFns] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [invokeFn, setInvokeFn] = useState<string | null>(null);
  const [payload, setPayload] = useState('{}');
  const [invokeResult, setInvokeResult] = useState<any>(null);
  const [invoking, setInvoking] = useState(false);

  const load = useCallback(async () => {
    setLoading(true); setErr(null);
    try {
      const d = await fetchWithAuth(`/cloud/${projectId}/functions`);
      setFns(d.functions || []);
    } catch (e: any) { setErr(e.message); }
    finally { setLoading(false); }
  }, [projectId]);

  useEffect(() => { load(); }, [load]);

  const handleInvoke = async () => {
    if (!invokeFn) return;
    setInvoking(true); setInvokeResult(null);
    try {
      const p = JSON.parse(payload);
      const d = await fetchWithAuth(`/cloud/${projectId}/functions/${invokeFn}/invoke`, {
        method: 'POST', body: JSON.stringify({ payload: p }),
      });
      setInvokeResult(d);
    } catch (e: any) {
      setInvokeResult({ ok: false, error: e.message });
    } finally { setInvoking(false); }
  };

  return (
    <div className="flex flex-col h-full gap-3 min-h-0">
      <SectionHeader title="Edge Functions" action={<RefreshBtn onClick={load} />} />
      {loading ? <Spin /> : err ? <Err msg={err} /> : fns.length === 0
        ? <Empty icon={Zap} msg="No edge functions deployed" />
        : (
          <ScrollArea className="flex-1 min-h-0">
            <div className="space-y-1.5">
              {fns.map((fn: any) => (
                <div key={fn.id || fn.name} className={`rounded-lg border px-3 py-2.5 ${
                  invokeFn === fn.name ? 'border-yellow-500/30 bg-yellow-500/5' : 'border-slate-700/50 bg-slate-800/30'
                }`}>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs font-semibold text-slate-200">{fn.name}</p>
                      <p className="text-[10px] text-slate-600">{fn.status || fn.slug || '—'}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`text-[9px] px-1.5 py-0.5 rounded-full ${
                        fn.status === 'ACTIVE' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-slate-500/10 text-slate-500'
                      }`}>{fn.status || 'deployed'}</span>
                      <button
                        onClick={() => setInvokeFn(invokeFn === fn.name ? null : fn.name)}
                        className="text-[10px] px-2 py-0.5 rounded bg-yellow-500/10 text-yellow-400 hover:bg-yellow-500/20 transition-colors"
                      >
                        {invokeFn === fn.name ? 'Cancel' : 'Invoke'}
                      </button>
                    </div>
                  </div>

                  {invokeFn === fn.name && (
                    <div className="mt-2 space-y-1.5">
                      <Textarea
                        value={payload}
                        onChange={e => setPayload(e.target.value)}
                        className="font-mono text-[10px] bg-slate-900/60 border-slate-700 text-slate-300 h-16 resize-none"
                        placeholder="JSON payload"
                      />
                      <Button size="sm" onClick={handleInvoke} disabled={invoking}
                        className="h-6 text-[10px] bg-yellow-600/80 hover:bg-yellow-600 text-white flex items-center gap-1">
                        {invoking ? <Loader2 className="h-3 w-3 animate-spin" /> : <Play className="h-3 w-3" />} Run
                      </Button>
                      {invokeResult && (
                        <pre className={`text-[10px] rounded p-2 font-mono whitespace-pre-wrap break-words ${
                          invokeResult.ok ? 'bg-emerald-900/20 text-emerald-300' : 'bg-red-900/20 text-red-300'
                        }`}>
                          {JSON.stringify(invokeResult, null, 2)}
                        </pre>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </ScrollArea>
        )
      }
    </div>
  );
}

// ── 8. AI ─────────────────────────────────────────────────────────────────────

function AiSection({ projectId, supabaseRef }: { projectId: string; supabaseRef: string }) {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<{ role: 'user' | 'ai'; content: string }[]>([]);
  const [loading, setLoading] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  const SYSTEM = `You are an expert Supabase database assistant for project ref "${supabaseRef}". 
Help the user with SQL queries, database design, RLS policies, auth configuration, and Supabase best practices.
When asked to write SQL, write clean, executable PostgreSQL. 
Be concise and technical.`;

  const send = async () => {
    if (!query.trim() || loading) return;
    const userMsg = query.trim();
    setQuery('');
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setLoading(true);

    try {
      const response = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: 'claude-sonnet-4-20250514',
          max_tokens: 1000,
          system: SYSTEM,
          messages: [
            ...messages.map(m => ({ role: m.role === 'ai' ? 'assistant' : 'user', content: m.content })),
            { role: 'user', content: userMsg },
          ],
        }),
      });
      const data = await response.json();
      const reply = data.content?.[0]?.text || 'No response';
      setMessages(prev => [...prev, { role: 'ai', content: reply }]);
    } catch (e: any) {
      setMessages(prev => [...prev, { role: 'ai', content: `Error: ${e.message}` }]);
    } finally {
      setLoading(false);
      setTimeout(() => endRef.current?.scrollIntoView({ behavior: 'smooth' }), 100);
    }
  };

  const STARTERS = [
    'Write RLS policies for a todos table where users can only see their own rows.',
    'Show me how to set up email auth in my app.',
    'How do I query data with React Query + Supabase?',
    'Optimize this query for performance.',
  ];

  return (
    <div className="flex flex-col h-full gap-2 min-h-0">
      <div className="shrink-0">
        <div className="flex items-center gap-1.5 mb-2">
          <Sparkles className="h-3.5 w-3.5 text-violet-400" />
          <span className="text-xs font-semibold text-slate-300">AI Database Assistant</span>
        </div>
        {messages.length === 0 && (
          <div className="grid grid-cols-2 gap-1.5 mb-2">
            {STARTERS.map((s, i) => (
              <button key={i} onClick={() => { setQuery(s); }}
                className="text-left text-[10px] px-2 py-2 rounded-lg border border-slate-700/50 bg-slate-800/30 text-slate-400 hover:bg-slate-800/60 hover:text-slate-300 hover:border-violet-500/30 transition-all leading-relaxed">
                {s}
              </button>
            ))}
          </div>
        )}
      </div>

      <ScrollArea className="flex-1 min-h-0">
        <div className="space-y-2 pr-1">
          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[90%] rounded-lg px-3 py-2 text-xs leading-relaxed ${
                m.role === 'user'
                  ? 'bg-violet-600/30 text-violet-100 border border-violet-500/20'
                  : 'bg-slate-800/60 text-slate-200 border border-slate-700/40'
              }`}>
                <pre className="whitespace-pre-wrap break-words font-sans">{m.content}</pre>
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-slate-800/60 border border-slate-700/40 rounded-lg px-3 py-2">
                <div className="flex items-center gap-1.5">
                  <div className="h-1.5 w-1.5 rounded-full bg-violet-400 animate-bounce [animation-delay:0ms]" />
                  <div className="h-1.5 w-1.5 rounded-full bg-violet-400 animate-bounce [animation-delay:150ms]" />
                  <div className="h-1.5 w-1.5 rounded-full bg-violet-400 animate-bounce [animation-delay:300ms]" />
                </div>
              </div>
            </div>
          )}
          <div ref={endRef} />
        </div>
      </ScrollArea>

      <div className="flex gap-2 shrink-0">
        <Input
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } }}
          placeholder="Ask about SQL, RLS, auth…"
          className="flex-1 h-8 text-xs bg-slate-800/60 border-slate-700 text-slate-200 placeholder:text-slate-600"
          disabled={loading}
        />
        <Button onClick={send} disabled={loading || !query.trim()} size="sm"
          className="h-8 text-xs bg-violet-600/80 hover:bg-violet-600 text-white px-3">
          {loading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5" />}
        </Button>
      </div>
    </div>
  );
}

// ── 9. SECRETS ────────────────────────────────────────────────────────────────

function SecretsSection({ projectId }: { projectId: string }) {
  const [secrets, setSecrets] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [adding, setAdding] = useState(false);
  const [newName, setNewName] = useState('');
  const [newVal, setNewVal] = useState('');
  const [showVals, setShowVals] = useState<Record<string, boolean>>({});
  const [copied, setCopied] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true); setErr(null);
    try {
      const d = await fetchWithAuth(`/cloud/${projectId}/secrets`);
      setSecrets(d.secrets || []);
    } catch (e: any) { setErr(e.message); }
    finally { setLoading(false); }
  }, [projectId]);

  useEffect(() => { load(); }, [load]);

  const handleAdd = async () => {
    if (!newName.trim() || !newVal.trim()) return;
    try {
      await fetchWithAuth(`/cloud/${projectId}/secrets`, {
        method: 'POST', body: JSON.stringify({ name: newName.trim(), value: newVal.trim() }),
      });
      setAdding(false); setNewName(''); setNewVal('');
      load();
    } catch (e: any) { alert(e.message); }
  };

  const handleDelete = async (name: string) => {
    if (!confirm(`Delete secret "${name}"?`)) return;
    try {
      await fetchWithAuth(`/cloud/${projectId}/secrets/${name}`, { method: 'DELETE' });
      load();
    } catch (e: any) { alert(e.message); }
  };

  const copyName = (name: string) => {
    navigator.clipboard.writeText(name);
    setCopied(name);
    setTimeout(() => setCopied(null), 1500);
  };

  return (
    <div className="flex flex-col h-full gap-2 min-h-0">
      <div className="flex items-center justify-between shrink-0">
        <div className="flex items-center gap-1.5">
          <KeyRound className="h-3.5 w-3.5 text-rose-400" />
          <span className="text-xs font-semibold text-slate-300">Edge Function Secrets</span>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => setAdding(!adding)}
            className="flex items-center gap-1 text-[10px] px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 hover:bg-rose-500/20 transition-colors">
            <Plus className="h-3 w-3" /> Add
          </button>
          <RefreshBtn onClick={load} />
        </div>
      </div>

      {adding && (
        <div className="rounded-lg border border-rose-500/20 bg-rose-500/5 p-3 space-y-2 shrink-0">
          <p className="text-[10px] text-rose-400 font-semibold uppercase">New Secret</p>
          <Input value={newName} onChange={e => setNewName(e.target.value)} placeholder="SECRET_NAME"
            className="h-7 text-[10px] font-mono bg-slate-900/60 border-slate-700 text-slate-300 placeholder:text-slate-600" />
          <Input value={newVal} onChange={e => setNewVal(e.target.value)} placeholder="secret value…" type="password"
            className="h-7 text-[10px] bg-slate-900/60 border-slate-700 text-slate-300 placeholder:text-slate-600" />
          <div className="flex gap-2">
            <Button size="sm" onClick={handleAdd} className="h-6 text-[10px] bg-rose-600/80 hover:bg-rose-600 text-white">Save</Button>
            <Button size="sm" variant="ghost" onClick={() => setAdding(false)} className="h-6 text-[10px] text-slate-400">Cancel</Button>
          </div>
        </div>
      )}

      <div className="mb-1 p-2 rounded-lg bg-amber-500/5 border border-amber-500/15">
        <p className="text-[10px] text-amber-400/80">Values are masked for security. Access them in Edge Functions via <code className="font-mono">Deno.env.get('NAME')</code>.</p>
      </div>

      {loading ? <Spin /> : err ? <Err msg={err} /> : secrets.length === 0
        ? <Empty icon={KeyRound} msg="No secrets configured" />
        : (
          <ScrollArea className="flex-1 min-h-0">
            <div className="space-y-1">
              {secrets.map((s, i) => (
                <div key={i} className="flex items-center gap-2 px-3 py-2 rounded-lg border border-slate-700/40 bg-slate-800/30 group hover:border-slate-600/50 transition-colors">
                  <code className="flex-1 text-[11px] text-rose-300 font-mono">{s.name}</code>
                  <span className="text-[10px] text-slate-600 font-mono tracking-widest">••••••••</span>
                  <button onClick={() => copyName(s.name)}
                    className="opacity-0 group-hover:opacity-100 text-slate-600 hover:text-slate-400 transition-all" title="Copy name">
                    {copied === s.name ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
                  </button>
                  <button onClick={() => handleDelete(s.name)}
                    className="opacity-0 group-hover:opacity-100 text-red-500/70 hover:text-red-400 transition-all" title="Delete">
                    <Trash2 className="h-3 w-3" />
                  </button>
                </div>
              ))}
            </div>
          </ScrollArea>
        )
      }
    </div>
  );
}

// ── Root ──────────────────────────────────────────────────────────────────────

export default function CloudDashboard({ projectId, supabaseRef }: CloudDashboardProps) {
  const [active, setActive] = useState<Section>('overview');

  const renderSection = () => {
    switch (active) {
      case 'overview':   return <OverviewSection   projectId={projectId} supabaseRef={supabaseRef} />;
      case 'database':   return <DatabaseSection   projectId={projectId} />;
      case 'sql':        return <SqlSection        projectId={projectId} />;
      case 'users':      return <UsersSection      projectId={projectId} />;
      case 'storage':    return <StorageSection    projectId={projectId} />;
      case 'logs':       return <LogsSection       projectId={projectId} />;
      case 'functions':  return <FunctionsSection  projectId={projectId} />;
      case 'ai':         return <AiSection         projectId={projectId} supabaseRef={supabaseRef} />;
      case 'secrets':    return <SecretsSection    projectId={projectId} />;
    }
  };

  return (
    <div className="h-full flex bg-slate-900 overflow-hidden">
      {/* Sidebar nav */}
      <nav className="w-40 shrink-0 border-r border-slate-700/50 flex flex-col bg-slate-900/80">
        {/* Header */}
        <div className="px-3 py-3 border-b border-slate-700/40">
          <div className="flex items-center gap-2">
            <Server className="h-4 w-4 text-blue-400" />
            <span className="text-xs font-bold text-white">Cloud</span>
          </div>
          <p className="text-[9px] text-slate-600 font-mono mt-0.5 truncate">{supabaseRef}</p>
        </div>

        {/* Nav items */}
        <div className="flex-1 py-2 space-y-0.5 px-1.5">
          {SECTIONS.map(({ id, label, icon: Icon, color }) => (
            <button
              key={id}
              onClick={() => setActive(id)}
              className={`w-full flex items-center gap-2 px-2 py-1.5 rounded-md text-xs text-left transition-all ${
                active === id
                  ? 'bg-slate-700/70 text-white'
                  : 'text-slate-500 hover:bg-slate-800/60 hover:text-slate-300'
              }`}
            >
              <Icon className={`h-3.5 w-3.5 shrink-0 ${active === id ? color : 'text-slate-600'}`} />
              <span className="truncate">{label}</span>
              {active === id && <ChevronRight className="h-3 w-3 ml-auto text-slate-600" />}
            </button>
          ))}
        </div>

        {/* Footer */}
        <div className="px-3 py-2 border-t border-slate-700/40">
          <a
            href={`https://supabase.com/dashboard/project/${supabaseRef}`}
            target="_blank" rel="noreferrer"
            className="flex items-center gap-1.5 text-[10px] text-slate-600 hover:text-slate-400 transition-colors"
          >
            <ExternalLink className="h-3 w-3" />
            Supabase Studio
          </a>
        </div>
      </nav>

      {/* Content */}
      <main className="flex-1 min-w-0 flex flex-col p-4 min-h-0 overflow-hidden">
        {renderSection()}
      </main>
    </div>
  );
}