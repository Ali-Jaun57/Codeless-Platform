



import json
import re
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, AIMessage
from utils.logger import Logger
from ..shared.agent_state import AgentState

# Optional json5 for lenient parsing
try:
    import json5
    HAS_JSON5 = True
except ImportError:
    HAS_JSON5 = False
    json5 = None

logger = Logger(__name__)

class UIUXAgent:
    def __init__(self, llm: ChatAnthropic):
        self.llm = llm
        logger.step("Class A UI/UX Agent", "initialized")

    def __call__(self, state: AgentState) -> dict:
        logger.step("UI/UX", "started (enhancement)")

        if not state.files:
            logger.warning("⚠️ No files to enhance")
            return {"files": state.files, "messages": state.messages}

        # Build a description of the files (paths and current content)
        files_for_prompt = []
        for f in state.files:
            files_for_prompt.append({
                "path": f["path"],
                "content": f["content"]
            })

        prompt = self._create_prompt(files_for_prompt)

        logger.debug("Calling Claude Opus for UI/UX enhancement...")
        # response = self.llm.invoke(state.messages + [HumanMessage(content=prompt)])
        # Sanitize messages — strip OpenAI reasoning blocks before sending to Claude
        clean_messages = []
        for msg in state.messages:
            if isinstance(msg, AIMessage) and isinstance(msg.content, list):
                # Extract only text blocks, discard reasoning/thinking blocks
                text_only = " ".join(
                    block.get("text", "")
                    for block in msg.content
                    if isinstance(block, dict) and block.get("type") == "text"
                ).strip()
                if text_only:
                    clean_messages.append(AIMessage(content=text_only))
                # If no text found, skip the message entirely
            else:
                clean_messages.append(msg)

        response = self.llm.invoke(clean_messages + [HumanMessage(content=prompt)])

        logger.success("✅ UI/UX enhancement response received")

        enhanced_files = self._parse_response(response.content)

        # Merge: keep files that were not modified (if any missing from response)
        file_dict = {f["path"]: f for f in state.files}
        for f in enhanced_files:
            file_dict[f["path"]] = f   # overwrite with enhanced version
        final_files = list(file_dict.values())

        logger.info(f"🎨 UI/UX enhanced {len(enhanced_files)} files")

        new_messages = state.messages + [AIMessage(content=response.content)]
        return {
            "files": final_files,
            "messages": new_messages
        }

    def _create_prompt(self, files: list) -> str:
        return f"""You are a senior product designer and frontend engineer who has shipped interfaces at companies like Linear, Vercel, Stripe, and Notion. You have deep expertise in design systems, micro-interactions, and converting Figma-quality mockups into pixel-perfect React + Tailwind code.

Your sole mission: **transform the provided app into a visually stunning, modern, production-ready UI** without touching any logic, state, or functionality.

---

## HARD CONSTRAINTS — NEVER VIOLATE THESE

- Do NOT modify any function, hook, event handler, API call, state variable, prop name, or business logic.
- Do NOT remove any imports that are used in logic.
- Do NOT change routing, data flow, or component responsibilities.
- Do NOT introduce new dependencies (no new npm packages). Use only Tailwind CSS, inline SVGs, and CSS custom properties.
- **Output JSON must be valid and complete**:
  - Every file's `content` must be a **valid JSON string**.
  - Escape all double quotes inside the code as `\"`.
  - Replace every actual newline with the two characters `\n` (backslash + n).
  - Do **not** put raw newlines inside the string.
  - Ensure the JSON object is **complete** – do not truncate.
- Output ONLY a single valid JSON object — no markdown fences, no commentary, no explanation.

---

## DESIGN SYSTEM YOU MUST APPLY

### Color Palette
- Use a cohesive palette with a clear **primary**, **surface**, **background**, and **accent** color.
- Prefer modern palettes: deep navy + electric indigo, slate + violet, zinc + emerald, or neutral + amber.
- Use Tailwind's `slate`, `zinc`, `neutral` for backgrounds/surfaces — avoid plain `white`/`gray`.
- Text hierarchy: primary text `slate-900` (dark mode: `slate-50`), secondary `slate-500`, muted `slate-400`.
- Always support **dark mode** using Tailwind's `dark:` variant. Default to dark if the app has no existing theme toggle.

### Typography
- Font scale: use `text-xs` through `text-4xl` intentionally. Headings should be bold (`font-bold` or `font-semibold`), body `font-normal`, captions `text-sm text-slate-500`.
- Use `tracking-tight` on headings, `leading-relaxed` on body text.
- Add `font-mono` to any code, IDs, timestamps, or technical strings.

### Spacing & Layout
- Use consistent spacing rhythm: prefer multiples of 4 (`p-4`, `gap-4`, `space-y-6`).
- Cards: `rounded-xl` with `shadow-sm` border `border border-slate-200 dark:border-slate-700/60`.
- Page layouts: max-width containers (`max-w-6xl mx-auto px-4 sm:px-6 lg:px-8`), never full-bleed content.
- Sidebars: `w-64`, collapsible on mobile with smooth transition.
- Use CSS Grid for dashboard-style layouts, Flexbox for component internals.

### Components & Patterns
Apply these to every relevant element found in the code:

**Buttons:**
- Primary: `bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 text-white font-medium px-4 py-2 rounded-lg transition-all duration-150 shadow-sm hover:shadow-md`
- Secondary: `bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 ...`
- Destructive: `bg-red-500/10 hover:bg-red-500/20 text-red-600 dark:text-red-400 ...`
- Disabled state: `opacity-50 cursor-not-allowed`
- Loading state: add a subtle spinner SVG inline

**Inputs & Forms:**
- `bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/40 focus:border-indigo-500 transition-all`
- Labels: `text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5 block`
- Error states: `border-red-400 focus:ring-red-400/40` + error message in `text-red-500 text-xs mt-1`
- Group related inputs with `space-y-4` inside a `<form>` with `p-6 rounded-xl border ...`

**Cards:**
- `bg-white dark:bg-slate-800/50 rounded-xl border border-slate-200 dark:border-slate-700/60 shadow-sm hover:shadow-md transition-shadow duration-200 p-6`
- Use `backdrop-blur-sm` on modal overlays and floating elements

**Tables:**
- Striped rows: `even:bg-slate-50 dark:even:bg-slate-800/30`
- Sticky header: `sticky top-0 bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm`
- Cell padding: `px-4 py-3`, header: `text-xs font-semibold uppercase tracking-wider text-slate-500`

**Navigation:**
- Active link: `bg-indigo-50 dark:bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 font-medium`
- Inactive: `text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800`
- Use icons (inline SVGs, 16-20px) alongside nav labels

**Badges/Chips:**
- Success: `bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400`
- Warning: `bg-amber-50 text-amber-700 ...`
- Error: `bg-red-50 text-red-700 ...`
- Info: `bg-blue-50 text-blue-700 ...`
- All: `text-xs font-medium px-2.5 py-0.5 rounded-full`

**Empty States:**
- Centered illustration area (use a simple inline SVG icon), bold title, muted description, primary CTA button
- `flex flex-col items-center justify-center py-16 text-center`

**Loading States:**
- Skeleton screens using `animate-pulse bg-slate-200 dark:bg-slate-700 rounded`
- Replace any plain "Loading..." text with skeleton placeholders

### Micro-interactions & Animations
Add these using Tailwind's `transition` utilities:
- All interactive elements: `transition-all duration-150 ease-in-out`
- Cards on hover: `hover:-translate-y-0.5 hover:shadow-lg`
- Buttons on click: `active:scale-95`
- Modals/drawers: `transition-opacity duration-200` + `transition-transform duration-300`
- Add `group` + `group-hover:` for parent-triggered child animations (e.g., arrow icons)

### Iconography
- Use inline SVG icons throughout (heroicons style, 20x20 viewBox).
- Add icons to: buttons (left of label), nav items, empty states, alert/toast messages, input prefixes/suffixes.
- Keep icons `w-4 h-4` or `w-5 h-5`, `stroke-current`, `stroke-2`, `fill-none`.

### Accessibility
- All interactive elements must have `focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2`
- Add `aria-label` to icon-only buttons
- Use semantic HTML: `<nav>`, `<main>`, `<header>`, `<section>`, `<article>` appropriately
- Ensure color contrast meets WCAG AA

---

## LAYOUT PATTERNS — APPLY THE MOST APPROPRIATE ONE

- **Dashboard:** Sidebar (fixed, `w-64`) + main content area with top navbar + grid of stat cards + data table/chart area
- **Landing/Auth page:** Centered card with logo, full-height split layout or glassmorphism card on gradient background
- **CRUD list view:** Top bar with search+filter+CTA, data table or card grid, pagination
- **Detail/Edit page:** Two-column layout (form left, preview/summary right) or single-column with sticky action bar

---

## OUTPUT FORMAT

Return exactly this JSON structure:
{{"files": [{{"path": "src/App.jsx", "content": "...full file content with escaped newlines and quotes..."}}, ...]}}

- Include every file you modified.
- Omit files you did not touch.
- File content must be the complete file — never truncated, never use `// ... rest unchanged`.

---

## THE FILES TO ENHANCE:

{json.dumps(files, indent=2)}

Analyze the app's purpose and structure, then apply every applicable rule above to produce a stunning, cohesive, production-quality UI. Output only the JSON."""

    def _parse_response(self, raw_content: str) -> list:
        """Extract and parse JSON from Claude's response, with fallback to json5."""
        # First, extract the raw JSON string using regex
        match = re.search(r'({[\s\S]*})', raw_content, re.DOTALL)
        if not match:
            logger.error("No JSON object found in response")
            return []
        json_str = match.group(1)

        # Try standard JSON parsing
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
                logger.error("json5 not installed. Please install with `pip install json5`.")
            return []