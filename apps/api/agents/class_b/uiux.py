

# # import json
# # import time
# # from langchain_openai import ChatOpenAI
# # from langchain_core.messages import HumanMessage, AIMessage
# # from utils.logger import Logger
# # from utils.json_parser import extract_json_from_text
# # from ..shared.agent_state import AgentState

# # logger = Logger(__name__)

# # class UIUX:
# #     def __init__(self, llm: ChatOpenAI):
# #         self.llm = llm
# #         logger.step("Class B UI/UX Agent", "initialized")



# import json
# import re
# from langchain_anthropic import ChatAnthropic
# from langchain_core.messages import HumanMessage, AIMessage
# from utils.logger import Logger
# from ..shared.agent_state import AgentState

# # Optional json5 for lenient parsing
# try:
#     import json5
#     HAS_JSON5 = True
# except ImportError:
#     HAS_JSON5 = False
#     json5 = None

# logger = Logger(__name__)


# class UIUX:
#     def __init__(self, llm: ChatAnthropic):
#         self.llm = llm
#         logger.step("Class B UI/UX Agent", "initialized")

#     def __call__(self, state: AgentState) -> dict:
#         logger.step("UI/UX", "started (enhancement)")

#         if not state.files:
#             logger.warning("⚠️ No files to enhance")
#             return {"files": state.files, "messages": state.messages}

#         # Only enhance frontend source files — skip SQL migrations, config, env files
#         SKIP_EXTENSIONS = {".sql", ".env", ".md", ".json", ".toml", ".yaml", ".yml"}
#         SKIP_PREFIXES   = ("supabase/", "public/", "dist/", ".git")

#         files_for_prompt = []
#         for f in state.files:
#             path = f.get("path", "")
#             ext  = "." + path.rsplit(".", 1)[-1] if "." in path else ""
#             if ext in SKIP_EXTENSIONS:
#                 continue
#             if any(path.startswith(p) for p in SKIP_PREFIXES):
#                 continue
#             files_for_prompt.append({"path": path, "content": f["content"]})

#         if not files_for_prompt:
#             logger.warning("⚠️ No eligible frontend files to enhance")
#             return {"files": state.files, "messages": state.messages}

#         prompt = self._create_prompt(files_for_prompt)

#         logger.debug("Calling Claude for Class B UI/UX enhancement...")
#         response = self.llm.invoke(state.messages + [HumanMessage(content=prompt)])
#         logger.success("✅ UI/UX enhancement response received")

#         enhanced_files = self._parse_response(response.content)

#         # Merge: enhanced files overwrite originals; untouched files are kept as-is
#         file_dict = {f["path"]: f for f in state.files}
#         for f in enhanced_files:
#             file_dict[f["path"]] = f
#         final_files = list(file_dict.values())

#         logger.info(f"🎨 UI/UX enhanced {len(enhanced_files)} files")

#         new_messages = state.messages + [AIMessage(content=response.content)]
#         return {
#             "files": final_files,
#             "messages": new_messages,
#         }

#     # ------------------------------------------------------------------
#     # Prompt
#     # ------------------------------------------------------------------

#     def _create_prompt(self, files: list) -> str:
#         return f"""You are a senior product designer and frontend engineer who has shipped interfaces at companies like Linear, Vercel, Stripe, and Notion. You have deep expertise in design systems, micro-interactions, and converting Figma-quality mockups into pixel-perfect React + Tailwind code.

# Your sole mission: **transform the provided React + Supabase app into a visually stunning, modern, production-ready UI** — without touching any logic, state, Supabase calls, auth flows, RLS policies, or database schema.

# ---

# ## HARD CONSTRAINTS — NEVER VIOLATE THESE

# - Do NOT modify any function, hook, event handler, Supabase query, state variable, prop name, or business logic.
# - Do NOT remove any imports that are used in logic.
# - Do NOT change routing, data flow, auth guards, or component responsibilities.
# - Do NOT introduce new npm dependencies. Use only Tailwind CSS, inline SVGs, and CSS custom properties.
# - Do NOT touch SQL migration files, `.env` files, or any file outside `src/`.
# - **Output JSON must be valid and complete**:
#   - Every file's `content` must be a **valid JSON string**.
#   - Escape all double quotes inside the code as `\"`.
#   - Replace every actual newline with the two characters `\\n` (backslash + n).
#   - Do **not** put raw newlines inside the string.
#   - Ensure the JSON object is **complete** — do not truncate.
# - Output ONLY a single valid JSON object — no markdown fences, no commentary, no explanation.

