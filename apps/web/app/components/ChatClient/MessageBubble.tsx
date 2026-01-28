
'use client';

import { cn } from '@/lib/utils';

interface MessageBubbleProps {
  role: 'user' | 'assistant';
  content: string | React.ReactNode;
}

export default function MessageBubble({ role, content }: MessageBubbleProps) {
  const isUser = role === 'user';
  
  return (
    <div className={cn(
      "message-row",
      isUser ? "message-row-user" : "message-row-assistant"
    )}>
      <div className={cn(
        "message-bubble",
        isUser
          ? "message-bubble-user"
          : "message-bubble-assistant"
      )}>
        {content}
      </div>
    </div>
  );
}