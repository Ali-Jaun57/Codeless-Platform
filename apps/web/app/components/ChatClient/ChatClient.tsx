





'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { supabaseBrowser } from '@/lib/supabase';
import { projectsApi } from '@/lib/api/client';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import MessageBubble from './MessageBubble';
import VSCodeDisplay from '../CodeDisplay/VSCodeDisplay';
import { ArrowLeft, Loader2, X, Monitor, Code2, Cloud } from 'lucide-react';
import CloudDashboard from '../CloudDashboard/CloudDashboard';
import './ChatClient.css';

type Message = {
  role: 'user' | 'assistant';
  content: string | React.ReactNode;
  files?: any[];
  preview_url?: string;
};

interface ChatClientProps {
  projectId: string;
  project?: any;  // Make project optional
}

export default function ChatClient({ projectId, project }: ChatClientProps) {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [projectData, setProjectData] = useState<any>(project);
  const [messages, setMessages] = useState<Message[]>([
    { 
      role: 'assistant', 
      content: project?.name 
        ? `Hello! I'm ready to help you build **${project.name}**. Describe what you want to build and I'll generate the code.`
        : `Hello! I'm ready to help you build your app. Describe what you want to build and I'll generate the code.`
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [generatedFiles, setGeneratedFiles] = useState<any[]>([]);
  const [showCodePanel, setShowCodePanel] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string>('');
  const [supabaseRef, setSupabaseRef] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'preview' | 'code' | 'cloud'>('preview');
  
  // Conversation context
  const [conversationContext, setConversationContext] = useState<{
    originalPrompt: string;
    pendingClarification: {
      question: string;
      detectedClass: string;
    } | null;
  }>({
    originalPrompt: '',
    pendingClarification: null
  });

  // Load project data if not provided
  useEffect(() => {
    async function loadProject() {
      if (!project && projectId) {
        try {
          const data = await projectsApi.get(projectId);
          setProjectData(data);
          
          // Update the first message with project name
          setMessages(prev => {
            const newMessages = [...prev];
            newMessages[0] = {
              role: 'assistant',
              content: `Hello! I'm ready to help you build **${data.name}**. Describe what you want to build and I'll generate the code.`
            };
            return newMessages;
          });
        } catch (error) {
          console.error('Error loading project:', error);
        }
      } else if (project) {
        setProjectData(project);
      }
    }
    
    loadProject();
  }, [projectId, project]);


useEffect(() => {
  async function loadConversationHistory() {
    try {
      const data = await projectsApi.getConversations(projectId);
      
      if (data.messages && data.messages.length > 0) {
        // ✅ Format ALL messages - NO FILTERING
        const historyMessages: Message[] = data.messages.map((msg: any) => {
          if (msg.role === 'user') {
            return { 
              role: 'user', 
              content: msg.content 
            };
          } else {
            
            return {
              role: 'assistant',
              content: msg.content,
              files: msg.files || [],
              preview_url: msg.preview_url
            };
          }
        });
        
        console.log('Loaded messages:', historyMessages.length); // Debug log
        setMessages(historyMessages);
        
        // Get latest files and preview
        const lastAssistantMsg = [...data.messages]
          .reverse()
          .find((m: any) => m.role === 'assistant' && m.files?.length > 0);
        
        if (lastAssistantMsg) {
          setGeneratedFiles(lastAssistantMsg.files);
          setPreviewUrl(lastAssistantMsg.preview_url || '');
          setShowCodePanel(true);
        }

        // Restore supabase_ref for Cloud tab (persists across page refreshes)
        try {
          const projData = await projectsApi.get(projectId);
          if (projData?.supabase_ref) {
            setSupabaseRef(projData.supabase_ref);
          }
        } catch {
          // Non-fatal — Cloud tab simply won't appear for non-Class-B projects
        }
      } else {
        
        setMessages([
          { 
            role: 'assistant', 
            content: project?.name 
              ? `Hello! I'm ready to help you build **${project.name}**. Describe what you want to build and I'll generate the code.`
              : `Hello! I'm ready to help you build your app. Describe what you want to build and I'll generate the code.`
          }
        ]);
      }
    } catch (error) {
      console.error('Error loading conversation:', error);
      // Show default message on error
      setMessages([
        { 
          role: 'assistant', 
          content: `Hello! I'm ready to help you build your app. Describe what you want to build and I'll generate the code.`
        }
      ]);
    }
  }
  
  if (projectId) {
    loadConversationHistory();
  }
}, [projectId, project?.name]);

  // Auth listener
  useEffect(() => {
    const { data: listener } = supabaseBrowser.auth.onAuthStateChange(
      (_event, session) => {
        setUser(session?.user ?? null);
        if (!session?.user) {
          router.push('/');
        }
      }
    );
    
    supabaseBrowser.auth.getUser().then(({ data: { user } }) => {
      setUser(user);
    });
    
    return () => listener.subscription.unsubscribe();
  }, [router]);

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    
    // Handle clarification answer
    if (conversationContext.pendingClarification) {
      await handleClarificationAnswer(input);
      return;
    }
    
    // Save original prompt
    setConversationContext({
      originalPrompt: input,
      pendingClarification: null
    });
    
    // Add user message
    const userMessage: Message = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);
    
    try {
      // Get fresh session token
      const { data: { session } } = await supabaseBrowser.auth.getSession();
      const token = session?.access_token;
      
      if (!token) {
        throw new Error('Not authenticated');
      }
      
      const response = await fetch('http://localhost:8000/api/v1/generate/project', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ 
          prompt: input,
          project_id: projectId
        }),
      });
      
      if (response.status === 401) {
        // Token expired - sign out and redirect
        await supabaseBrowser.auth.signOut();
        router.push('/');
        throw new Error('Session expired');
      }
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || `API error: ${response.status}`);
      }
      
      const data = await response.json();
      
    