# ---

# ## DESIGN SYSTEM YOU MUST APPLY

# ### Color Palette
# - Use a cohesive palette: deep navy + electric indigo, slate + violet, zinc + emerald, or neutral + amber.
# - Use Tailwind's `slate`, `zinc`, `neutral` for backgrounds/surfaces — avoid plain `white`/`gray`.
# - Text hierarchy: primary `slate-900` (dark: `slate-50`), secondary `slate-500`, muted `slate-400`.
# - Always support **dark mode** via Tailwind's `dark:` variant. Default to dark if no existing theme toggle.

# ### Typography
# - Headings: `font-bold` or `font-semibold`, `tracking-tight`.
# - Body: `font-normal`, `leading-relaxed`.
# - Captions: `text-sm text-slate-500`.
# - IDs, timestamps, code snippets: `font-mono`.

# ### Spacing & Layout
# - Consistent rhythm: multiples of 4 (`p-4`, `gap-4`, `space-y-6`).
# - Cards: `rounded-xl shadow-sm border border-slate-200 dark:border-slate-700/60`.
# - Page containers: `max-w-6xl mx-auto px-4 sm:px-6 lg:px-8`.
# - Sidebars: `w-64`, collapsible on mobile.
# - CSS Grid for dashboard layouts; Flexbox for component internals.

# ### Components & Patterns

# **Buttons:**
# - Primary: `bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 text-white font-medium px-4 py-2 rounded-lg transition-all duration-150 shadow-sm hover:shadow-md`
# - Secondary: `bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300`
# - Destructive: `bg-red-500/10 hover:bg-red-500/20 text-red-600 dark:text-red-400`
# - Disabled: `opacity-50 cursor-not-allowed`
# - Loading: inline spinner SVG

# **Inputs & Forms:**
# - `bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/40 focus:border-indigo-500 transition-all`
# - Labels: `text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5 block`
# - Error: `border-red-400 focus:ring-red-400/40` + `text-red-500 text-xs mt-1`

# **Cards:**
# - `bg-white dark:bg-slate-800/50 rounded-xl border border-slate-200 dark:border-slate-700/60 shadow-sm hover:shadow-md transition-shadow duration-200 p-6`
# - Modals/floating: `backdrop-blur-sm`

# **Tables:**
# - Striped: `even:bg-slate-50 dark:even:bg-slate-800/30`
# - Sticky header: `sticky top-0 bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm`
# - Header cells: `text-xs font-semibold uppercase tracking-wider text-slate-500`

# **Navigation:**
# - Active: `bg-indigo-50 dark:bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 font-medium`
# - Inactive: `text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800`

# **Badges:**
# - Success: `bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400`
# - Warning: `bg-amber-50 text-amber-700`
# - Error: `bg-red-50 text-red-700`
# - Info: `bg-blue-50 text-blue-700`
# - All: `text-xs font-medium px-2.5 py-0.5 rounded-full`

# **Empty States:**
# - `flex flex-col items-center justify-center py-16 text-center`
# - Inline SVG icon + bold title + muted description + primary CTA

# **Loading States:**
# - Skeleton screens: `animate-pulse bg-slate-200 dark:bg-slate-700 rounded`
# - Replace plain "Loading..." text with skeleton placeholders

# ### Micro-interactions & Animations
# - All interactive elements: `transition-all duration-150 ease-in-out`
# - Cards hover: `hover:-translate-y-0.5 hover:shadow-lg`
# - Buttons click: `active:scale-95`
# - Modals: `transition-opacity duration-200` + `transition-transform duration-300`
# - Use `group` + `group-hover:` for parent-triggered child animations

# ### Iconography
# - Inline SVG icons throughout (heroicons style, 20×20 viewBox).
# - Buttons (left of label), nav items, empty states, alerts, input prefixes.
# - Size: `w-4 h-4` or `w-5 h-5`, `stroke-current stroke-2 fill-none`.

