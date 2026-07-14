

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # Models per agent
    CLASSIFIER_MODEL = os.getenv("CLASSIFIER_MODEL", "gpt-4o-mini")
    PLANNER_MODEL    = os.getenv("PLANNER_MODEL",    "gpt-4o-mini")
    CRITIC_MODEL     = os.getenv("CRITIC_MODEL",     "gpt-4o")
    CODER_MODEL      = os.getenv("CODER_MODEL",      "gpt-4o")

    # Supabase (your own DB — used by the API)
    SUPABASE_URL              = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    SUPABASE_ANON_KEY         = os.getenv("SUPABASE_ANON_KEY")

    # GitHub
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

    # App settings
    MAX_ITERATIONS     = int(os.getenv("MAX_ITERATIONS", "8"))
    WORKFLOW_TIMEOUT   = int(os.getenv("WORKFLOW_TIMEOUT", "18000000000000"))
    DEPLOYMENT_TIMEOUT = int(os.getenv("DEPLOYMENT_TIMEOUT", "300000000"))

    # Vercel (replaces Netlify for both Class A and Class B)
    VERCEL_TOKEN = os.getenv("VERCEL_TOKEN")

    # Anthropic
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    UIUX_MODEL        = os.getenv("UIUX_MODEL", "claude-sonnet-4-6")

    # Supabase Management API (for creating user Supabase projects — Class B)
    SUPABASE_ACCESS_TOKEN = os.getenv("SUPABASE_ACCESS_TOKEN")
    SUPABASE_ORG_ID       = os.getenv("SUPABASE_ORG_ID")

    @classmethod
    def validate(cls):
        missing = []
        if not cls.SUPABASE_URL:
            missing.append("SUPABASE_URL")
        if not cls.SUPABASE_SERVICE_ROLE_KEY:
            missing.append("SUPABASE_SERVICE_ROLE_KEY")
        if not cls.OPENAI_API_KEY:
            missing.append("OPENAI_API_KEY")
        if not cls.ANTHROPIC_API_KEY:
            missing.append("ANTHROPIC_API_KEY")
        if not cls.VERCEL_TOKEN:
            missing.append("VERCEL_TOKEN")
        if missing:
            raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")