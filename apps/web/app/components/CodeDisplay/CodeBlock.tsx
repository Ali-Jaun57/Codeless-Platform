
'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Check, Copy } from 'lucide-react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface CodeBlockProps {
  code: string;
  language: string;
  showLineNumbers?: boolean;
}

export default function CodeBlock({ 
  code, 
  language, 
  showLineNumbers = true 
}: CodeBlockProps) {
  const [copied, setCopied] = useState(false);
  
  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  
  return (
    <div className="relative h-full overflow-hidden">
      <div className="flex justify-between items-center bg-[#1a2236] text-[#cbd5e1] px-3 py-2 border-b border-[#334155]">
        <div className="flex items-center gap-2">
          <div className="flex gap-1">
            <div className="w-2.5 h-2.5 rounded-full bg-[#ef4444]"></div>
            <div className="w-2.5 h-2.5 rounded-full bg-[#f59e0b]"></div>
            <div className="w-2.5 h-2.5 rounded-full bg-[#10b981]"></div>
          </div>
          <span className="text-xs font-mono font-medium">{language.toUpperCase()}</span>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleCopy}
          className="h-6 px-2 text-xs bg-[#1e293b] hover:bg-[#334155] text-[#cbd5e1] border border-[#334155] rounded"
        >
          {copied ? (
            <>
              <Check className="h-3 w-3 mr-1" />
              Copied
            </>
          ) : (
            <>
              <Copy className="h-3 w-3 mr-1" />
              Copy
            </>
          )}
        </Button>
      </div>
      
      <div className="h-[calc(100%-40px)] overflow-auto custom-scrollbar">
        <SyntaxHighlighter
          language={language}
          style={vscDarkPlus}
          showLineNumbers={showLineNumbers}
          customStyle={{
            margin: 0,
            padding: '12px',
            fontSize: '12px',
            backgroundColor: '#0f172a',
            height: '100%',
            minHeight: '100%',
            fontFamily: '"Fira Code", "Consolas", "Monaco", "Andale Mono", "Ubuntu Mono", monospace',
            lineHeight: '1.4'
          }}
          lineNumberStyle={{
            color: '#64748b',
            minWidth: '2.5em',
            textAlign: 'right',
            paddingRight: '1em',
            borderRight: '1px solid #334155'
          }}
          lineProps={{
            style: {
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word'
            }
          }}
        >
          {code}
        </SyntaxHighlighter>
      </div>
    </div>
  );
}