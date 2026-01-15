// 'use client';

// import { Auth } from '@supabase/auth-ui-react';
// import { ThemeSupa } from '@supabase/auth-ui-shared';
// import { supabaseBrowser } from '@/lib/supabase';

// export default function ClientAuth() {
//   return (
//     <div className="flex min-h-screen flex-col items-center justify-center p-24 bg-background">
//       <h1 className="text-4xl font-bold mb-8">Codeless Auth</h1>
//       <div className="w-full max-w-md">
//         <Auth
//           supabaseClient={supabaseBrowser}
//           appearance={{ theme: ThemeSupa }}
//           theme="dark"
//           providers={[]}
//           redirectTo="http://localhost:3000"
//         />
//       </div>
//     </div>
//   );
// }

'use client';

import { Auth } from '@supabase/auth-ui-react';
import { ThemeSupa } from '@supabase/auth-ui-shared';
import { supabaseBrowser } from '@/lib/supabase';

export default function ClientAuth() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-24 bg-background">
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
    </div>
  );
}