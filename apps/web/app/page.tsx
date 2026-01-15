
// // // // // // 'use client'; // This makes it a Client Component (needed for interactive auth UI)

// // // // // // import { useEffect, useState } from 'react';
// // // // // // import { supabaseBrowser } from '../lib/supabase';
// // // // // // import { Auth } from '@supabase/auth-ui-react';
// // // // // // import { ThemeSupa } from '@supabase/auth-ui-shared';

// // // // // // export default function Home() {
// // // // // //   const [user, setUser] = useState<any>(null);

// // // // // //   useEffect(() => {
// // // // // //     // Check current session on load
// // // // // //     supabaseBrowser.auth.getSession().then(({ data: { session } }) => {
// // // // // //       setUser(session?.user ?? null);
// // // // // //     });

// // // // // //     // Listen for auth changes (login/logout)
// // // // // //     const { data: listener } = supabaseBrowser.auth.onAuthStateChange((_event, session) => {
// // // // // //       setUser(session?.user ?? null);
// // // // // //     });

// // // // // //     return () => listener.subscription.unsubscribe();
// // // // // //   }, []);

// // // // // //   if (user) {
// // // // // //     return (
// // // // // //       <main className="flex min-h-screen flex-col items-center justify-center p-24">
// // // // // //         <h1 className="text-4xl font-bold mb-8">Welcome, {user.email}!</h1>
// // // // // //         <button
// // // // // //           onClick={() => supabaseBrowser.auth.signOut()}
// // // // // //           className="bg-red-600 text-white px-6 py-3 rounded-lg"
// // // // // //         >
// // // // // //           Sign Out
// // // // // //         </button>
// // // // // //       </main>
// // // // // //     );
// // // // // //   }

// // // // // //   return (
// // // // // //     <main className="flex min-h-screen flex-col items-center justify-center p-24">
// // // // // //       <h1 className="text-4xl font-bold mb-8">Codeless Auth</h1>
// // // // // //       <div className="w-full max-w-md">
// // // // // //         <Auth
// // // // // //           supabaseClient={supabaseBrowser}
// // // // // //           appearance={{ theme: ThemeSupa }}
// // // // // //           theme="dark"
// // // // // //           providers={[]}
// // // // // //           redirectTo="http://localhost:3000"  // Ensures smooth redirect after actions
// // // // // //         />
// // // // // //       </div>
// // // // // //     </main>
// // // // // //   );
// // // // // // }

// // // // // 'use client';

// // // // // import { Auth } from '@supabase/auth-ui-react';
// // // // // import { ThemeSupa } from '@supabase/auth-ui-shared';
// // // // // import { useEffect, useState } from "react";
// // // // // import { supabaseBrowser } from "@/lib/supabase";
// // // // // import { useRouter } from "next/navigation";
// // // // // import { Button } from "@/components/ui/button";
// // // // // import { Input } from "@/components/ui/input";
// // // // // import { ScrollArea } from "@/components/ui/scroll-area";
// // // // // import { Avatar, AvatarFallback } from "@/components/ui/avatar";
// // // // // import { cn } from "@/lib/utils";

// // // // // type Message = {
// // // // //   role: "user" | "assistant";
// // // // //   content: string;
// // // // // };

// // // // // export default function ChatPage() {
// // // // //   const [user, setUser] = useState<any>(null);
// // // // //   const [messages, setMessages] = useState<Message[]>([
// // // // //     { role: "assistant", content: "Hello! Describe the app or code you want to build." }
// // // // //   ]);
// // // // //   const [input, setInput] = useState("");
// // // // //   const [loading, setLoading] = useState(false);
// // // // //   const router = useRouter();

// // // // //   useEffect(() => {
// // // // //     // Check auth + redirect if not logged in
// // // // //     supabaseBrowser.auth.getSession().then(({ data: { session } }) => {
// // // // //       if (!session) {
// // // // //         router.push("/"); // Or keep auth form — we'll refine
// // // // //       } else {
// // // // //         setUser(session.user);
// // // // //       }
// // // // //     });

// // // // //     // Listen for auth changes
// // // // //     supabaseBrowser.auth.onAuthStateChange((_event, session) => {
// // // // //       if (!session) router.push("/");
// // // // //       setUser(session?.user ?? null);
// // // // //     });
// // // // //   }, [router]);

// // // // //   // const sendMessage = () => {
// // // // //   //   if (!input.trim() || loading) return;

// // // // //   //   const newMessages = [...messages, { role: "user", content: input }];
// // // // //   //   setMessages(newMessages);
// // // // //   //   setInput("");
// // // // //   //   setLoading(true);