# ### Accessibility
# - All interactive elements: `focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2`
# - `aria-label` on icon-only buttons
# - Semantic HTML: `<nav>`, `<main>`, `<header>`, `<section>`, `<article>`
# - WCAG AA color contrast

# ---

# ## LAYOUT PATTERNS

# - **Dashboard:** Fixed sidebar (`w-64`) + top navbar + stat cards grid + data table/chart area
# - **Auth pages:** Centered card with logo, glassmorphism card on gradient background
# - **CRUD list:** Top bar with search + filter + CTA, data table or card grid, pagination
# - **Detail/Edit:** Two-column (form + preview) or single-column with sticky action bar

# ---

# ## OUTPUT FORMAT

# Return exactly this JSON structure:
# {{"files": [{{"path": "src/App.jsx", "content": "...full file content with escaped newlines and quotes..."}}]}}

# - Include every file you modified.
# - Omit files you did not touch.
# - File content must be the **complete file** — never truncated, never use `// ... rest unchanged`.

# ---

# ## THE FILES TO ENHANCE:

# {json.dumps(files, indent=2)}

# Analyze the app's purpose and Supabase integration, then apply every applicable rule above to produce a stunning, cohesive, production-quality UI. Output only the JSON."""

#     # ------------------------------------------------------------------
#     # Response parsing
#     # ------------------------------------------------------------------

#     def _parse_response(self, raw_content: str) -> list:
#         """Extract and parse JSON from the model's response."""
#         match = re.search(r'({[\s\S]*})', raw_content, re.DOTALL)
#         if not match:
#             logger.error("No JSON object found in UI/UX response")
#             return []
#         json_str = match.group(1)

#         try:
#             data = json.loads(json_str)
#             return data.get("files", [])
#         except json.JSONDecodeError as e:
#             logger.warning(f"Standard JSON parsing failed: {e}. Trying json5...")
#             if HAS_JSON5:
#                 try:
#                     data = json5.loads(json_str)
#                     return data.get("files", [])
#                 except Exception as e2:
#                     logger.error(f"json5 also failed: {e2}")
#             else:
#                 logger.error("json5 not installed — run `pip install json5`.")
#             return []







import json
import re
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, AIMessage
from utils.logger import Logger
from ..shared.agent_state import AgentState

try:
    import json5
    HAS_JSON5 = True
except ImportError:
    HAS_JSON5 = False
    json5 = None

logger = Logger(__name__)


