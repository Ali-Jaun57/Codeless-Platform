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