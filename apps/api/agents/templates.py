# apps/api/agents/templates.py
"""
Template files for Class A React apps
"""

# Folder structure visualization
FOLDER_STRUCTURE = """my-app/                           # Root folder
├── 📄 package.json              # [TEMPLATE: fill only "name" field]
├── 📄 package-lock.json         # [IGNORE: auto-generated]
├── 📄 README.md                 # [TEMPLATE: fill description only]
├── 📄 .gitignore                # [TEMPLATE: standard]
├── 📄 .env.example              # [TEMPLATE: empty]
├── 📄 vercel.json               # [TEMPLATE: standard Vercel config]
├── ⚙️ vite.config.js            # [TEMPLATE: standard Vite config]
├── ⚙️ tailwind.config.js        # [TEMPLATE: standard Tailwind config]
├── ⚙️ postcss.config.js         # [TEMPLATE: standard PostCSS config]
├── 📄 index.html               # [TEMPLATE: fill title only]
├── 📁 public/
│   ├── 📄 favicon.ico          # [TEMPLATE: generic icon]
│   └── 📄 robots.txt           # [TEMPLATE: standard]
└── 📁 src/
    ├── 📄 main.jsx             # [TEMPLATE: standard React entry]
    ├── 📄 App.jsx              # [GENERATE: plan completely]
    ├── 📄 index.css            # [TEMPLATE: Tailwind imports]
    ├── 📁 components/          # [GENERATE: plan components]
    ├── 📁 hooks/               # [GENERATE: plan custom hooks]
    └── 📁 utils/               # [GENERATE: plan utility functions]
"""

# Template file contents


# Example output for reference
EXAMPLE_OUTPUT = {
    "project_name": "",
    "app_title": "", 
    "app_description": "",
    "files_to_generate": [
        {
            "path": "src/App.jsx",
            "description":""
        },
        {
            "path": "src/components/",
            "description": ""
        },
        {
            "path": "src/components/", 
            "description": ""
        },
        {
            "path": "src/hooks/",
            "description": ""
        }
    ]
}



TEMPLATE_CONTENTS = {
    "package.json": """{
  "name": "{{APP_NAME}}",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.0.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "tailwindcss": "^3.3.0",
    "vite": "^4.0.0"
  }
}""",

    "README.md": """# {{APP_TITLE}}
    
    {{APP_DESCRIPTION}}

    ## Features
    - Built with React + Vite
    - Styled with Tailwind CSS
    - Fast development experience

    ## Getting Started
    1. Install dependencies: `npm install`
    2. Start dev server: `npm run dev`
    3. Build for production: `npm run build`

    ## Deployment
    This project is ready for deployment on Vercel, Netlify, or GitHub Pages.""",

    ".gitignore": """
    # Dependencies
    node_modules/
    # Build outputs
    dist/
    
    # Environment variables
    .env
    .env.local
    .env.development.local
    .env.test.local
    .env.production.local

    # Logs
    npm-debug.log*
    yarn-debug.log*
    yarn-error.log*

    # OS files
    .DS_Store
    Thumbs.db

    # IDE files
    .vscode/
    .idea/
    *.swp
    *.swo
""",

    ".env.example": """
    # Environment variables template
    # Copy this to .env.local and fill in your values
    # API Keys (if needed)
    # VITE_API_KEY=your_api_key_here
    # 
    # App Configuration
    VITE_APP_NAME={{APP_TITLE}}
    """,
    
    "vercel.json": """{
      \"buildCommand\": \"npm run build\",
      \"devCommand\": \"npm run dev\",
      \"installCommand\": \"npm install\",
      \"framework\": \"vite\",
      \"outputDirectory\": \"dist\"
    }""",

    "vite.config.js": """import { defineConfig } from 'vite'
    import react from '@vitejs/plugin-react'

    export default defineConfig({
        plugins: [react()],
        build: {
            outDir: 'dist'
        }
    })""",


    "tailwind.config.js": """
    /** @type {import('tailwindcss').Config} */
    export default {
        content: [
                "./index.html",    "./src/**/*.{js,ts,jsx,tsx}",
        ],
        theme: {
            extend: {},
        },
        plugins: [],
    }""",

    "postcss.config.js": """export default {
        plugins: {
            tailwindcss: {},
            autoprefixer: {},
        },
    }""",

    "index.html": """<!DOCTYPE html>
    <html lang=\"en\">
    <head>
        <meta charset=\"UTF-8\" />
            <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
                <title>{{APP_TITLE}}</title>
                </head>
                <body>
                    <div id=\"root\"></div>
                        <script type=\"module\" src=\"/src/main.jsx\"></script>
                        </body>
                        </html>""",
    
    "public/favicon.ico": "BINARY_FILE_CONTENT",
    
    "public/robots.txt": """User-agent: *
    Allow: /
    Sitemap: https://your-domain.com/sitemap.xml""",
    
    "src/main.jsx": """
    import React from 'react'
    import ReactDOM from 'react-dom/client'
    import App from './App.jsx'
    import './index.css'

    ReactDOM.createRoot(document.getElementById('root')).render(
      <React.StrictMode>
        <App />
      </React.StrictMode>
    )""",

    "src/index.css": """
    @tailwind base;
    @tailwind components;
    @tailwind utilities;

    html {
        scroll-behavior: smooth;
    }

    :root {
        font-family: Inter, system-ui, Avenir, Helvetica, Arial, sans-serif;
        line-height: 1.5;
        font-weight: 400;
    }

    :root {
    font-family: Inter, system-ui, Avenir, Helvetica, Arial, sans-serif;
    line-height: 1.5;
    font-weight: 400;
    }

    body {
    margin: 0;
    min-height: 100vh;
    }

    #root {
    width: 100%;
    min-height: 100vh;
    }
    """}