class UIUX:
    def __init__(self, llm: ChatAnthropic):
        self.llm = llm
        logger.step("Class B UI/UX Agent", "initialized")

    def __call__(self, state: AgentState) -> dict:
        logger.step("UI/UX", "started (enhancement)")

        if not state.files:
            logger.warning("⚠️ No files to enhance")
            return {"files": state.files, "messages": state.messages}

        # ------------------------------------------------------------------
        # Step 1 — Filter to JSX/TSX files only
        # These are the only files that contain UI — hooks, utils, config,
        # migrations etc. have no className strings to enhance so we skip them.
        # This keeps the prompt small enough for a single coherent call.
        # ------------------------------------------------------------------
        SKIP_EXTENSIONS = {".sql", ".env", ".md", ".json", ".toml", ".yaml", ".yml", ".txt"}
        SKIP_PREFIXES   = ("supabase/", "public/", "dist/", ".git")
        SKIP_PATHS      = {
            "src/main.tsx",
            "src/main.jsx",
            "src/vite-env.d.ts",
            "src/integrations/supabase/client.ts",
            "src/integrations/supabase/types.ts",
            "src/lib/utils.ts",
        }

        jsx_files = []
        for f in state.files:
            path    = f.get("path", "")
            content = f.get("content", "")
            ext     = "." + path.rsplit(".", 1)[-1] if "." in path else ""

            # Skip by extension
            if ext in SKIP_EXTENSIONS:
                continue

            # Skip by prefix
            if any(path.startswith(p) for p in SKIP_PREFIXES):
                continue

            # Skip known non-UI files
            if path in SKIP_PATHS:
                continue

            # Skip hook files — they contain logic, not JSX
            if path.startswith("src/hooks/"):
                continue

            # Skip context files unless they contain JSX
            if path.startswith("src/context/") and "return (" not in content:
                continue

            # Only include files that actually contain JSX return statements
            if "return (" not in content and "return(" not in content:
                continue

            jsx_files.append({"path": path, "content": content})

        if not jsx_files:
            logger.warning("⚠️ No JSX files found to enhance")
            return {"files": state.files, "messages": state.messages}

        logger.info(
            f"🎨 Sending {len(jsx_files)} JSX files to Claude for enhancement: "
            f"{[f['path'] for f in jsx_files]}"
        )

        # # ------------------------------------------------------------------
        # # Step 2 — Sanitize messages
        # # Strip OpenAI reasoning blocks that Claude cannot process
        # # ------------------------------------------------------------------
        # clean_messages = []
        # for msg in state.messages:
        #     if isinstance(msg, AIMessage) and isinstance(msg.content, list):
        #         text_only = " ".join(
        #             block.get("text", "")
        #             for block in msg.content
        #             if isinstance(block, dict) and block.get("type") == "text"
        #         ).strip()
        #         if text_only:
        #             clean_messages.append(AIMessage(content=text_only))
        #     else:
        #         clean_messages.append(msg)

        # ------------------------------------------------------------------
        # Step 2 — Extract only what Claude needs to understand the app:
        #   - Index 0: original user prompt (the scenario)
        #   - Index 1: planner's response (schema, pages, components)
        # Everything else (coder dumps, critic feedback) wastes context window.
        # ------------------------------------------------------------------
        context_messages = []

        for i, msg in enumerate(state.messages):
            # Keep only the first 2 messages
            if i >= 2:
                break

            # Sanitize AIMessage — strip OpenAI reasoning blocks
            if isinstance(msg, AIMessage) and isinstance(msg.content, list):
                text_only = " ".join(
                    block.get("text", "")
                    for block in msg.content
                    if isinstance(block, dict) and block.get("type") == "text"
                ).strip()
                if text_only:
                    context_messages.append(AIMessage(content=text_only))
            else:
                context_messages.append(msg)

        # ------------------------------------------------------------------
        # Step 3 — Single call with all JSX files
        # Because we only send JSX files, the prompt is small enough for
        # one call — guaranteeing full visual coherence across all pages.
        # ------------------------------------------------------------------
        prompt = self._create_prompt(jsx_files)

        try:
            logger.debug("Calling Claude for Class B UI/UX enhancement...")
            response = self.llm.invoke(
                context_messages + [HumanMessage(content=prompt)]
            )
            logger.success("✅ UI/UX enhancement response received")
            logger.debug(f"Raw UI/UX response: {response.content}")  # Log first 500 chars

            enhanced_files = self._parse_response(response.content)

            if not enhanced_files:
                logger.warning("⚠️ No files parsed from UI/UX response — keeping originals")
                return {"files": state.files, "messages": state.messages}

        except Exception as e:
            logger.error(f"❌ UI/UX enhancement failed: {str(e)} — keeping originals")
            return {"files": state.files, "messages": state.messages}

        # ------------------------------------------------------------------
        # Step 4 — Merge: enhanced files overwrite originals
        # Files that were not sent to Claude (hooks, config etc.) are kept
        # exactly as they are.
        # ------------------------------------------------------------------
        file_dict = {f["path"]: f for f in state.files}
        for f in enhanced_files:
            file_dict[f["path"]] = f
        final_files = list(file_dict.values())

        logger.info(f"🎨 UI/UX enhanced {len(enhanced_files)} files")

        new_messages = state.messages + [AIMessage(content=response.content)]
        return {
            "files":    final_files,
            "messages": new_messages,
        }

    # ------------------------------------------------------------------
    # Prompt
    # ------------------------------------------------------------------

    def _create_prompt(self, files: list) -> str:
#         return f"""You are a senior product designer and frontend engineer who has shipped interfaces at companies like Linear, Vercel, Stripe, and Notion. You have deep expertise in design systems, micro-interactions, and converting Figma-quality mockups into pixel-perfect React + Tailwind code.