// // // // //   //   // Fake assistant response (for now — real LLM later)
// // // // //   //   setTimeout(() => {
// // // // //   //     setMessages([...newMessages, { role: "assistant", content: "Thinking... (AI coming in Phase 7)" }]);
// // // // //   //     setLoading(false);
// // // // //   //   }, 1000);
// // // // //   // };
// // // // //   const sendMessage = (e: React.FormEvent) => {
// // // // //     e.preventDefault(); // Prevents form refresh

// // // // //     if (!input.trim() || loading) return;

// // // // //     // Add user message (functional update — no stale closure)
// // // // //     setMessages((prev) => [...prev, { role: "user", content: input }]);

// // // // //     setInput("");
// // // // //     setLoading(true);

// // // // //     // Fake assistant response (functional again)
// // // // //     setTimeout(() => {
// // // // //       setMessages((prev) => [
// // // // //         ...prev,
// // // // //         { role: "assistant", content: "Thinking... (AI coming in Phase 7)" },
// // // // //       ]);
// // // // //       setLoading(false);
// // // // //     }, 1500); // Slightly longer for realism
// // // // //   };

// // // // //   if (!user) {
// // // // //     return <div className="flex min-h-screen items-center justify-center">Loading...</div>;
// // // // //   }

// // // // //   if (!user) {
// // // // //     return (
// // // // //       <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-background">
// // // // //         <h1 className="text-4xl font-bold mb-8">Codeless Auth</h1>
// // // // //         <div className="w-full max-w-md">
// // // // //           <Auth
// // // // //             supabaseClient={supabaseBrowser}
// // // // //             appearance={{ theme: ThemeSupa }}
// // // // //             theme="dark"
// // // // //             providers={[]}
// // // // //             redirectTo="http://localhost:3000"
// // // // //           />
// // // // //         </div>
// // // // //       </main>
// // // // //     );
// // // // //   }

// // // // //   return (
// // // // //     <div className="flex h-screen flex-col bg-background">
// // // // //       <header className="border-b p-4">
// // // // //         <div className="flex items-center justify-between">
// // // // //           <h1 className="text-2xl font-bold">Codeless Chat</h1>
// // // // //           <Button variant="outline" onClick={() => supabaseBrowser.auth.signOut()}>
// // // // //             Sign Out ({user.email})
// // // // //           </Button>
// // // // //         </div>
// // // // //       </header>

// // // // //       <ScrollArea className="flex-1 p-4">
// // // // //         <div className="mx-auto max-w-4xl space-y-4">
// // // // //           {messages.map((msg, i) => (
// // // // //             <div
// // // // //               key={i}
// // // // //               className={cn(
// // // // //                 "flex gap-4",
// // // // //                 msg.role === "user" ? "justify-end" : "justify-start"
// // // // //               )}
// // // // //             >
// // // // //               {msg.role === "assistant" && (
// // // // //                 <Avatar>
// // // // //                   <AvatarFallback>AI</AvatarFallback>
// // // // //                 </Avatar>
// // // // //               )}
// // // // //               <div
// // // // //                 className={cn(
// // // // //                   "max-w-lg rounded-lg px-4 py-2",
// // // // //                   msg.role === "user"
// // // // //                     ? "bg-primary text-primary-foreground"
// // // // //                     : "bg-muted"
// // // // //                 )}
// // // // //               >
// // // // //                 {msg.content}
// // // // //               </div>
// // // // //               {msg.role === "user" && (
// // // // //                 <Avatar>
// // // // //                   <AvatarFallback>U</AvatarFallback>
// // // // //                 </Avatar>
// // // // //               )}
// // // // //             </div>
// // // // //           ))}
// // // // //           {loading && <div className="text-center text-muted-foreground">Typing...</div>}
// // // // //         </div>
// // // // //       </ScrollArea>

// // // // //       <div className="border-t p-4">
// // // // //         {/* <form
// // // // //           onSubmit={(e) => {
// // // // //             e.preventDefault();
// // // // //             sendMessage();
// // // // //           }}
// // // // //           className="mx-auto flex max-w-4xl gap-2"
// // // // //         > */}
// // // // //         <form
// // // // //           onSubmit={sendMessage} // ← Direct call
// // // // //           className="mx-auto flex max-w-4xl gap-2"
// // // // //         >
// // // // //           <Input
// // // // //             value={input}
// // // // //             onChange={(e) => setInput(e.target.value)}
// // // // //             placeholder="Describe your app..."
// // // // //             disabled={loading}
// // // // //             className="flex-1"
// // // // //           />
// // // // //           <Button type="submit" disabled={loading}>
// // // // //             Send
// // // // //           </Button>
// // // // //         </form>
// // // // //       </div>
// // // // //     </div>
// // // // //   );
// // // // // }


