'use client';

import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useRouter } from "next/navigation";  // For reload on error if needed
import { useState } from 'react';
import { supabaseBrowser } from '@/lib/supabase';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { cn } from '@/lib/utils';
import { CodeBlock } from '@/components/ui/code-block';

// type Message = {
//   role: "user" | "assistant";
//   content: string;
// };

type Message = {
  role: "user" | "assistant";
  content: string | React.ReactNode;  // Allow string or JSX
};

type Props = {
  initialUser: any;
};

export default function ChatClient({ initialUser }: Props) {
  const [user, setUser] = useState(initialUser);
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", content: "Hello! Describe the app or code you want to build." }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  // Auth listener (for sign out)
  useState(() => {
    const { data: listener } = supabaseBrowser.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
    });
    return () => listener.subscription.unsubscribe();
  });

  // const sendMessage = async (e: React.FormEvent) => {
  //   e.preventDefault();
  //   if (!input.trim() || loading) return;

  //   const userMessage = { role: "user" as const, content: input };
  //   setMessages((prev) => [...prev, userMessage]);
  //   setInput("");
  //   setLoading(true);

  //   try {
  //     const res = await fetch("http://localhost:8000/generate-project", {
  //       method: "POST",
  //       headers: { "Content-Type": "application/json" },
  //       body: JSON.stringify({ prompt: input }),
  //     });

  //     if (!res.ok) {
  //       const err = await res.text();
  //       throw new Error(err || "API error");
  //     }

  //     const data = await res.json();
  //     setMessages((prev) => [...prev, { role: "assistant" as const, content: `\`\`\`${data.language}\n${data.code}\n\`\`\`` }]);
  //   } catch (err: any) {
  //     setMessages((prev) => [...prev, { role: "assistant" as const, content: `Error: ${err.message || "Failed to generate code"}` }]);
  //   } finally {
  //     setLoading(false);
  //   }
  // };

  //   const sendMessage = async (e: React.FormEvent) => {
  //   e.preventDefault();
  //   if (!input.trim() || loading) return;

  //   const userMessage = { role: "user" as const, content: input };
  //   setMessages((prev) => [...prev, userMessage]);
  //   setInput("");
  //   setLoading(true);

  //   try {
  //     const res = await fetch("http://localhost:8000/generate-project", {
  //       method: "POST",
  //       headers: { "Content-Type": "application/json" },
  //       body: JSON.stringify({ prompt: input }),
  //     });

  //     if (!res.ok) {
  //       const err = await res.text();
  //       throw new Error(err || "API error");
  //     }

  //     const data = await res.json();  // { files: [{ path: "...", content: "..." }, ...] }

  //     if (!data.files || data.files.length === 0) {
  //       throw new Error("No files generated");
  //     }

  //     // Render as tabs (path as tab title)
  //     const multiFileContent = (
  //       <Tabs defaultValue={data.files[0].path} className="w-full mt-4">
  //         <TabsList className="grid w-full" style={{ gridTemplateColumns: `repeat(${data.files.length}, 1fr)` }}>
  //           {data.files.map((file: any) => (
  //             <TabsTrigger key={file.path} value={file.path}>
  //               {file.path.split('/').pop() || file.path}  // File name as title
  //             </TabsTrigger>
  //           ))}
  //         </TabsList>
  //         {data.files.map((file: any) => (
  //           <TabsContent key={file.path} value={file.path}>
  //             <CodeBlock
  //               code={file.content}
  //               language={file.path.split('.').pop() || "text"}  // Detect language from extension
  //             />
  //           </TabsContent>
  //         ))}
  //       </Tabs>
  //     );

  //     setMessages((prev) => [...prev, { role: "assistant" as const, content: multiFileContent }]);
  //   } catch (err: any) {
  //     console.error(err);
  //     setMessages((prev) => [...prev, { role: "assistant" as const, content: `Error generating project: ${err.message || "Failed"}. Check backend console.` }]);
  //   } finally {
  //     setLoading(false);
  //   }
  // };

  const sendMessage = async (e: React.FormEvent) => {
  e.preventDefault();
  if (!input.trim() || loading) return;

  const userMessage = { role: "user" as const, content: input };
  setMessages((prev) => [...prev, userMessage]);
  setInput("");
  setLoading(true);

  try {
    const res = await fetch("http://localhost:8000/generate-project", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt: input }),
    });

    if (!res.ok) {
      const errText = await res.text();
      throw new Error(errText || `API error ${res.status}`);
    }

    const data = await res.json();

    // Safe check for files array
    if (!data.files || !Array.isArray(data.files) || data.files.length === 0) {
      throw new Error("No files returned from API");
    }

    const multiFileContent = (
      <Tabs defaultValue={data.files[0].path} className="w-full mt-4">
        <TabsList className="grid w-full" style={{ gridTemplateColumns: `repeat(${data.files.length}, 1fr)` }}>
          {data.files.map((file: any) => (
            <TabsTrigger key={file.path} value={file.path}>
              {file.path.split('/').pop() || file.path}
            </TabsTrigger>
          ))}
        </TabsList>
        {data.files.map((file: any) => (
          <TabsContent key={file.path} value={file.path}>
            <CodeBlock
              code={file.content}
              language={file.path.split('.').pop() || "text"}
            />
          </TabsContent>
        ))}
      </Tabs>
    );

    setMessages((prev) => [...prev, { role: "assistant" as const, content: multiFileContent }]);
  } catch (err: any) {
    console.error("Generation error:", err);
    setMessages((prev) => [
      ...prev,
      { role: "assistant" as const, content: `Error generating project: ${err.message || "Unknown error. Check backend console and OpenAI key."}` },
    ]);
  } finally {
    setLoading(false);
  }
};

  if (!user) {
    return <div className="flex min-h-screen items-center justify-center bg-background">Signed out — reload for auth form</div>;
  }

  return (
    <div className="flex h-screen flex-col bg-background">
      <header className="border-b p-4">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">Codeless Chat</h1>
          <Button variant="outline" onClick={() => supabaseBrowser.auth.signOut()}>
            Sign Out ({user.email})
          </Button>
        </div>
      </header>

      <ScrollArea className="flex-1 p-4">
        <div className="mx-auto max-w-4xl space-y-4">
          {/* {messages.map((msg, i) => (
            <div
              key={i}
              className={cn(
                "flex items-end gap-3 my-4",
                msg.role === "user" ? "justify-end" : "justify-start"
              )}
            >
              
              {msg.role === "assistant" && (
  <div className="w-full">
    {typeof msg.content === 'string' ? (
      <div className="max-w-lg rounded-lg px-4 py-2 bg-muted">
        {msg.content}
      </div>
    ) : (
      msg.content  // JSX tabs for multi-file
    )}
  </div>
)}
              <div  
                className={cn(
                  "max-w-md rounded-2xl px-4 py-3 shadow-md",
                  msg.role === "user"
                    ? "bg-primary text-primary-foreground rounded-br-none"
                    : "bg-muted text-foreground rounded-bl-none"
                )}
              >
                {msg.content}
              </div>
              {msg.role === "user" && (
                <Avatar className="h-8 w-8">
                  <AvatarFallback className="bg-secondary text-secondary-foreground">U</AvatarFallback>
                </Avatar>
              )}
            </div>
          ))} */}
{messages.map((msg, i) => (
  <div
    key={i}
    className={cn(
      "flex items-end gap-3 my-4",
      msg.role === "user" ? "justify-end" : "justify-start"
    )}
  >
    {msg.role === "assistant" && (
      <Avatar className="h-8 w-8">
        <AvatarFallback className="bg-secondary text-secondary-foreground">AI</AvatarFallback>
      </Avatar>
    )}
    
    {/* Remove the duplicate w-full div and keep only this main message bubble */}
    <div  
      className={cn(
        "max-w-full rounded-2xl px-4 py-3 shadow-md",
        msg.role === "user"
          ? "bg-primary text-primary-foreground rounded-br-none"
          : "bg-muted text-foreground rounded-bl-none"
      )}
    >
      {msg.role === "assistant" ? (
        // Assistant message content (with tabs for multi-file or plain text)
        <div className="w-full">
          {typeof msg.content === 'string' ? (
            msg.content.startsWith('```') ? (
              // Extract language and code from block for single file
              (() => {
                const parts = msg.content.split('```');
                const language = parts[1]?.split('\n')[0]?.trim() || 'text';
                const code = parts[1]?.split('\n').slice(1).join('\n').trim() || '';
                return <CodeBlock code={code} language={language} />;
              })()
            ) : (
              // Plain text message
              <div className="max-w-lg">{msg.content}</div>
            )
          ) : (
            // JSX tabs for multi-file
            msg.content
          )}
        </div>
      ) : (
        // User message content (simple text)
        msg.content
      )}
    </div>
    
    {msg.role === "user" && (
      <Avatar className="h-8 w-8">
        <AvatarFallback className="bg-secondary text-secondary-foreground">U</AvatarFallback>
      </Avatar>
    )}
  </div>
))}
          {loading && <div className="text-center text-muted-foreground">Typing...</div>}
        </div>
      </ScrollArea>

      <div className="border-t p-4">
        <form onSubmit={sendMessage} className="mx-auto flex max-w-4xl gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Describe your app..."
            disabled={loading}
            className="flex-1"
          />
          <Button type="submit" disabled={loading}>
            Send
          </Button>
        </form>
      </div>
    </div>
  );
}