# Your sole mission: **transform ALL the provided files into a visually stunning, modern, production-ready UI** — without touching any logic, state, Supabase calls, auth flows, RLS policies, or database schema.

# You are receiving ALL the UI files of this app in one call. You MUST apply one single cohesive design system across ALL files. Every page, every component, every button must use the EXACT same colors, border radius, spacing, and typography. The app must look like it was designed by one designer, not multiple.

# ---

# ## HARD CONSTRAINTS — NEVER VIOLATE THESE

# - Do NOT modify any function, hook, event handler, Supabase query, state variable, prop name, or business logic.
# - Do NOT remove any imports that are used in logic.
# - Do NOT change routing, data flow, auth guards, or component responsibilities.
# - Do NOT introduce new npm dependencies. Use only Tailwind CSS, inline SVGs, and CSS custom properties.
# - Do NOT touch SQL migration files, `.env` files, or any file outside `src/`.
# - **Output JSON must be valid and complete**:
#   - Every file's `content` must be a **valid JSON string**.
#   - Escape all double quotes inside the code as `\"`.
#   - Replace every actual newline with the two characters `\\n` (backslash + n).
#   - Do **not** put raw newlines inside the string.
#   - Ensure the JSON object is **complete** — do not truncate.
# - Output ONLY a single valid JSON object — no markdown fences, no commentary, no explanation.

# ---
# ## DESIGN SYSTEM — DESIGN IT YOURSELF, APPLY IT EVERYWHERE

# Before writing a single line of code, look at the app's purpose and personality 
# from the file names and content. Then design ONE unique cohesive color palette 
# that fits this specific app — not a generic template.

# for example:
# - A finance app should feel trustworthy and precise.
# - A social app should feel warm and energetic.
# - A productivity app should feel clean and focused.
# - A medical app should feel calm and professional.
# - A creative app should feel bold and expressive.

# Rules for your chosen palette:
# - Pick a background color 
# - Pick ONE primary accent color that fits the app's personality
# - Pick ONE secondary/success color if the app needs it
# - Use Tailwind slate/zinc/neutral for surfaces — never plain white/gray
# - Text hierarchy: primary slate-50, secondary slate-400, muted slate-500

# Once you have decided your palette, apply it IDENTICALLY to every single file. 
# The same button class, same card class, same input class — everywhere without exception.
# Do NOT use different shades or variants across files.

# ### Components — USE THESE EXACT CLASSES IN EVERY FILE

# **Primary Button** (same in every file):
# `bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 active:scale-95 text-white font-medium px-4 py-2 rounded-lg transition-all duration-150 shadow-sm hover:shadow-md focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950`

# **Secondary Button** (same in every file):
# `bg-slate-800 hover:bg-slate-700 active:scale-95 text-slate-300 font-medium px-4 py-2 rounded-lg border border-slate-700 transition-all duration-150`

# **Destructive Button** (same in every file):
# `bg-red-500/10 hover:bg-red-500/20 active:scale-95 text-red-400 font-medium px-4 py-2 rounded-lg border border-red-500/20 transition-all duration-150`

# **Input** (same in every file):
# `w-full bg-slate-800/60 border border-slate-700/60 rounded-lg px-3 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/40 focus:border-indigo-500 transition-all duration-150`

# **Label** (same in every file):
# `text-sm font-medium text-slate-300 mb-1.5 block`

# **Card** (same in every file):
# `bg-slate-900/60 border border-slate-800/60 rounded-xl p-6 shadow-sm hover:shadow-md transition-shadow duration-200`

# **Page background** (same in every file):
# `min-h-screen bg-slate-950`

# **Header/Navbar** (same in every file):
# `sticky top-0 z-20 border-b border-slate-800/60 bg-slate-950/80 backdrop-blur-md`

# **Badges:**
# - Success: `bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-medium px-2.5 py-0.5 rounded-full`
# - Warning: `bg-amber-500/10 text-amber-400 border border-amber-500/20 text-xs font-medium px-2.5 py-0.5 rounded-full`
# - Error: `bg-red-500/10 text-red-400 border border-red-500/20 text-xs font-medium px-2.5 py-0.5 rounded-full`
# - Info: `bg-blue-500/10 text-blue-400 border border-blue-500/20 text-xs font-medium px-2.5 py-0.5 rounded-full`

