// import Image, { type ImageProps } from "next/image";
// // import { Button } from "@repo/ui/button";
// import styles from "./page.module.css";

// type Props = Omit<ImageProps, "src"> & {
//   srcLight: string;
//   srcDark: string;
// };

// const ThemeImage = (props: Props) => {
//   const { srcLight, srcDark, ...rest } = props;

//   return (
//     <>
//       <Image {...rest} src={srcLight} className="imgLight" />
//       <Image {...rest} src={srcDark} className="imgDark" />
//     </>
//   );
// };

// export default function Home() {
//   return (
//     <div className={styles.page}>
//       <main className={styles.main}>
//         <ThemeImage
//           className={styles.logo}
//           srcLight="turborepo-dark.svg"
//           srcDark="turborepo-light.svg"
//           alt="Turborepo logo"
//           width={180}
//           height={38}
//           priority
//         />
//         <ol>
//           <li>
//             Get started by editing <code>apps/web/app/page.tsx</code>
//           </li>
//           <li>Save and see your changes instantly.</li>
//         </ol>

//         <div className={styles.ctas}>
//           <a
//             className={styles.primary}
//             href="https://vercel.com/new/clone?demo-description=Learn+to+implement+a+monorepo+with+a+two+Next.js+sites+that+has+installed+three+local+packages.&demo-image=%2F%2Fimages.ctfassets.net%2Fe5382hct74si%2F4K8ZISWAzJ8X1504ca0zmC%2F0b21a1c6246add355e55816278ef54bc%2FBasic.png&demo-title=Monorepo+with+Turborepo&demo-url=https%3A%2F%2Fexamples-basic-web.vercel.sh%2F&from=templates&project-name=Monorepo+with+Turborepo&repository-name=monorepo-turborepo&repository-url=https%3A%2F%2Fgithub.com%2Fvercel%2Fturborepo%2Ftree%2Fmain%2Fexamples%2Fbasic&root-directory=apps%2Fdocs&skippable-integrations=1&teamSlug=vercel&utm_source=create-turbo"
//             target="_blank"
//             rel="noopener noreferrer"
//           >
//             <Image
//               className={styles.logo}
//               src="/vercel.svg"
//               alt="Vercel logomark"
//               width={20}
//               height={20}
//             />
//             Deploy now
//           </a>
//           <a
//             href="https://turborepo.com/docs?utm_source"
//             target="_blank"
//             rel="noopener noreferrer"
//             className={styles.secondary}
//           >
//             Read our docs
//           </a>
//         </div>
//         {/* <Button appName="web" className={styles.secondary}>
//           Open alert
//         </Button> */}
//         <button className="bg-blue-500 text-white px-4 py-2 rounded">Get Started</button>
//       </main>
//       <footer className={styles.footer}>
//         <a
//           href="https://vercel.com/templates?search=turborepo&utm_source=create-next-app&utm_medium=appdir-template&utm_campaign=create-next-app"
//           target="_blank"
//           rel="noopener noreferrer"
//         >
//           <Image
//             aria-hidden
//             src="/window.svg"
//             alt="Window icon"
//             width={16}
//             height={16}
//           />
//           Examples
//         </a>
//         <a
//           href="https://turborepo.com?utm_source=create-turbo"
//           target="_blank"
//           rel="noopener noreferrer"
//         >
//           <Image
//             aria-hidden
//             src="/globe.svg"
//             alt="Globe icon"
//             width={16}
//             height={16}
//           />
//           Go to turborepo.com →
//         </a>
//       </footer>
//     </div>
//   );
// }

// import Image from "next/image";

// export default function Home() {
//   return (
//     <main className="flex min-h-screen flex-col items-center justify-center p-24">
//       <h1 className="text-4xl font-bold mb-8">Codeless — Welcome!</h1>
//       <p className="text-xl">Monorepo setup complete. Ready for real UI.</p>
//       {/* Temporary button until shadcn/ui */}
//       <button className="mt-8 bg-blue-600 text-white px-6 py-3 rounded-lg">
//         Let's Build
//       </button>
//     </main>
//   );
// }

'use client'; // This makes it a Client Component (needed for interactive auth UI)

import { useEffect, useState } from 'react';
import { supabaseBrowser } from '../lib/supabase';
import { Auth } from '@supabase/auth-ui-react';
import { ThemeSupa } from '@supabase/auth-ui-shared';

export default function Home() {
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    // Check current session on load
    supabaseBrowser.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null);
    });

    // Listen for auth changes (login/logout)
    const { data: listener } = supabaseBrowser.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
    });

    return () => listener.subscription.unsubscribe();
  }, []);

  if (user) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center p-24">
        <h1 className="text-4xl font-bold mb-8">Welcome, {user.email}!</h1>
        <button
          onClick={() => supabaseBrowser.auth.signOut()}
          className="bg-red-600 text-white px-6 py-3 rounded-lg"
        >
          Sign Out
        </button>
      </main>
    );
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <h1 className="text-4xl font-bold mb-8">Codeless Auth</h1>
      <div className="w-full max-w-md">
        <Auth
          supabaseClient={supabaseBrowser}
          appearance={{ theme: ThemeSupa }}
          theme="dark"
          providers={[]}
          redirectTo="http://localhost:3000"  // Ensures smooth redirect after actions
        />
      </div>
    </main>
  );
}