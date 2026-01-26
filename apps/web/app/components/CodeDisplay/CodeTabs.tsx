// frontend/app/components/CodeDisplay/CodeTabs.tsx
'use client';

import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import CodeBlock from './CodeBlock';

interface CodeTabsProps {
  files: Array<{
    path: string;
    content: string;
  }>;
  onExport?: (files: any[]) => void;
  onTest?: (files: any[]) => void;
  onDeploy?: (files: any[]) => void;
}

export default function CodeTabs({ 
  files, 
  onExport, 
  onTest, 
  onDeploy 
}: CodeTabsProps) {
  const defaultTab = files[0]?.path || "0";
  
  const getFileName = (path: string) => {
    return path.split('/').pop() || path;
  };
  
  const getLanguage = (path: string) => {
    const extension = path.split('.').pop() || 'text';
    return extension.toLowerCase();
  };
  
  return (
    <div className="w-full">
      <Tabs defaultValue={defaultTab} className="w-full">
        {/* Header with actions */}
        <div className="flex items-center justify-between bg-background px-4 py-2 border-b">
          <span className="text-lg font-semibold">Generated Project</span>
          <div className="flex gap-2">
            {onExport && (
              <Button onClick={() => onExport(files)} size="sm">
                Export to GitHub
              </Button>
            )}
            {onTest && (
              <Button onClick={() => onTest(files)} size="sm" variant="outline">
                Run Tests
              </Button>
            )}
            {onDeploy && (
              <Button onClick={() => onDeploy(files)} size="sm" variant="secondary">
                Deploy
              </Button>
            )}
          </div>
        </div>
        
        {/* File tabs */}
        <TabsList className="grid w-full" style={{ 
          gridTemplateColumns: `repeat(${files.length}, 1fr)` 
        }}>
          {files.map((file) => (
            <TabsTrigger key={file.path} value={file.path}>
              {getFileName(file.path)}
            </TabsTrigger>
          ))}
        </TabsList>
        
        {/* File contents */}
        {files.map((file) => (
          <TabsContent key={file.path} value={file.path}>
            <CodeBlock
              code={file.content}
              language={getLanguage(file.path)}
            />
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
}