# **Empty State** (same in every file):
# `flex flex-col items-center justify-center py-20 text-center`

# **Skeleton Loading** (same in every file):
# `animate-pulse bg-slate-700/60 rounded`

# ### Micro-interactions
# - All interactive elements: `transition-all duration-150 ease-in-out`
# - Cards on hover: `hover:-translate-y-0.5 hover:shadow-lg`
# - Buttons on click: `active:scale-95`
# - Use `group` + `group-hover:` for parent-triggered child animations

# ### Iconography
# - Use inline SVG icons throughout (heroicons style, 20×20 viewBox)
# - Add icons to: buttons (left of label), nav items, empty states, form inputs
# - Size: `w-4 h-4` or `w-5 h-5`, `stroke-current`, `strokeWidth="2"`, `fill="none"`

# ### Accessibility
# - All interactive elements: `focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950`
# - `aria-label` on icon-only buttons
# - Semantic HTML: `<nav>`, `<main>`, `<header>`, `<section>`

# ---

# ## LAYOUT PATTERNS — APPLY THE RIGHT ONE PER FILE

# - **Auth page:** Full-height centered layout, glassmorphism card on gradient background with blur orbs
# - **Dashboard/list page:** Sticky top navbar + max-width container + stat cards grid + data list/table
# - **Detail/form page:** Single column with sticky action bar, or two-column (form + summary)

# ---

# ## OUTPUT FORMAT

# Return exactly this JSON structure:
# {{"files": [{{"path": "src/App.tsx", "content": "...complete file with escaped newlines and quotes..."}}]}}

# - Include ALL files you received — enhance every single one.
# - File content must be the **complete file** — never truncated, never `// ... rest unchanged`.
# - Every file must feel like it belongs to the same app.

# ---

# ## THE FILES TO ENHANCE:

# {json.dumps(files, indent=2)}

