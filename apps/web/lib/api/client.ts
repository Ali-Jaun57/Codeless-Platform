



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

// ✅ EXPORT projectsApi HERE
export const projectsApi = {
  // Get all projects for current user
  getAll: () => fetchWithAuth('/dashboard/projects'),
  
  // Get single project
  get: (id: string) => fetchWithAuth(`/dashboard/projects/${id}`),
  
  // Create new project
  create: (data: { name: string; description?: string }) => 
    fetchWithAuth('/dashboard/projects', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  
  // Delete project (soft delete)
  delete: (id: string) => 
    fetchWithAuth(`/dashboard/projects/${id}`, {
      method: 'DELETE',
    }),
  
  // Get conversation history for a project
  getConversations: (projectId: string) => 
    fetchWithAuth(`/dashboard/projects/${projectId}/conversations`),
};