


import { supabaseBrowser } from '@/lib/supabase';

const API_BASE = 'http://localhost:8000/api/v1';

export async function fetchWithAuth(endpoint: string, options: RequestInit = {}) {
  const { data: { session } } = await supabaseBrowser.auth.getSession();
  const token = session?.access_token;
  
  if (!token) {
    window.location.href = '/';
    throw new Error('Not authenticated');
  }
  
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });
  
  if (response.status === 401) {
    await supabaseBrowser.auth.signOut();
    window.location.href = '/';
    throw new Error('Session expired - please sign in again');
  }
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `API error: ${response.status}`);
  }
  
  return response.json();
}

// Projects API
export const projectsApi = {
  getAll: () => fetchWithAuth('/dashboard/projects'),
  get: (id: string) => fetchWithAuth(`/dashboard/projects/${id}`),
  create: (data: { name: string; description?: string }) => 
    fetchWithAuth('/dashboard/projects', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  delete: (id: string) => 
    fetchWithAuth(`/dashboard/projects/${id}`, {
      method: 'DELETE',
    }),
  getConversations: (projectId: string) => 
    fetchWithAuth(`/dashboard/projects/${projectId}/conversations`),
};

// Cloud Dashboard API — all 9 sections
export const cloudApi = {
  // 1. Overview
  overview: (projectId: string) =>
    fetchWithAuth(`/cloud/${projectId}/overview`),

  // 2. Database
  listTables: (projectId: string) =>
    fetchWithAuth(`/cloud/${projectId}/tables`),
  getRows: (projectId: string, table: string, limit = 50, offset = 0) =>
    fetchWithAuth(`/cloud/${projectId}/tables/${table}/rows?limit=${limit}&offset=${offset}`),
  insertRow: (projectId: string, table: string, data: Record<string, any>) =>
    fetchWithAuth(`/cloud/${projectId}/tables/${table}/rows`, {
      method: 'POST',
      body: JSON.stringify({ data }),
    }),
  updateRow: (projectId: string, table: string, rowId: string, data: Record<string, any>) =>
    fetchWithAuth(`/cloud/${projectId}/tables/${table}/rows/${rowId}`, {
      method: 'PATCH',
      body: JSON.stringify({ data }),
    }),
  deleteRow: (projectId: string, table: string, rowId: string) =>
    fetchWithAuth(`/cloud/${projectId}/tables/${table}/rows/${rowId}`, {
      method: 'DELETE',
    }),

  // 3. SQL Editor
  runSql: (projectId: string, sql: string) =>
    fetchWithAuth(`/cloud/${projectId}/sql`, {
      method: 'POST',
      body: JSON.stringify({ sql }),
    }),

  // 4. Users
  listUsers: (projectId: string, page = 1, perPage = 50) =>
    fetchWithAuth(`/cloud/${projectId}/users?page=${page}&per_page=${perPage}`),
  deleteUser: (projectId: string, uid: string) =>
    fetchWithAuth(`/cloud/${projectId}/users/${uid}`, { method: 'DELETE' }),

  // 5. Storage
  listBuckets: (projectId: string) =>
    fetchWithAuth(`/cloud/${projectId}/storage/buckets`),
  listFiles: (projectId: string, bucket: string, prefix = '') =>
    fetchWithAuth(`/cloud/${projectId}/storage/${bucket}/files?prefix=${encodeURIComponent(prefix)}`),
  getSignedUrl: (projectId: string, bucket: string, path: string) =>
    fetchWithAuth(`/cloud/${projectId}/storage/${bucket}/sign?path=${encodeURIComponent(path)}`),
  deleteFile: (projectId: string, bucket: string, path: string) =>
    fetchWithAuth(`/cloud/${projectId}/storage/${bucket}/files?path=${encodeURIComponent(path)}`, {
      method: 'DELETE',
    }),

  // 6. Logs
  getLogs: (projectId: string, logType = 'api', limit = 100) =>
    fetchWithAuth(`/cloud/${projectId}/logs?log_type=${logType}&limit=${limit}`),

  // 7. Edge Functions
  listFunctions: (projectId: string) =>
    fetchWithAuth(`/cloud/${projectId}/functions`),
  invokeFunction: (projectId: string, fnName: string, payload: Record<string, any> = {}) =>
    fetchWithAuth(`/cloud/${projectId}/functions/${fnName}/invoke`, {
      method: 'POST',
      body: JSON.stringify({ payload }),
    }),

  // 8. Secrets
  listSecrets: (projectId: string) =>
    fetchWithAuth(`/cloud/${projectId}/secrets`),
  upsertSecret: (projectId: string, name: string, value: string) =>
    fetchWithAuth(`/cloud/${projectId}/secrets`, {
      method: 'POST',
      body: JSON.stringify({ name, value }),
    }),
  deleteSecret: (projectId: string, name: string) =>
    fetchWithAuth(`/cloud/${projectId}/secrets/${name}`, { method: 'DELETE' }),
};