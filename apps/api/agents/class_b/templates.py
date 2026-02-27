
FOLDER_STRUCTURE_B = """
my-app/
├── 📄 .env.example                  # Environment variables template (Supabase URL, anon key)
├── 📄 .gitignore                     # Standard gitignore (node_modules, dist, .env)
├── 📄 README.md                       # Project description, setup instructions
├── 📄 index.html                      # Entry HTML with root div, title placeholder
├── 📄 package.json                     # Dependencies (React, Supabase, React Query, etc.)
├── 📄 postcss.config.js                 # PostCSS config (Tailwind + autoprefixer)
├── 📄 tailwind.config.js                 # Tailwind config (content, theme, plugins)
├── 📄 tsconfig.json                      # TypeScript config (paths, strict mode)
├── 📄 tsconfig.node.json                  # TypeScript config for Vite
├── 📄 vite.config.ts                       # Vite config with React plugin and path alias
├── 📁 public/
│   └── 📄 favicon.ico                      # Generic favicon (placeholder)
├── 📁 src/
│   ├── 📄 main.tsx                          # Entry point: ReactDOM render with providers
│   ├── 📄 App.tsx                            # Root component with routes (to be extended)
│   ├── 📄 index.css                          # Tailwind imports + global styles
│   ├── 📄 vite-env.d.ts                       # Vite environment types
│   ├── 📁 components/                          # Reusable UI components (AI generated)
│   ├── 📁 pages/                               # Page components (AI generated)
│   ├── 📁 hooks/                                # Custom React hooks (AI generated)
│   ├── 📁 lib/                                  # Utilities, helpers (AI generated)
│   ├── 📁 types/                                # TypeScript types/interfaces (AI generated)
│   └── 📁 integrations/
│       └── 📁 supabase/
│           ├── 📄 client.ts                     # Supabase client instance (template)
│           └── 📄 types.ts                       # Database types (can be generated)
└── 📁 supabase/
    ├── 📁 migrations/                            # SQL migration files (AI generated)
    └── 📄 seed.sql                                # Optional seed data (not required)
"""



TEMPLATE_CONTENTS_B = {
    ".env.example":"""
VITE_SUPABASE_URL="{{SUPABASE_URL}}"
VITE_SUPABASE_ANON_KEY="{{SUPABASE_ANON_KEY}}"
""",
".gitignore":"""
# Logs
logs
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*
lerna-debug.log*

# Dependencies
node_modules
dist
dist-ssr
*.local

# Editor directories and files
.vscode/*
!.vscode/extensions.json
.idea
.DS_Store
*.suo
*.ntvs*
*.njsproj
*.sln
*.sw?
""",
"README.md":"""
# {{APP_TITLE}}

{{APP_DESCRIPTION}}

## Tech Stack
- React + TypeScript + Vite
- Tailwind CSS
- Supabase (authentication, database, storage)
- TanStack Query (React Query)

## Getting Started
1. Install dependencies: `npm install`
2. Copy `.env.example` to `.env` and fill in your Supabase credentials.
3. Start the development server: `npm run dev`
4. Build for production: `npm run build`

## Environment Variables
- `VITE_SUPABASE_URL`: Your Supabase project URL.
- `VITE_SUPABASE_ANON_KEY`: Your Supabase anonymous key.

## Deployment
This project is ready to be deployed to Vercel, Netlify, or any static hosting provider. Make sure to set the environment variables on your hosting platform.
""",
"index.html":"""
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/favicon.ico" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{{APP_TITLE}}</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
""",
"package.json":"""
{
  "name": "{{PROJECT_NAME}}",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.15.0",
    "@supabase/supabase-js": "^2.0.0",
    "@tanstack/react-query": "^4.28.0",
    "@tanstack/react-query-devtools": "^4.28.0"
  },
  "devDependencies": {
    "@types/react": "^18.0.0",
    "@types/react-dom": "^18.0.11",
    "@vitejs/plugin-react": "^4.0.0",
    "autoprefixer": "^10.4.14",
    "postcss": "^8.4.23",
    "tailwindcss": "^3.3.0",
    "typescript": "^4.9.5",
    "vite": "^4.3.0"
  }
}
""",
"postcss.config.js":"""
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
""",
"tailwind.config.js":"""
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {},
  },
  plugins: [],
};
""",
"tsconfig.json":"""
{
  "compilerOptions": {
    "target": "ES2022",
    "useDefineForClassFields": true,
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  },
  "include": ["src", "vite.config.ts"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
""",
"tsconfig.node.json":"""
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
""",
"vite.config.ts":"""
import path from "path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src")
    }
  },
  server: {
    port: 5173
  }
});
""",
"src/main.tsx":"""
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
""",
"src/index.css":"""
@tailwind base;
@tailwind components;
@tailwind utilities;

html, body, #root {
  height: 100%;
}
""",
"src/vite-env.d.ts":"""
/// <reference types="vite/client" />
""",
"src/integrations/supabase/client.ts":"""
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Missing Supabase environment variables. Please check your .env file.');
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
""",
"src/integrations/supabase/types.ts":"""
export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[];

export interface Database {
  public: {
    Tables: {
      // Tables will be defined here by the AI when migrations are generated
    };
    Views: Record<string, never>;
    Functions: Record<string, never>;
    Enums: Record<string, never>;
  };
}
"""
}



EXAMPLE_OUTPUT_B = {
    "project_name": "my-app",
    "app_title": "My App",
    "app_description": "A full‑stack app with Supabase.",
    "database": {
        "tables": [
            {
                "name": "todos",
                "columns": [
                    {"name": "id", "type": "uuid", "primary": True, "default": "gen_random_uuid()"},
                    {"name": "user_id", "type": "uuid", "references": "auth.users.id"},
                    {"name": "title", "type": "text"},
                    {"name": "completed", "type": "boolean", "default": False},
                    {"name": "created_at", "type": "timestamptz", "default": "now()"}
                ],
                "rls_policies": [
                    "authenticated users can SELECT rows where user_id = auth.uid()",
                    "authenticated users can INSERT rows with user_id = auth.uid()",
                    "authenticated users can UPDATE rows where user_id = auth.uid()",
                    "authenticated users can DELETE rows where user_id = auth.uid()"
                ]
            }
        ]
    },
    "auth": {
        "providers": ["email"],
        "pages": ["/auth"]
    },
    "pages": [
        {"path": "/", "name": "Dashboard", "auth": True},
        {"path": "/auth", "name": "Auth", "auth": False}
    ],
    "components": [
        {"path": "src/components/TodoList.tsx", "description": "Displays todos and allows add/complete/delete."},
        {"path": "src/components/AuthForm.tsx", "description": "Login/signup form."}
    ],
    "files_to_generate": [
        {"path": "src/App.tsx", "description": "Main app with routing."},
        {"path": "src/pages/Dashboard.tsx", "description": "Dashboard page."},
        {"path": "src/pages/Auth.tsx", "description": "Authentication page."},
        {"path": "src/components/TodoList.tsx", "description": "Todo list component."},
        {"path": "src/components/AuthForm.tsx", "description": "Auth form component."},
        {"path": "supabase/migrations/001_create_todos.sql", "description": "SQL migration for todos table and RLS."}
    ]
}
