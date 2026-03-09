



'use client';

import { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  FileText, 
  Folder, 
  FolderOpen, 
  X,
  FileCode,
  FileJson,
  File,
  Terminal,
  Settings,
  Package,
  Code2,
  Eye,
  Play,
  Monitor,
  Zap
} from 'lucide-react';
import CodeBlock from './CodeBlock';

interface FileData {
  path: string;
  content: string;
}

interface VSCodeDisplayProps {
  files: FileData[];
  previewUrl?: string;
  onExport?: (files: FileData[]) => void;
  onClose?: () => void;
  isFullScreen?: boolean;
  projectName?: string;
  // When true: no outer code-panel wrapper, no Preview/Code tab bar — just the editor
  codeOnly?: boolean;
}

interface FileNode {
  name: string;
  path: string;
  type: 'file' | 'folder';
  children?: FileNode[];
}

type ViewMode = 'code' | 'preview';

export default function VSCodeDisplay({ 
  files, 
  previewUrl = '',  
  onExport,
  onClose,
  isFullScreen = false,
  projectName = 'Generated Project',
  codeOnly = false,
}: VSCodeDisplayProps) {
  const [selectedFile, setSelectedFile] = useState<string>(files[0]?.path || '');
  const [openTabs, setOpenTabs] = useState<string[]>([files[0]?.path || '']);
  const [openFolders, setOpenFolders] = useState<Set<string>>(new Set());
  const [viewMode, setViewMode] = useState<ViewMode>(codeOnly ? 'code' : 'preview');
  
  const [iframeKey, setIframeKey] = useState<number>(0);
  const [lastPreviewUrl, setLastPreviewUrl] = useState<string>('');
  
  // Auto-switch to preview and reload when new URL arrives (only when not codeOnly)
  useEffect(() => {
    if (!codeOnly && previewUrl && previewUrl !== lastPreviewUrl) {
      setLastPreviewUrl(previewUrl);
      setIframeKey(prev => prev + 1);
      setViewMode('preview');
    }
  }, [previewUrl, lastPreviewUrl, codeOnly]);
  
  useEffect(() => {
    const initialTabs = files.slice(0, 3).map(f => f.path);
    setOpenTabs(initialTabs);
    if (files[0]) {
      setSelectedFile(files[0].path);
    }
  }, [files]);
  
  const buildFileTree = (): FileNode[] => {
    const root: FileNode[] = [];
    const pathMap: Record<string, FileNode> = {};
    
    files.forEach(file => {
      const parts = file.path.split('/');
      let currentPath = '';
      let parentNode: FileNode | null = null;
      
      parts.forEach((part, index) => {
        const isFile = index === parts.length - 1;
        currentPath = currentPath ? `${currentPath}/${part}` : part;
        
        if (!pathMap[currentPath]) {
          const newNode: FileNode = {
            name: part,
            path: currentPath,
            type: isFile ? 'file' : 'folder'
          };
          
          pathMap[currentPath] = newNode;
          
          if (parentNode) {
            if (!parentNode.children) parentNode.children = [];
            parentNode.children.push(newNode);
          } else {
            root.push(newNode);
          }
        }
        
        parentNode = pathMap[currentPath];
      });
    });
    
    const sortNodes = (nodes: FileNode[]): FileNode[] => {
      return nodes.sort((a, b) => {
        if (a.type === 'folder' && b.type !== 'folder') return -1;
        if (a.type !== 'folder' && b.type === 'folder') return 1;
        return a.name.localeCompare(b.name);
      }).map(node => ({
        ...node,
        children: node.children ? sortNodes(node.children) : undefined
      }));
    };
    
    return sortNodes(root);
  };
  
  const fileTree = buildFileTree();
  
  const toggleFolder = (path: string) => {
    const newOpenFolders = new Set(openFolders);
    if (newOpenFolders.has(path)) {
      newOpenFolders.delete(path);
    } else {
      newOpenFolders.add(path);
    }
    setOpenFolders(newOpenFolders);
  };
  
  const getFileIcon = (fileName: string, isFolder: boolean, isOpen: boolean) => {
    if (isFolder) {
      return isOpen ? 
        <FolderOpen className="file-item-icon icon-folder-open" size={12} /> : 
        <Folder className="file-item-icon icon-folder" size={12} />;
    }
    
    const extension = fileName.split('.').pop()?.toLowerCase();
    const fileNameLower = fileName.toLowerCase();
    
    if (fileNameLower === 'package.json') {
      return <Package className="file-item-icon icon-json" size={12} />;
    }
    
    switch (extension) {
      case 'js':  return <FileCode className="file-item-icon icon-js" size={12} />;
      case 'jsx': return <Code2 className="file-item-icon icon-jsx" size={12} />;
      case 'ts':  return <FileCode className="file-item-icon icon-ts" size={12} />;
      case 'tsx': return <Code2 className="file-item-icon icon-tsx" size={12} />;
      case 'py':  return <Terminal className="file-item-icon icon-py" size={12} />;
      case 'html':return <FileCode className="file-item-icon icon-html" size={12} />;
      case 'css': return <FileCode className="file-item-icon icon-css" size={12} />;
      case 'json':return <FileJson className="file-item-icon icon-json" size={12} />;
      case 'md':  return <FileText className="file-item-icon icon-md" size={12} />;
      default:    return <File className="file-item-icon icon-file" size={12} />;
    }
  };
  
  const getLanguage = (path: string): string => {
    const extension = path.split('.').pop() || 'text';
    const languageMap: Record<string, string> = {
      'js': 'javascript', 'jsx': 'jsx', 'ts': 'typescript', 'tsx': 'tsx',
      'py': 'python', 'html': 'html', 'css': 'css', 'json': 'json',
      'md': 'markdown', 'txt': 'text', 'gitignore': 'text', 'sql': 'sql',
    };
    return languageMap[extension.toLowerCase()] || extension;
  };
  
  const renderFileTree = (nodes: FileNode[], level = 0) => {
    return nodes.map(node => {
      const isFolder = node.type === 'folder';
      const isOpen = openFolders.has(node.path);
      
      return (
        <div key={node.path}>
          <div
            className={`file-item ${selectedFile === node.path ? 'active' : ''}`}
            style={{ paddingLeft: `${level * 1 + 0.75}rem` }}
            onClick={() => {
              if (isFolder) {
                toggleFolder(node.path);
              } else {
                setSelectedFile(node.path);
                if (!openTabs.includes(node.path)) {
                  setOpenTabs(prev => [...prev, node.path].slice(-5));
                }
              }
            }}
          >
            {getFileIcon(node.name, isFolder, isOpen)}
            <span className="file-name">{node.name}</span>
          </div>
          {isFolder && isOpen && node.children && (
            <div>{renderFileTree(node.children, level + 1)}</div>
          )}
        </div>
      );
    });
  };
  
  const selectedFileData = files.find(f => f.path === selectedFile);
  
  const closeTab = (tabPath: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const newTabs = openTabs.filter(tab => tab !== tabPath);
    setOpenTabs(newTabs);
    if (selectedFile === tabPath) {
      setSelectedFile(newTabs[0] || '');
    }
  };

  // ─── Code editor JSX (shared between both modes) ──────────────────────────
  const codeEditorJSX = (
    <>
      {/* Header with project name, Export, and optional Close */}
      <div className="code-view-header">
        <div className="code-view-title">
          <Code2 className="h-3.5 w-3.5" />
          <span>{projectName || 'Generated Project'}</span>
        </div>
        <div className="code-view-actions">
          {onExport && (
            <Button
              variant="default"
              size="sm"
              onClick={() => onExport(files)}
              className="btn-primary h-7 px-3 text-xs"
            >
              <Zap className="h-3 w-3 mr-1.5" />
              Export to GitHub
            </Button>
          )}
          {onClose && (
            <Button variant="ghost" size="sm" onClick={onClose} className="btn-ghost h-7 w-7 p-0">
              <X className="h-3.5 w-3.5" />
            </Button>
          )}
        </div>
      </div>

      {/* File Explorer + Editor */}
      <div className="code-view-content">
        <div className="file-explorer">
          <div className="file-explorer-header">EXPLORER</div>
          <ScrollArea className="file-tree custom-scrollbar">
            {renderFileTree(fileTree)}
          </ScrollArea>
        </div>
        <div className="editor-container">
          <div className="editor-tabs custom-scrollbar">
            {openTabs.map(tabPath => {
              const file = files.find(f => f.path === tabPath);
              const fileName = file?.path.split('/').pop() || tabPath;
              return (
                <div
                  key={tabPath}
                  className={`editor-tab ${selectedFile === tabPath ? 'active' : ''}`}
                  onClick={() => setSelectedFile(tabPath)}
                >
                  {getFileIcon(fileName, false, false)}
                  <span className="truncate text-xs">{fileName}</span>
                  <div className="tab-close" onClick={(e) => closeTab(tabPath, e)}>
                    <X className="h-2.5 w-2.5" />
                  </div>
                </div>
              );
            })}
          </div>
          <div className="editor-content custom-scrollbar">
            {selectedFileData ? (
              <CodeBlock
                code={selectedFileData.content}
                language={getLanguage(selectedFileData.path)}
                showLineNumbers={true}
              />
            ) : (
              <div className="flex h-full items-center justify-center text-[#94a3b8]">
                <div className="text-center">
                  <File className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p className="text-xs">Select a file to view its content</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );

  // ─── codeOnly mode: no outer panel wrapper, no tab bar ────────────────────
  // Used when ChatClient owns the tab bar (flat Preview | Code | Cloud tabs)
  if (codeOnly) {
    return (
      <div className="code-panel-content" style={{ display: 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden' }}>
        {codeEditorJSX}
      </div>
    );
  }

  // ─── Standalone mode: full panel with its own Preview/Code tab bar ─────────
  return (
    <div className="code-panel">
      <div className="code-panel-tabs">
        <button
          className={`code-panel-tab ${viewMode === 'preview' ? 'active' : ''}`}
          onClick={() => setViewMode('preview')}
          disabled={!previewUrl}
          style={{ opacity: previewUrl ? 1 : 0.4, cursor: previewUrl ? 'pointer' : 'not-allowed' }}
        >
          <Monitor size={14} />
          Preview
        </button>
        <button
          className={`code-panel-tab ${viewMode === 'code' ? 'active' : ''}`}
          onClick={() => setViewMode('code')}
        >
          <Code2 size={14} />
          Code
        </button>
      </div>
      
      <div className="code-panel-content">
        {viewMode === 'code' ? (
          codeEditorJSX
        ) : (
          <div className="preview-container">
            {previewUrl ? (
              <iframe
                key={`iframe-${iframeKey}`}
                src={previewUrl}
                className="w-full h-full border-0"
                title="Live Preview"
                sandbox="allow-scripts allow-same-origin allow-modals allow-forms allow-popups"
                loading="lazy"
              />
            ) : (
              <div className="preview-placeholder">
                <Monitor className="preview-placeholder-icon" />
                <h3>Live Preview</h3>
                <p>Preview URL not available. The app may still be deploying or this project type doesn't support live preview.</p>
                <div className="mt-6 flex gap-2">
                  <Button variant="outline" size="sm" onClick={() => setViewMode('code')} className="px-4 text-xs">
                    <Code2 className="h-3 w-3 mr-1.5" />
                    Switch to Code
                  </Button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}