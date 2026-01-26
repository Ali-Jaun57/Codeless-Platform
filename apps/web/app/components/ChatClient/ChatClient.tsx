



// frontend/app/components/ChatClient/ChatClient.tsx
'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { supabaseBrowser } from '@/lib/supabase';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import MessageBubble from './MessageBubble';
import CodeTabs from '../CodeDisplay/CodeTabs';
import './ChatClient.css';

type Message = {
  role: 'user' | 'assistant';
  content: string | React.ReactNode;
};

interface ChatClientProps {
  initialUser: any;
}

export default function ChatClient({ initialUser }: ChatClientProps) {
  const [user, setUser] = useState(initialUser);
  const [messages, setMessages] = useState<Message[]>([
    { 
      role: 'assistant', 
      content: 'Hello! Describe the app or code you want to build.' 
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  
  // Conversation context for handling clarifications
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
  
  // Auth listener
  useEffect(() => {
    const { data: listener } = supabaseBrowser.auth.onAuthStateChange(
      (_event, session) => {
        setUser(session?.user ?? null);
      }
    );
    
    return () => listener.subscription.unsubscribe();
  }, []);
  
  const exportToGitHub = async (files: any[]) => {
    try {
      const repoName = prompt(
        'Enter repository name:', 
        `codeless-project-${Date.now()}`
      );
      
      if (!repoName) return;
      
      const response = await fetch('http://localhost:8000/export-project', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          repo_name: repoName,
          files: files
        }),
      });
      
      if (!response.ok) throw new Error('Export failed');
      
      const data = await response.json();
      window.open(data.repo_url, '_blank');
      alert(`Exported to GitHub: ${data.repo_url}`);
    } catch (error) {
      console.error('Export error:', error);
      alert('Export failed — check backend and GitHub token');
    }
  };
  
  const handleClarificationAnswer = async (answer: string) => {
    if (!conversationContext.pendingClarification || !conversationContext.originalPrompt) return;
    
    const userMessage: Message = { role: 'user', content: answer };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);
    
    try {
      // Combine original prompt with clarification answer
      const combinedPrompt = `${conversationContext.originalPrompt}. Clarification: ${answer}`;
      
      const response = await fetch('http://localhost:8000/generate-project', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: combinedPrompt }),
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || `API error ${response.status}`);
      }
      
      const data = await response.json();
      
      // Reset context
      setConversationContext({
        originalPrompt: '',
        pendingClarification: null
      });
      
      // Handle response
      if (data.type === 'success' && data.files && Array.isArray(data.files) && data.files.length > 0) {
        const multiFileContent = (
          <div>
            <p className="mb-2">✅ Detected as: <strong>{data.detected_class}</strong></p>
            <CodeTabs 
              files={data.files} 
              onExport={exportToGitHub}
            />
          </div>
        );
        
        setMessages(prev => [
          ...prev, 
          { role: 'assistant', content: multiFileContent }
        ]);
      }
      else if (data.type === 'unsupported_class') {
        setMessages(prev => [
          ...prev,
          { 
            role: 'assistant', 
            content: `${data.message}`
          },
        ]);
      }
      else if (data.type === 'no_class_matched') {
        setMessages(prev => [
          ...prev,
          { 
            role: 'assistant', 
            content: `I couldn't determine what type of app you want. ${data.message}`
          },
        ]);
      }
      else if (data.type === 'clarification_needed') {
        // Handle nested clarification (should be rare)
        setConversationContext(prev => ({
          originalPrompt: combinedPrompt,
          pendingClarification: {
            question: data.message,
            detectedClass: data.detected_class
          }
        }));
        
        setMessages(prev => [
          ...prev,
          { 
            role: 'assistant', 
            content: `To better understand, please clarify: ${data.message}`
          },
        ]);
      }
      else {
        throw new Error('Unexpected response format from API');
      }
      
    } catch (error: any) {
      console.error('Clarification error:', error);
      setMessages(prev => [
        ...prev,
        { 
          role: 'assistant', 
          content: `Error: ${error.message || 'Unknown error.'}` 
        },
      ]);
      
      // Reset context on error too
      setConversationContext({
        originalPrompt: '',
        pendingClarification: null
      });
    } finally {
      setLoading(false);
    }
  };
  
  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    
    // Check if this is a clarification answer
    if (conversationContext.pendingClarification) {
      // This is answering a clarification
      await handleClarificationAnswer(input);
      return;
    }
    
    // Normal message - store as original prompt
    setConversationContext({
      originalPrompt: input,
      pendingClarification: null
    });
    
    const userMessage: Message = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);
    
    try {
      const response = await fetch('http://localhost:8000/generate-project', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: input }),
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || `API error ${response.status}`);
      }
      
      const data = await response.json();
      
      // Handle different response types
      if (data.type === 'clarification_needed') {
        // Store clarification context
        setConversationContext(prev => ({
          ...prev,
          pendingClarification: {
            question: data.message,
            detectedClass: data.detected_class
          }
        }));
        
        // Show clarification question
        setMessages(prev => [
          ...prev,
          { 
            role: 'assistant', 
            content: `To better understand, please clarify: ${data.message}`
          },
        ]);
      } 
      else if (data.type === 'no_class_matched') {
        // Show no class matched message
        setMessages(prev => [
          ...prev,
          { 
            role: 'assistant', 
            content: `I couldn't determine what type of app you want. ${data.message}`
          },
        ]);
      }
      else if (data.type === 'success' && data.files && Array.isArray(data.files) && data.files.length > 0) {
        // Show generated files
        const multiFileContent = (
          <div>
            <p className="mb-2">✅ Detected as: <strong>{data.detected_class}</strong></p>
            <CodeTabs 
              files={data.files} 
              onExport={exportToGitHub}
            />
          </div>
        );
        
        setMessages(prev => [
          ...prev, 
          { role: 'assistant', content: multiFileContent }
        ]);
      }
      else if (data.type === 'unsupported_class') {
        // Show unsupported class message
        setMessages(prev => [
          ...prev,
          { 
            role: 'assistant', 
            content: `${data.message}`
          },
        ]);
      }
      else {
        throw new Error('Unexpected response format from API');
      }
    } catch (error: any) {
      console.error('Generation error:', error);
      setMessages(prev => [
        ...prev,
        { 
          role: 'assistant', 
          content: `Error generating project: ${error.message || 'Unknown error. Check backend console and OpenAI key.'}` 
        },
      ]);
    } finally {
      setLoading(false);
    }
  };
  
  if (!user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        Signed out — please reload for authentication
      </div>
    );
  }
  
  return (
    <div className="chat-container">
      <header className="chat-header">
        <div className="chat-header-content">
          <h1 className="text-2xl font-bold">Codeless Chat</h1>
          <Button 
            variant="outline" 
            onClick={() => supabaseBrowser.auth.signOut()}
          >
            Sign Out ({user.email})
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
            <div className="loading-indicator">
              {conversationContext.pendingClarification 
                ? 'Processing your clarification...' 
                : 'Generating your project...'}
            </div>
          )}
          
          {conversationContext.pendingClarification && !loading && (
            <div className="clarification-reminder p-3 bg-yellow-50 border border-yellow-200 rounded-lg my-4 mx-4">
              <p className="text-sm text-yellow-800">
                ⚠️ Awaiting clarification: <strong>{conversationContext.pendingClarification.question}</strong>
              </p>
              <p className="text-xs text-yellow-600 mt-1">
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
                : 'Describe your app or feature...'
            }
            disabled={loading}
            className="flex-1"
          />
          <Button type="submit" disabled={loading}>
            {loading 
              ? (conversationContext.pendingClarification ? 'Processing...' : 'Generating...')
              : 'Send'}
          </Button>
        </form>
      </div>
    </div>
  );
}