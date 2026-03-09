
# ─────────────────────────────────────────────────────────────────────────────
# Proxy service — makes authenticated requests to the user's Supabase project.
# The service_role_key is stored in our DB and NEVER sent to the frontend.
# Supports: Overview, Database (CRUD), SQL Editor, Users, Storage,
#           Logs, Edge Functions, Secrets.
# ─────────────────────────────────────────────────────────────────────────────

import requests
from typing import Any, Dict, List, Optional
from uuid import UUID

from supabase_client import supabase as db_client
from utils.logger import Logger

logger = Logger(__name__)

MGMT_BASE         = "https://api.supabase.com/v1"
REST_BASE         = "https://{ref}.supabase.co/rest/v1"
AUTH_ADMIN_BASE   = "https://{ref}.supabase.co/auth/v1/admin"
STORAGE_BASE      = "https://{ref}.supabase.co/storage/v1"
FUNCTIONS_BASE    = "https://{ref}.supabase.co/functions/v1"

# Log source table map — used by get_logs()
LOG_TABLE_MAP = {
    "api":       "edge_logs",
    "auth":      "auth_logs",
    "storage":   "storage_logs",
    "realtime":  "realtime_logs",
    "postgrest": "postgres_logs",
}


class SupabaseProxyService:

    # ── Private helpers ───────────────────────────────────────────────────────

    def _creds(self, project_id: str, user_id: str) -> Dict[str, str]:
        project = db_client.get_project(UUID(project_id), user_id)
        if not project:
            raise ValueError(f"Project {project_id} not found or access denied")
        ref = project.get("supabase_ref")
        key = project.get("supabase_service_key")
        if not ref:
            raise ValueError("No Supabase backend attached. Only Class B apps have a Cloud tab.")
        if not key:
            raise ValueError("No service-role key stored. Re-deploy the app to refresh credentials.")
        return {"ref": ref, "key": key}

    def _svc_h(self, key: str) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {key}",
            "apikey": key,
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    def _mgmt_h(self) -> Dict[str, str]:
        from config import Config
        token = Config.SUPABASE_ACCESS_TOKEN
        if not token:
            raise ValueError("SUPABASE_ACCESS_TOKEN not configured on this server.")
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    def _rest(self, ref: str, path: str) -> str:
        return f"{REST_BASE.format(ref=ref)}/{path.lstrip('/')}"

    def _auth(self, ref: str, path: str) -> str:
        return f"{AUTH_ADMIN_BASE.format(ref=ref)}/{path.lstrip('/')}"

    def _stor(self, ref: str, path: str) -> str:
        return f"{STORAGE_BASE.format(ref=ref)}/{path.lstrip('/')}"

    # ── Overview ──────────────────────────────────────────────────────────────

    def get_overview(self, project_id: str, user_id: str) -> Dict:
        c = self._creds(project_id, user_id)
        ref, key = c["ref"], c["key"]

        def _safe(fn):
            try: return fn()
            except Exception: return 0

        table_count = _safe(lambda: len([
            p for p in requests.get(
                self._rest(ref, ""), headers=self._svc_h(key), timeout=8
            ).json().get("paths", {})
            if not p.lstrip("/").startswith("rpc/") and p.lstrip("/")
        ]))

        user_count = _safe(lambda: (
            requests.get(
                self._auth(ref, "users"), headers=self._svc_h(key),
                params={"page": 1, "per_page": 1}, timeout=8
            ).json().get("total", 0)
        ))

        bucket_count = _safe(lambda: len(
            requests.get(self._stor(ref, "bucket"), headers=self._svc_h(key), timeout=8).json()
        ))

        fn_count = _safe(lambda: len(
            requests.get(f"{MGMT_BASE}/projects/{ref}/functions", headers=self._mgmt_h(), timeout=8).json()
        ))

        return {
            "ref": ref,
            "supabase_url": f"https://{ref}.supabase.co",
            "table_count": table_count,
            "user_count": user_count,
            "bucket_count": bucket_count,
            "function_count": fn_count,
        }

    # ── Database ──────────────────────────────────────────────────────────────

    def list_tables(self, project_id: str, user_id: str) -> List[Dict]:
        c = self._creds(project_id, user_id)
        resp = requests.get(self._rest(c["ref"], ""), headers=self._svc_h(c["key"]), timeout=15)
        resp.raise_for_status()
        tables = []
        for path, methods in resp.json().get("paths", {}).items():
            name = path.lstrip("/")
            if not name or name.startswith("rpc/"):
                continue
            params = methods.get("get", {}).get("parameters", [])
            cols = [p["name"] for p in params if p.get("in") == "query"
                    and p["name"] not in ("select", "order", "offset", "limit")]
            tables.append({"name": name, "columns": cols})
        return tables

    def get_table_rows(self, project_id: str, user_id: str, table: str, limit=100, offset=0) -> List[Dict]:
        c = self._creds(project_id, user_id)
        h = {**self._svc_h(c["key"]), "Prefer": "count=exact"}
        resp = requests.get(self._rest(c["ref"], table), headers=h, params={"limit": limit, "offset": offset}, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def insert_row(self, project_id: str, user_id: str, table: str, row: Dict) -> Dict:
        c = self._creds(project_id, user_id)
        resp = requests.post(self._rest(c["ref"], table), json=row, headers=self._svc_h(c["key"]), timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return data[0] if isinstance(data, list) else data

    def update_row(self, project_id: str, user_id: str, table: str, row_id: str, updates: Dict) -> Dict:
        c = self._creds(project_id, user_id)
        resp = requests.patch(
            self._rest(c["ref"], table), json=updates, headers=self._svc_h(c["key"]),
            params={"id": f"eq.{row_id}"}, timeout=15
        )
        resp.raise_for_status()
        data = resp.json()
        return data[0] if isinstance(data, list) and data else updates

    def delete_row(self, project_id: str, user_id: str, table: str, row_id: str) -> bool:
        c = self._creds(project_id, user_id)
        requests.delete(
            self._rest(c["ref"], table), headers=self._svc_h(c["key"]),
            params={"id": f"eq.{row_id}"}, timeout=15
        ).raise_for_status()
        return True

    # ── SQL Editor ────────────────────────────────────────────────────────────

    def execute_sql(self, project_id: str, user_id: str, sql: str) -> Dict:
        c = self._creds(project_id, user_id)
        url = f"{MGMT_BASE}/projects/{c['ref']}/database/query"
        resp = requests.post(url, json={"query": sql}, headers=self._mgmt_h(), timeout=30)
        if not resp.ok:
            msg = resp.text
            try: msg = resp.json().get("message", msg)
            except Exception: pass
            return {"rows": [], "columns": [], "error": msg, "row_count": 0}
        data = resp.json()
        rows = data if isinstance(data, list) else data.get("rows", [])
        cols = list(rows[0].keys()) if rows else []
        return {"rows": rows, "columns": cols, "error": None, "row_count": len(rows)}

    # ── Auth Users ────────────────────────────────────────────────────────────

    def list_users(self, project_id: str, user_id: str, page=1, per_page=50) -> Dict:
        c = self._creds(project_id, user_id)
        resp = requests.get(
            self._auth(c["ref"], "users"), headers=self._svc_h(c["key"]),
            params={"page": page, "per_page": per_page}, timeout=15
        )
        resp.raise_for_status()
        data = resp.json()
        users = data.get("users", data if isinstance(data, list) else [])
        return {"users": users, "total": data.get("total", len(users)), "page": page, "per_page": per_page}

    def delete_user(self, project_id: str, caller_id: str, target_uid: str) -> bool:
        c = self._creds(project_id, caller_id)
        requests.delete(self._auth(c["ref"], f"users/{target_uid}"), headers=self._svc_h(c["key"]), timeout=15).raise_for_status()
        return True

    # ── Storage ───────────────────────────────────────────────────────────────

    def list_buckets(self, project_id: str, user_id: str) -> List[Dict]:
        c = self._creds(project_id, user_id)
        resp = requests.get(self._stor(c["ref"], "bucket"), headers=self._svc_h(c["key"]), timeout=15)
        resp.raise_for_status()
        return resp.json()

    def list_files(self, project_id: str, user_id: str, bucket: str, prefix: str = "") -> List[Dict]:
        c = self._creds(project_id, user_id)
        url = self._stor(c["ref"], f"object/list/{bucket}")
        payload = {"prefix": prefix, "limit": 200, "offset": 0, "sortBy": {"column": "name", "order": "asc"}}
        resp = requests.post(url, json=payload, headers=self._svc_h(c["key"]), timeout=15)
        resp.raise_for_status()
        return resp.json()

    def get_signed_url(self, project_id: str, user_id: str, bucket: str, path: str) -> str:
        c = self._creds(project_id, user_id)
        url = self._stor(c["ref"], f"object/sign/{bucket}/{path}")
        resp = requests.post(url, json={"expiresIn": 3600}, headers=self._svc_h(c["key"]), timeout=15)
        resp.raise_for_status()
        signed = resp.json().get("signedURL", "")
        if signed.startswith("/"):
            signed = f"https://{c['ref']}.supabase.co/storage/v1{signed}"
        return signed

    def delete_file(self, project_id: str, user_id: str, bucket: str, path: str) -> bool:
        c = self._creds(project_id, user_id)
        requests.delete(self._stor(c["ref"], f"object/{bucket}/{path}"), headers=self._svc_h(c["key"]), timeout=15).raise_for_status()
        return True

    # ── Logs ─────────────────────────────────────────────────────────────────
    # FIXED: Supabase analytics endpoint requires ?sql=SELECT...FROM {table}
    # NOT ?project=&limit=&type= (that was the old broken format)

    def get_logs(self, project_id: str, user_id: str, log_type: str = "api", limit: int = 100) -> List[Dict]:
        c = self._creds(project_id, user_id)
        table = LOG_TABLE_MAP.get(log_type, "edge_logs")
        sql = f"SELECT timestamp, event_message FROM {table} ORDER BY timestamp DESC LIMIT {limit}"
        url = f"{MGMT_BASE}/projects/{c['ref']}/analytics/endpoints/logs.all"
        resp = requests.get(url, headers=self._mgmt_h(), params={"sql": sql}, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        return data.get("result", data if isinstance(data, list) else [])

    # ── Edge Functions ────────────────────────────────────────────────────────

    def list_functions(self, project_id: str, user_id: str) -> List[Dict]:
        c = self._creds(project_id, user_id)
        resp = requests.get(f"{MGMT_BASE}/projects/{c['ref']}/functions", headers=self._mgmt_h(), timeout=15)
        resp.raise_for_status()
        return resp.json()

    def invoke_function(self, project_id: str, user_id: str, fn_name: str, payload: Dict) -> Dict:
        c = self._creds(project_id, user_id)
        url = f"{FUNCTIONS_BASE.format(ref=c['ref'])}/{fn_name}"
        resp = requests.post(url, json=payload, headers=self._svc_h(c["key"]), timeout=30)
        try: result = resp.json()
        except Exception: result = {"raw": resp.text}
        return {"status": resp.status_code, "ok": resp.ok, "data": result}

    # ── Secrets ──────────────────────────────────────────────────────────────

    def list_secrets(self, project_id: str, user_id: str) -> List[Dict]:
        c = self._creds(project_id, user_id)
        resp = requests.get(f"{MGMT_BASE}/projects/{c['ref']}/secrets", headers=self._mgmt_h(), timeout=15)
        resp.raise_for_status()
        return resp.json()

    def upsert_secret(self, project_id: str, user_id: str, name: str, value: str) -> bool:
        c = self._creds(project_id, user_id)
        requests.post(
            f"{MGMT_BASE}/projects/{c['ref']}/secrets",
            json=[{"name": name, "value": value}],
            headers=self._mgmt_h(), timeout=15
        ).raise_for_status()
        return True

    def delete_secret(self, project_id: str, user_id: str, name: str) -> bool:
        c = self._creds(project_id, user_id)
        requests.delete(
            f"{MGMT_BASE}/projects/{c['ref']}/secrets",
            json=[name],
            headers=self._mgmt_h(), timeout=15
        ).raise_for_status()
        return True


supabase_proxy = SupabaseProxyService()