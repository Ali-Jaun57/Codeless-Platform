'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { supabaseBrowser } from '@/lib/supabase';
import { projectsApi } from '@/lib/api/client';
import ChatClient from '@/app/components/ChatClient/ChatClient';

export default function ChatPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.projectId as string;
  
  const [project, setProject] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadProject() {
      try {
        setLoading(true);
        setError(null);
        
        // Check authentication
        const { data: { user } } = await supabaseBrowser.auth.getUser();
        if (!user) {
          router.push('/');
          return;
        }
        
        // Load project details and conversation history
        const projectData = await projectsApi.get(projectId);
        setProject(projectData);
        
      } catch (error: any) {
        console.error('Error loading project:', error);
        if (error.message?.includes('404') || error.message?.includes('not found')) {
          setError('Project not found');
        } else {
          setError('Failed to load project');
        }
      } finally {
        setLoading(false);
      }
    }
    
    if (projectId) {
      loadProject();
    }
  }, [projectId, router]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="h-12 w-12 animate-spin rounded-full border-4 border-blue-500 border-t-transparent mx-auto mb-4" />
          <p className="text-slate-400">Loading project...</p>
        </div>
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-white mb-2">Project Not Found</h2>
          <p className="text-slate-400 mb-6">{error || 'This project may have been deleted.'}</p>
          <button
            onClick={() => router.push('/dashboard')}
            className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all"
          >
            Return to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return <ChatClient projectId={projectId} project={project} />;
}