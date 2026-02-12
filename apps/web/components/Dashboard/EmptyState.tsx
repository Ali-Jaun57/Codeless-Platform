'use client';

import { Button } from '@/components/ui/button';
import { FolderPlus, Code2, Sparkles } from 'lucide-react';

interface EmptyStateProps {
  onCreateClick: () => void;
}

export default function EmptyState({ onCreateClick }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
      <div className="relative">
        <div className="absolute inset-0 bg-gradient-to-r from-blue-500/20 to-purple-500/20 rounded-full blur-3xl" />
        <div className="relative bg-slate-800/50 p-6 rounded-full border border-slate-700 mb-6">
          <FolderPlus className="h-12 w-12 text-blue-400" />
        </div>
      </div>
      
      <h2 className="text-2xl font-bold text-white mb-3">
        No projects yet
      </h2>
      
      <p className="text-slate-400 max-w-md mb-8">
        Start your first project and let AI build your React application through simple conversation. No coding required.
      </p>
      
      <div className="flex flex-col sm:flex-row gap-4">
        <Button
          onClick={onCreateClick}
          className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 px-6 py-5 text-base"
        >
          <Sparkles className="h-5 w-5 mr-2" />
          Create Your First Project
        </Button>
      </div>
      
      <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6 max-w-3xl">
        <div className="bg-slate-800/30 p-4 rounded-lg border border-slate-700">
          <Code2 className="h-6 w-6 text-blue-400 mb-2" />
          <h3 className="font-semibold text-white mb-1">Describe</h3>
          <p className="text-xs text-slate-400">Tell the AI what you want to build in plain English</p>
        </div>
        <div className="bg-slate-800/30 p-4 rounded-lg border border-slate-700">
          <Sparkles className="h-6 w-6 text-purple-400 mb-2" />
          <h3 className="font-semibold text-white mb-1">Generate</h3>
          <p className="text-xs text-slate-400">AI creates React components with Tailwind CSS</p>
        </div>
        <div className="bg-slate-800/30 p-4 rounded-lg border border-slate-700">
          <FolderPlus className="h-6 w-6 text-green-400 mb-2" />
          <h3 className="font-semibold text-white mb-1">Preview</h3>
          <p className="text-xs text-slate-400">See live preview and export to GitHub</p>
        </div>
      </div>
    </div>
  );
}