if (data.type === 'clarification_needed') {
  setConversationContext(prev => ({
    ...prev,
    pendingClarification: {
      question: data.message,
      detectedClass: data.detected_class
    }
  }));
  
  // ✅ Add the AI's clarification question to messages
  setMessages(prev => [
    ...prev,
    { 
      role: 'assistant', 
      content: `To better understand, please clarify: ${data.message}`
    },
  ]);
}
      else if (data.type === 'unsupported_class') {
        setMessages(prev => [
          ...prev,
          { 
            role: 'assistant', 
            content: `⚠️ ${data.message}`
          },
        ]);
      }
      else if (data.type === 'success' && data.files?.length > 0) {
        // Save files and preview
        setGeneratedFiles(data.files);
        setPreviewUrl(data.preview_url || '');
        setShowCodePanel(true);
        // Class B apps return supabase_ref — this enables the Cloud tab
        if (data.supabase_ref) {
          setSupabaseRef(data.supabase_ref);
        }
        // Auto-switch to preview after generation
        setActiveTab(previewUrl ? 'preview' : 'code');
        
        // Add success message
        const successMessage: Message = {
          role: 'assistant',
          content: (
            <div>
              <p className="font-medium">✅ Your app is ready!</p>
              <p className="text-sm text-slate-400 mt-1">
                Generated {data.files.length} files. Check the code and live preview on the right.
              </p>
            </div>
          ),
          files: data.files,
          preview_url: data.preview_url
        };
        
        setMessages(prev => [...prev, successMessage]);
      }
      
    } catch (error: any) {
      console.error('Generation error:', error);
      setMessages(prev => [
        ...prev,
        { 
          role: 'assistant', 
          content: `❌ Error: ${error.message || 'Failed to generate project. Please try again.'}` 
        },
      ]);
    } finally {
      setLoading(false);
    }
  };


