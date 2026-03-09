# apps/api/endpoints/cloud.py
# ─────────────────────────────────────────────────────────────────────────────
# Cloud tab backend — all 9 sections:
# Overview · Database (CRUD) · SQL Editor · Users · Storage · Logs ·
# Edge Functions · AI · Secrets
#
# Routes prefix: /api/v1/cloud/{project_id}/...
# ─────────────────────────────────────────────────────────────────────────────

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from supabase_client import supabase as db_client
from services.supabase_proxy import supabase_proxy
from utils.logger import Logger

logger = Logger(__name__)
router = APIRouter(prefix="/cloud", tags=["cloud"])
security = HTTPBearer()


# ── Auth dependency ───────────────────────────────────────────────────────────

async def get_current_user(creds: HTTPAuthorizationCredentials = Depends(security)):
    user = db_client.verify_token(creds.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return user


# ── Error helper ──────────────────────────────────────────────────────────────

def _err(e: Exception) -> HTTPException:
    msg = str(e)
    if "not found" in msg.lower() or "access denied" in msg.lower():
        return HTTPException(404, msg)
    if "no supabase" in msg.lower() or "no service" in msg.lower() or "class b" in msg.lower():
        return HTTPException(400, msg)
    logger.error(f"Cloud proxy error: {msg}")
    return HTTPException(500, msg)


# ── Request bodies ────────────────────────────────────────────────────────────

class RowBody(BaseModel):
    data: Dict[str, Any]

class SqlBody(BaseModel):
    sql: str

class InvokeBody(BaseModel):
    payload: Dict[str, Any] = {}

class SecretBody(BaseModel):
    name: str
    value: str


# ─────────────────────────────────────────────────────────────────────────────
# 1. OVERVIEW
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{project_id}/overview")
async def get_overview(project_id: str, user=Depends(get_current_user)):
    """Aggregate stats: tables, users, buckets, functions."""
    try:
        return supabase_proxy.get_overview(project_id, user.id)
    except Exception as e:
        raise _err(e)


# ─────────────────────────────────────────────────────────────────────────────
# 2. DATABASE (CRUD)
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{project_id}/tables")
async def list_tables(project_id: str, user=Depends(get_current_user)):
    try:
        return {"tables": supabase_proxy.list_tables(project_id, user.id)}
    except Exception as e:
        raise _err(e)


@router.get("/{project_id}/tables/{table}/rows")
async def get_rows(
    project_id: str, table: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    user=Depends(get_current_user),
):
    try:
        rows = supabase_proxy.get_table_rows(project_id, user.id, table, limit, offset)
        return {"rows": rows, "table": table, "limit": limit, "offset": offset}
    except Exception as e:
        raise _err(e)


@router.post("/{project_id}/tables/{table}/rows")
async def insert_row(project_id: str, table: str, body: RowBody, user=Depends(get_current_user)):
    try:
        return {"row": supabase_proxy.insert_row(project_id, user.id, table, body.data)}
    except Exception as e:
        raise _err(e)


@router.patch("/{project_id}/tables/{table}/rows/{row_id}")
async def update_row(project_id: str, table: str, row_id: str, body: RowBody, user=Depends(get_current_user)):
    try:
        return {"row": supabase_proxy.update_row(project_id, user.id, table, row_id, body.data)}
    except Exception as e:
        raise _err(e)


@router.delete("/{project_id}/tables/{table}/rows/{row_id}")
async def delete_row(project_id: str, table: str, row_id: str, user=Depends(get_current_user)):
    try:
        supabase_proxy.delete_row(project_id, user.id, table, row_id)
        return {"success": True}
    except Exception as e:
        raise _err(e)


# ─────────────────────────────────────────────────────────────────────────────
# 3. SQL EDITOR
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/{project_id}/sql")
async def run_sql(project_id: str, body: SqlBody, user=Depends(get_current_user)):
    """Execute raw SQL. Returns {rows, columns, error, row_count}."""
    try:
        return supabase_proxy.execute_sql(project_id, user.id, body.sql)
    except Exception as e:
        raise _err(e)


# ─────────────────────────────────────────────────────────────────────────────
# 4. USERS
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{project_id}/users")
async def list_users(
    project_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    user=Depends(get_current_user),
):
    try:
        return supabase_proxy.list_users(project_id, user.id, page, per_page)
    except Exception as e:
        raise _err(e)


@router.delete("/{project_id}/users/{target_uid}")
async def delete_user(project_id: str, target_uid: str, user=Depends(get_current_user)):
    try:
        supabase_proxy.delete_user(project_id, user.id, target_uid)
        return {"success": True}
    except Exception as e:
        raise _err(e)


# ─────────────────────────────────────────────────────────────────────────────
# 5. STORAGE
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{project_id}/storage/buckets")
async def list_buckets(project_id: str, user=Depends(get_current_user)):
    try:
        return {"buckets": supabase_proxy.list_buckets(project_id, user.id)}
    except Exception as e:
        raise _err(e)


@router.get("/{project_id}/storage/{bucket}/files")
async def list_files(
    project_id: str, bucket: str,
    prefix: str = Query(""),
    user=Depends(get_current_user),
):
    try:
        return {"files": supabase_proxy.list_files(project_id, user.id, bucket, prefix)}
    except Exception as e:
        raise _err(e)


@router.get("/{project_id}/storage/{bucket}/sign")
async def get_signed_url(
    project_id: str, bucket: str,
    path: str = Query(...),
    user=Depends(get_current_user),
):
    try:
        url = supabase_proxy.get_signed_url(project_id, user.id, bucket, path)
        return {"url": url}
    except Exception as e:
        raise _err(e)


@router.delete("/{project_id}/storage/{bucket}/files")
async def delete_file(
    project_id: str, bucket: str,
    path: str = Query(...),
    user=Depends(get_current_user),
):
    try:
        supabase_proxy.delete_file(project_id, user.id, bucket, path)
        return {"success": True}
    except Exception as e:
        raise _err(e)


# ─────────────────────────────────────────────────────────────────────────────
# 6. LOGS
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{project_id}/logs")
async def get_logs(
    project_id: str,
    log_type: str = Query("api"),
    limit: int = Query(100, ge=1, le=500),
    user=Depends(get_current_user),
):
    try:
        logs = supabase_proxy.get_logs(project_id, user.id, log_type, limit)
        return {"logs": logs, "log_type": log_type}
    except Exception as e:
        raise _err(e)


# ─────────────────────────────────────────────────────────────────────────────
# 7. EDGE FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{project_id}/functions")
async def list_functions(project_id: str, user=Depends(get_current_user)):
    try:
        return {"functions": supabase_proxy.list_functions(project_id, user.id)}
    except Exception as e:
        raise _err(e)


@router.post("/{project_id}/functions/{fn_name}/invoke")
async def invoke_function(project_id: str, fn_name: str, body: InvokeBody, user=Depends(get_current_user)):
    try:
        return supabase_proxy.invoke_function(project_id, user.id, fn_name, body.payload)
    except Exception as e:
        raise _err(e)


# ─────────────────────────────────────────────────────────────────────────────
# 8. SECRETS
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{project_id}/secrets")
async def list_secrets(project_id: str, user=Depends(get_current_user)):
    try:
        secrets = supabase_proxy.list_secrets(project_id, user.id)
        # Mask values — names shown, values redacted for security
        masked = [{"name": s.get("name", ""), "value": "••••••••"} for s in secrets]
        return {"secrets": masked}
    except Exception as e:
        raise _err(e)


@router.post("/{project_id}/secrets")
async def upsert_secret(project_id: str, body: SecretBody, user=Depends(get_current_user)):
    try:
        supabase_proxy.upsert_secret(project_id, user.id, body.name, body.value)
        return {"success": True}
    except Exception as e:
        raise _err(e)


@router.delete("/{project_id}/secrets/{secret_name}")
async def delete_secret(project_id: str, secret_name: str, user=Depends(get_current_user)):
    try:
        supabase_proxy.delete_secret(project_id, user.id, secret_name)
        return {"success": True}
    except Exception as e:
        raise _err(e)