// // // // import { supabaseBrowser } from "@/lib/supabase";
// // // // import { Auth } from '@supabase/auth-ui-react';
// // // // import { ThemeSupa } from '@supabase/auth-ui-shared';
// // // // import ChatClient from "./ChatClient" // We'll create this next

// // // // // Server-side session check (reliable — no cookie sync issues)
// // // // const getSession = async () => {
// // // //   // For server component, we can use direct client (anon key is public-safe for getSession)
// // // //   const supabase = supabaseBrowser;
// // // //   const { data: { session } } = await supabase.auth.getSession();
// // // //   return session;
// // // // };

// // // // export default async function Home() {
// // // //   const session = await getSession();

// // // //   if (!session) {
// // // //     return (
// // // //       <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-background">
// // // //         <h1 className="text-4xl font-bold mb-8">Codeless Auth</h1>
// // // //         <div className="w-full max-w-md">
// // // //           <Auth
// // // //             supabaseClient={supabaseBrowser}
// // // //             appearance={{ theme: ThemeSupa }}
// // // //             theme="dark"
// // // //             providers={[]}
// // // //             redirectTo="http://localhost:3000"
// // // //           />
// // // //         </div>
// // // //       </main>
// // // //     );
// // // //   }

// // // //   return <ChatClient initialUser={session.user} />;
// // // // }\




// // // import { Auth } from '@supabase/auth-ui-react';
// // // import { ThemeSupa } from '@supabase/auth-ui-shared';
// // // import { supabaseBrowser } from '@/lib/supabase';
// // // import ChatClient from './ChatClient';

// // // // Server-side session check (runs on server — reliable)
// // // async function getSession() {
// // //   const { data: { session } } = await supabaseBrowser.auth.getSession();
// // //   return session;
// // // }

// // // export default async function Home() {
// // //   const session = await getSession();

// // //   if (!session) {
// // //     return (
// // //       <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-background">
// // //         <h1 className="text-4xl font-bold mb-8">Codeless Auth</h1>
// // //         <div className="w-full max-w-md">
// // //           <Auth
// // //             supabaseClient={supabaseBrowser}
// // //             appearance={{ theme: ThemeSupa }}
// // //             theme="dark"
// // //             providers={[]}
// // //             redirectTo="http://localhost:3000"
// // //           />
// // //         </div>
// // //       </main>
// // //     );
// // //   }

// // //   return <ChatClient initialUser={session.user} />;
// // // }

// // "use client";

// // import { supabaseBrowser } from '@/lib/supabase';
// // import ClientAuth from './ClientAuth';
// // import ChatClient from './ChatClient';

// // // Server-side session check (reliable)
// // async function getSession() {
// //   const { data: { session } } = await supabaseBrowser.auth.getSession();
// //   return session;
// // }

// // export default async function Home() {
// //   const session = await getSession();

// //   if (!session) {
// //     return <ClientAuth />;
// //   }

// //   return <ChatClient initialUser={session.user} />;
// // }

// import { supabaseBrowser } from '@/lib/supabase';
// import ClientAuth from './ClientAuth';
// import ChatClient from './ChatClient';

// // Server-side session check (secure, reliable)
// async function getSession() {
//   const { data: { session } } = await supabaseBrowser.auth.getSession();
//   return session;
// }

// export default async function Home() {
//   const session = await getSession();

//   if (!session) {
//     return <ClientAuth />;
//   }

//   return <ChatClient initialUser={session.user} />;
// }

'use client';

import { useEffect, useState } from 'react';
import { supabaseBrowser } from '@/lib/supabase';
import { Auth } from '@supabase/auth-ui-react';
import { ThemeSupa } from '@supabase/auth-ui-shared';
import ChatClient from './ChatClient';

export default function Home() {
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    // Initial session check
    supabaseBrowser.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null);
    });

    // Listener for auth changes (login → auto to chat)
    const { data: listener } = supabaseBrowser.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
    });

    return () => listener.subscription.unsubscribe();
  }, []);

  if (!user) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-background">
        <h1 className="text-4xl font-bold mb-8">Codeless Auth</h1>
        <div className="w-full max-w-md">
          <Auth
            supabaseClient={supabaseBrowser}
            appearance={{ theme: ThemeSupa }}
            theme="dark"
            providers={[]}
            redirectTo="http://localhost:3000"
          />
        </div>
      </main>
    );
  }

  return <ChatClient initialUser={user} />;
}