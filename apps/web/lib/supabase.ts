// // // // // // // apps/web/lib/supabase.ts
// // // // // // import { createBrowserClient } from '@supabase/ssr';

// // // // // // // Browser client (used in Client Components like our page.tsx)
// // // // // // // Automatically reads NEXT_PUBLIC_ env vars — no args needed
// // // // // // export const supabaseBrowser = createBrowserClient(
// // // // // //   process.env.NEXT_PUBLIC_SUPABASE_URL!,
// // // // // //   process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
// // // // // // );

// // // // // // // Optional: Server client for future Server Components / Actions
// // // // // // // We'll expand this later
// // // // // // export const getSupabaseServer = () => createBrowserClient(
// // // // // //   process.env.NEXT_PUBLIC_SUPABASE_URL!,
// // // // // //   process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
// // // // // // );

// // // // // // // Why this way?
// // // // // // // - @supabase/ssr is the 2025–2026 recommended package for Next.js App Router
// // // // // // // - Explicit args ensure clear error if env missing (what you saw)
// // // // // // // - Works identically in browser + server contexts

// // // // // // apps/web/lib/supabase.ts
// // // // // import { createBrowserSupabaseClient } from '@supabase/auth-helpers-nextjs';

// // // // // // Browser client — handles sessions/cookies with middleware
// // // // // export const supabaseBrowser = createBrowserSupabaseClient();

// // // // // // Optional server client for later (Server Components/Actions)
// // // // // // export const supabaseServer = createServerSupabaseClient(...);

// // // // // apps/web/lib/supabase.ts
// // // // import { createBrowserClient } from '@supabase/ssr';

// // // // // Browser client — reads NEXT_PUBLIC_ env vars automatically
// // // // export const supabaseBrowser = createBrowserClient(
// // // //   process.env.NEXT_PUBLIC_SUPABASE_URL!,
// // // //   process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
// // // // );

// // // // apps/web/lib/supabase.ts
// // // import { createBrowserSupabaseClient } from '@supabase/auth-helpers-nextjs';

// // // // Browser client — auto reads env + handles cookies with middleware
// // // export const supabaseBrowser = createBrowserSupabaseClient();

// // // apps/web/lib/supabase.ts
// // import { createBrowserClient } from '@supabase/ssr';

// // // Browser client for client components (chat, auth form)
// // export const supabaseBrowser = createBrowserClient(
// //   process.env.NEXT_PUBLIC_SUPABASE_URL!,
// //   process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
// // );

// // apps/web/lib/supabase.ts
// import { createBrowserClient } from '@supabase/ssr';

// export const supabaseBrowser = createBrowserClient(
//   process.env.NEXT_PUBLIC_SUPABASE_URL!,
//   process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
// );

import { createBrowserClient } from '@supabase/ssr';

export const supabaseBrowser = createBrowserClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);