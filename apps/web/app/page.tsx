
// 'use client';

// import { useEffect, useState } from 'react';
// import { supabaseBrowser } from '@/lib/supabase';
// import ClientAuth from './components/ClientAuth/ClientAuth';
// import ChatClient from './components/ChatClient/ChatClient';

// export default function HomePage() {
//   const [user, setUser] = useState<any>(null);
//   const [loading, setLoading] = useState(true);
  
//   useEffect(() => {
//     // Check initial session
//     supabaseBrowser.auth.getSession().then(({ data: { session } }) => {
//       setUser(session?.user ?? null);
//       setLoading(false);
//     });
    
//     // Listen for auth changes
//     const { data: listener } = supabaseBrowser.auth.onAuthStateChange(
//       (_event, session) => {
//         setUser(session?.user ?? null);
//         setLoading(false);
//       }
//     );
    
//     return () => listener.subscription.unsubscribe();
//   }, []);
  
//   if (loading) {
//     return (
//       <div className="flex min-h-screen items-center justify-center bg-background">
//         <div className="text-lg">Loading...</div>
//       </div>
//     );
//   }
  
//   if (!user) {
//     return <ClientAuth />;
//   }
  
//   return <ChatClient initialUser={user} />;
// }

// apps/web/app/page.tsx
'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { supabaseBrowser } from '@/lib/supabase';
import ClientAuth from './components/ClientAuth/ClientAuth';

export default function HomePage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    async function checkUser() {
      try {
        const { data: { user } } = await supabaseBrowser.auth.getUser();
        
        if (user) {
          // ✅ REDIRECT TO DASHBOARD, NOT CHAT
          router.push('/dashboard');
        } else {
          setUser(null);
        }
      } catch (error) {
        console.error('Error checking user:', error);
        setUser(null);
      } finally {
        setLoading(false);
      }
    }
    
    checkUser();
    
    const { data: listener } = supabaseBrowser.auth.onAuthStateChange(
      (_event, session) => {
        if (session?.user) {
          router.push('/dashboard');
        } else {
          setUser(null);
        }
        setLoading(false);
      }
    );
    
    return () => listener.subscription.unsubscribe();
  }, [router]);
  
  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-900">
        <div className="text-center">
          <div className="h-12 w-12 animate-spin rounded-full border-4 border-blue-500 border-t-transparent mx-auto mb-4" />
          <p className="text-slate-400">Loading...</p>
        </div>
      </div>
    );
  }
  
  if (!user) {
    return <ClientAuth />;
  }
  
  // This should never render because we redirect before this point
  return null;
}