# Analyze the app's purpose, decide on ONE design system, then apply it consistently to ALL {len(files)} files. Output only the JSON."""
        return f"""You are an expert Senior Frontend Architect and Creative Design System Engineer. Your sole responsibility is to take raw, functional component files generated by the Coder Agent and completely overhaul their visual identity, layouts, themes, and interactive polish.

CRITICAL MANDATE: You have absolute creative freedom. You must NEVER default to a standard dark-purple or uniform look. Every single application you style must possess an entirely unique visual soul tailored to its specific industry, purpose, and target audience. You will independently determine whether the app should use Light Mode, Dark Mode, or a Hybrid layout, and you will choose a completely custom color spectrum from scratch.

Follow this execution pipeline to process and rewrite the application files:

### STEP 1: INDEPENDENT COSMIC DESIGN ANALYSIS
Analyze the incoming code to discover the purpose, utility, and target user of the app. 
Based strictly on your analysis, autonomously invent a custom design system for this specific generation. You must independently choose:
1. The Core Mode: (Pure Light Mode, Deep Dark Mode, or High-contrast Hybrid).
2. The Hue Spectrum: Select a distinct primary anchor hue, secondary accent hue, and supporting neutral base canvas out of the entire Tailwind color universe. Ensure these selections vary wildly from app to app.

### STEP 2: ESTABLISH YOUR AUTONOMOUS TOKEN MAP
Before modifying any files, mentally build a strict, cohesive token system using your chosen palette colors and weights. You will dynamically assign your chosen colors across these exact layers:
- Page Canvas Background (The overall app background layer)
- Header / Navbar / Navigation Panels (Must contrast cleanly with the page canvas)
- Surface Cards & Content Containers (Elevated areas with distinct backgrounds, shadow depths, and micro-borders)
- Text Hierarchy (High-contrast primary foreground text, distinct secondary/muted body text)
- Form Elements (Input field fills, active/focus border glows, and structural text labels)
- Action Buttons (Distinct rules for: Primary call-to-action, Secondary actions, and Destructive operations)
- Semantic Badges (Custom color pairings for Success, Warning, Error, and Info states that align with your overall theme)

### STEP 3: APPLY STRUCTURAL LAYOUT PARADIGMS
Identify the file type or view and map it to a professional layout framework:
- Auth / Gateway Pages: Create high-polish entry screens using either a beautifully weighted single-card focus layout or a dynamic split-screen layout (one side handling clean, spacious inputs; the other side showcasing a bold, expressive brand presentation block).
- Dashboard / Management Pages: Structure with clean workspace tracking (e.g., sticky navigation sidebars, persistent header utility bars, and responsive content grids using `grid grid-cols-1 md:grid-cols-3 gap-6` to lay out metric cards and comprehensive data tables).
- Detail / Form Pages: Implement structured asymmetric workspaces (e.g., a multi-column view where primary form workflows take up the main width, while metadata, contextual actions, and validation status streams sit inside an independent lateral panel).

### STEP 4: INJECT MICRO-INTERACTIONS & MOTION POLISH
Make the user interface feel alive, tactile, and highly responsive to user feedback:
- Button Click Actions: Add explicit physical click-down feedback on every clickable element using scaling states (e.g., `active:scale-[0.98] transition-all duration-200`).
- Card Focus States: Elevate and shift component surfaces when cursors pass over them (e.g., structural hover translations, smooth shadow transitions, or subtle border color shifts).
- Compound Nesting Focus: Utilize Tailwind’s parent-child interaction utilities (`group` applied to structural containers paired with `group-hover:` modifiers on child elements) to drive elegant contextual reactions, such as making an inner chevron slide outward or revealing secondary controls.
- Skeleton Loading States: Build structural pulse blocks matching the exact contours of the component layout (`animate-pulse` blocks matching card/avatar geometry) rather than generic bars.
- Empty State Handlers: Design delightful, contextual empty views when content arrays are unpopulated. Combine a highly relevant icon component, an explicit bold header, a helpful descriptive explanation string, and an actionable primary button.

### STEP 5: ICONOGRAPHY, TYPOGRAPHY, & ACCESSIBILITY
- Maintain unified scaling constraints for all visual icons (ensure consistent bounding layouts and stroke weighting).
- Enforce a strict typographic scale using precise weight tracking (`font-bold tracking-tight text-xl` vs `text-sm font-normal`).
- Guard color contrast fiercely. Ensure text elements are completely legible against whatever background canvas or button hue you have autonomously chosen.


## OUTPUT FORMAT

Return exactly this JSON structure:
{{"files": [{{"path": "src/App.tsx", "content": "...complete file with escaped newlines and quotes..."}}]}}

- Include ALL files you received — enhance every single one.
- File content must be the **complete file** — never truncated, never `// ... rest unchanged`.
- Every file must feel like it belongs to the same app.

---

## THE FILES TO ENHANCE:

{json.dumps(files, indent=2)}

Analyze the app's purpose, decide on ONE design system, then apply it consistently to ALL {len(files)} files. Output only the JSON.
"""

    # ------------------------------------------------------------------
    # Response parsing
    # ------------------------------------------------------------------

    def _parse_response(self, raw_content) -> list:
        """Extract and parse JSON from the model's response."""
        # Handle list responses from reasoning models
        if isinstance(raw_content, list):
            raw_content = next(
                (block.get("text", "")
                 for block in raw_content
                 if isinstance(block, dict) and block.get("type") == "text"),
                ""
            )

        if not raw_content:
            logger.error("Empty response content")
            return []

        match = re.search(r'({[\s\S]*})', raw_content, re.DOTALL)
        if not match:
            logger.error("No JSON object found in UI/UX response")
            return []
        json_str = match.group(1)

        try:
            data = json.loads(json_str)
            return data.get("files", [])
        except json.JSONDecodeError as e:
            logger.warning(f"Standard JSON parsing failed: {e}. Trying json5...")
            if HAS_JSON5:
                try:
                    data = json5.loads(json_str)
                    return data.get("files", [])
                except Exception as e2:
                    logger.error(f"json5 also failed: {e2}")
            else:
                logger.error("json5 not installed — run `pip install json5`.")
            return []