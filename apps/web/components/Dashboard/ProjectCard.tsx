// apps/web/components/Dashboard/ProjectCard.tsx
'use client';

import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader } from '@/components/ui/card';
import { FolderOpen, Calendar, Code2, ExternalLink, Trash2 } from 'lucide-react';

interface Project {
  id: string;
  name: string;
  description: string | null;
  status: string;
  latest_files: any[];
  latest_preview_url: string | null;
  created_at: string;
  updated_at: string;
}

interface ProjectCardProps {
  project: Project;
  onDelete: (id: string) => void;
}

export default function ProjectCard({ project, onDelete }: ProjectCardProps) {
  const router = useRouter();
  
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const handleOpenProject = () => {
    router.push(`/chat/${project.id}`);
  };

  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirm('Are you sure you want to delete this project?')) {
      onDelete(project.id);
    }
  };

  return (
    <Card 
      className="group relative bg-slate-900/50 border-slate-700 hover:border-blue-500/50 transition-all duration-300 cursor-pointer hover:shadow-lg hover:shadow-blue-500/10"
      onClick={handleOpenProject}
    >
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <FolderOpen className="h-5 w-5 text-blue-400" />
            <h3 className="font-semibold text-white truncate max-w-[200px]">
              {project.name}
            </h3>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity"
            onClick={handleDelete}
          >
            <Trash2 className="h-4 w-4 text-red-400 hover:text-red-300" />
          </Button>
        </div>
        {project.description && (
          <p className="text-sm text-slate-400 line-clamp-2 mt-1">
            {project.description}
          </p>
        )}
      </CardHeader>
      
      <CardContent className="pb-3">
        <div className="flex items-center gap-4 text-xs text-slate-500">
          <div className="flex items-center gap-1">
            <Calendar className="h-3 w-3" />
            <span>{formatDate(project.updated_at)}</span>
          </div>
          {project.latest_files?.length > 0 && (
            <div className="flex items-center gap-1">
              <Code2 className="h-3 w-3" />
              <span>{project.latest_files.length} files</span>
            </div>
          )}
        </div>
      </CardContent>
      
      <CardFooter className="pt-0">
        {project.latest_preview_url ? (
          <a
            href={project.latest_preview_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 transition-colors"
            onClick={(e) => e.stopPropagation()}
          >
            <ExternalLink className="h-3 w-3" />
            <span>View Preview</span>
          </a>
        ) : (
          <span className="text-xs text-slate-600">No preview available</span>
        )}
      </CardFooter>
    </Card>
  );
}