const handleClarificationAnswer = async (answer: string) => {
  if (!conversationContext.pendingClarification) return;
  
  const userMessage: Message = { role: 'user', content: answer };
  setMessages(prev => [...prev, userMessage]);
  setInput('');
  setLoading(true);
  
  try {
    // Get fresh session token
    const { data: { session } } = await supabaseBrowser.auth.getSession();
    const token = session?.access_token;
    
    if (!token) {
      throw new Error('Not authenticated');
    }
    
   
    const response = await fetch('http://localhost:8000/api/v1/generate/project', {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        prompt: `${conversationContext.originalPrompt}. Clarification: ${answer}`,
        project_id: projectId,
        clarification: answer,
        detected_class: conversationContext.pendingClarification.detectedClass
      }),
    });
    
    if (response.status === 401) {
      await supabaseBrowser.auth.signOut();
      router.push('/');
      throw new Error('Session expired');
    }
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `API error: ${response.status}`);
    }
    
    const data = await response.json();
    
    // Reset clarification context
    setConversationContext({
      originalPrompt: '',
      pendingClarification: null
    });
    
    // Handle response
    if (data.type === 'success') {
      setGeneratedFiles(data.files);
      setPreviewUrl(data.preview_url || '');
      setShowCodePanel(true);
      
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: (
          <div>
            <p className="font-medium">✅ Your app is ready!</p>
            <p className="text-sm text-slate-400">Generated {data.files.length} files.</p>
          </div>
        ),
        files: data.files,
        preview_url: data.preview_url
      }]);
    } else if (data.type === 'clarification_needed') {
      // Handle nested clarification
      setConversationContext(prev => ({
        originalPrompt: prev.originalPrompt,
        pendingClarification: {
          question: data.message,
          detectedClass: data.detected_class
        }
      }));
      
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `To better understand, please clarify: ${data.message}`
      }]);
    } else if (data.type === 'unsupported_class') {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `⚠️ ${data.message}`
      }]);
    }
    
  } catch (error: any) {
    console.error('Clarification error:', error);
    setMessages(prev => [
      ...prev,
      { 
        role: 'assistant', 
        content: `❌ Error: ${error.message || 'Failed to process clarification.'}` 
      }
    ]);
  } finally {
    setLoading(false);
  }
};
  const exportToGitHub = async (files: any[]) => {
    try {
      // Get fresh session token for GitHub export
      const { data: { session } } = await supabaseBrowser.auth.getSession();
      const token = session?.access_token;
      
      if (!token) {
        throw new Error('Not authenticated');
      }
      
      const repoName = prompt(
        'Enter repository name:', 
        `${projectData?.name?.toLowerCase().replace(/\s+/g, '-') || 'app'}-${Date.now()}`
      );
      
      if (!repoName) return;
      
      const response = await fetch('http://localhost:8000/api/v1/export-project', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          repo_name: repoName,
          files: files
        }),
      });
      
      if (response.status === 401) {
        await supabaseBrowser.auth.signOut();
        router.push('/');
        throw new Error('Session expired');
      }
      
      if (!response.ok) throw new Error('Export failed');
      
      const data = await response.json();
      window.open(data.repo_url, '_blank');
    } catch (error) {
      console.error('Export error:', error);
      alert('Export failed — check backend and GitHub token');
    }
  };

  const closeCodePanel = () => {
    setShowCodePanel(false);
  };

  if (!user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-900">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className={`chat-container ${showCodePanel ? 'split-screen' : ''}`}>
      {/* Chat Panel */}
      <div className="chat-panel">
        <header className="chat-header">
          <div className="chat-header-content">
            <div className="flex items-center gap-3">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => router.push('/dashboard')}
                className="h-8 w-8 text-slate-400 hover:text-white hover:bg-slate-800"
              >
                <ArrowLeft className="h-4 w-4" />
              </Button>
              <div>
                <h1 className="text-lg font-semibold text-white">
                  {projectData?.name || 'Loading project...'}
                </h1>
                {projectData?.description && (
                  <p className="text-xs text-slate-400 truncate max-w-[300px]">
                    {projectData.description}
                  </p>
                )}
              </div>
            </div>
            <Button 
              variant="outline" 
              onClick={() => supabaseBrowser.auth.signOut()}
              className="border-slate-600 text-slate-300 hover:bg-slate-800"
            >
              Sign Out
            </Button>
          </div>
        </header>
        
        <ScrollArea className="chat-messages">
          <div className="chat-messages-container">
            {messages.map((msg, index) => (
              <MessageBubble
                key={index}
                role={msg.role}
                content={msg.content}
              />
            ))}
            
            {loading && (
              <div className="flex items-center gap-2 text-slate-400 px-4 py-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span className="text-sm">
                  {conversationContext.pendingClarification 
                    ? 'Processing clarification...' 
                    : 'Building your app...'}
                </span>
              </div>
            )}
            
            {conversationContext.pendingClarification && !loading && (
              <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4 mx-4">
                <p className="text-sm text-blue-400">
                  ⚠️ Awaiting clarification: <strong>{conversationContext.pendingClarification.question}</strong>
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  Type your answer above and press Send
                </p>
              </div>
            )}
          </div>
        </ScrollArea>
        
        <div className="chat-input">
          <form onSubmit={sendMessage} className="chat-input-form">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={
                conversationContext.pendingClarification
                  ? `Answer: ${conversationContext.pendingClarification.question}`
                  : projectData?.name 
                    ? `Build features for ${projectData.name}...`
                    : `Build features for your app...`
              }
              disabled={loading}
              className="flex-1"
            />
            <Button type="submit" disabled={loading || !input.trim()}>
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                'Send'
              )}
            </Button>
          </form>
        </div>
      </div>
      
      {/* ── Right Panel: Preview | Code | ☁ Cloud ── */}
      {showCodePanel && generatedFiles.length > 0 && (
        <div className="code-panel">

          {/* ── Flat top tab bar using existing CSS classes ── */}
          <div className="code-panel-tabs">
            <button
              className={`code-panel-tab ${activeTab === 'preview' ? 'active' : ''}`}
              onClick={() => setActiveTab('preview')}
              disabled={!previewUrl}
              style={{ opacity: previewUrl ? 1 : 0.4, cursor: previewUrl ? 'pointer' : 'not-allowed' }}
            >
              <Monitor size={14} />
              Preview
            </button>

            <button
              className={`code-panel-tab ${activeTab === 'code' ? 'active' : ''}`}
              onClick={() => setActiveTab('code')}
            >
              <Code2 size={14} />
              Code
            </button>

            {supabaseRef && (
              <button
                className={`code-panel-tab ${activeTab === 'cloud' ? 'active' : ''}`}
                onClick={() => setActiveTab('cloud')}
                style={{ color: activeTab === 'cloud' ? '#a78bfa' : undefined }}
              >
                <Cloud size={14} style={{ color: '#a78bfa' }} />
                Cloud
              </button>
            )}

            {/* Close button pushed to the right */}
            <button
              onClick={closeCodePanel}
              className="code-panel-tab"
              style={{ marginLeft: 'auto', minWidth: 'unset', padding: '0 10px' }}
            >
              <X size={14} />
            </button>
          </div>

          {/* ── Tab content area ── */}
          <div className="code-panel-content">

            {/* Preview */}
            {activeTab === 'preview' && (
              <div className="preview-container">
                {previewUrl ? (
                  <iframe
                    src={previewUrl}
                    className="w-full h-full border-0"
                    title="App Preview"
                    sandbox="allow-scripts allow-same-origin allow-modals allow-forms allow-popups"
                  />
                ) : (
                  <div className="preview-placeholder">
                    <Monitor className="preview-placeholder-icon" />
                    <h3>Live Preview</h3>
                    <p>No preview URL available. Deploy a Class B app to see a live preview.</p>
                    <button
                      className="code-panel-tab"
                      style={{ marginTop: 16 }}
                      onClick={() => setActiveTab('code')}
                    >
                      <Code2 size={14} /> Switch to Code
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Code — VSCodeDisplay in codeOnly mode (no inner tabs) */}
            {activeTab === 'code' && (
              <VSCodeDisplay
                files={generatedFiles}
                onExport={exportToGitHub}
                onClose={closeCodePanel}
                projectName={projectData?.name || 'Project'}
                codeOnly={true}
              />
            )}

            {/* Cloud — only for Class B deployed apps */}
            {activeTab === 'cloud' && supabaseRef && (
              <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
                <CloudDashboard
                  projectId={projectId}
                  supabaseRef={supabaseRef}
                />
              </div>
            )}

          </div>
        </div>
      )}
    </div>
  );
}