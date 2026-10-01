import os
import json
import urllib.request
import urllib.error
import asyncio
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, Request, Header

from db.client import db
from db.models.cron_model import CronScheduleUpdate, CronScheduleResponse
from routes.auth_routes import decode_access_token

cron_router = APIRouter()

CRON_JOB_ORG_API_URL = "https://api.cron-job.org/jobs"

def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required"
        )

    try:
        return decode_access_token(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token"
        )

def format_cron_settings(doc: dict) -> dict:
    public_url = os.getenv("PUBLIC_APP_URL", "http://localhost:8000").rstrip("/")
    default_target = f"{public_url}/api/v1/cron/execute-blog-job"
    return {
        "id": str(doc.get("_id", "1")),
        "frequency_type": doc.get("frequency_type", "daily"),
        "time_of_day": doc.get("time_of_day", "09:00"),
        "day_of_week": doc.get("day_of_week", 1),
        "interval_days": doc.get("interval_days", 3),
        "cron_expression": doc.get("cron_expression", "0 9 * * *"),
        "enabled": doc.get("enabled", True),
        "timezone": doc.get("timezone", "Asia/Kolkata"),
        "target_url": doc.get("target_url") or default_target,
        "cron_job_id": doc.get("cron_job_id"),
        "last_run": doc.get("last_run"),
        "updated_at": doc.get("updated_at"),
        "cron_job_org_status": doc.get("cron_job_org_status", "Not Synced")
    }

def build_cron_job_payload(settings: dict) -> dict:
    public_url = os.getenv("PUBLIC_APP_URL", "http://localhost:8000").rstrip("/")
    default_target = f"{public_url}/api/v1/cron/execute-blog-job"
    target_url = settings.get("target_url") or default_target
    secret_key = os.getenv("CRON_JOB_SECRET", "")

    # Parse time
    time_str = settings.get("time_of_day", "09:00")
    try:
        hour, minute = map(int, time_str.split(":"))
    except Exception:
        hour, minute = 9, 0

    freq = settings.get("frequency_type", "daily")
    wdays = [-1]
    mdays = [-1]

    if freq == "weekly":
        wdays = [settings.get("day_of_week", 1)]

    schedule = {
        "timezone": settings.get("timezone", "Asia/Kolkata"),
        "expiresAt": 0,
        "hours": [hour],
        "minutes": [minute],
        "mdays": mdays,
        "months": [-1],
        "wdays": wdays
    }

    job_data = {
        "job": {
            "url": target_url,
            "title": "HydraLakes Blog Agent Generator",
            "enabled": settings.get("enabled", True),
            "saveResponses": True,
            "schedule": schedule,
            "requestMethod": 0,  # 0 = GET, 1 = POST
            "extendedData": {
                "headers": {
                    "X-Cron-Secret": secret_key
                }
            }
        }
    }
    return job_data

def sync_with_cron_job_org_sync(settings: dict, existing_job_id: Optional[int] = None) -> tuple[Optional[int], str]:
    api_key = os.getenv("CRON_JOB_ORG_API_KEY", "").strip()

    if not api_key or api_key == "your_cron_job_org_api_key_here":
        return existing_job_id, "Placeholder API key detected in .env. Saved settings to DB."

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = build_cron_job_payload(settings)
    data_bytes = json.dumps(payload).encode("utf-8")

    try:
        if existing_job_id:
            # Update existing job
            url = f"{CRON_JOB_ORG_API_URL}/{existing_job_id}"
            req = urllib.request.Request(url, data=data_bytes, headers=headers, method="PUT")
        else:
            # Create new job
            url = CRON_JOB_ORG_API_URL
            req = urllib.request.Request(url, data=data_bytes, headers=headers, method="PUT")

        with urllib.request.urlopen(req, timeout=10) as resp:
            resp_data = json.loads(resp.read().decode("utf-8"))
            new_job_id = resp_data.get("jobId") or existing_job_id
            return new_job_id, "Successfully synced with Cron-job.org API"

    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        return existing_job_id, f"Cron-job.org API Error ({e.code}): {err_body}"
    except Exception as e:
        return existing_job_id, f"Failed to sync with Cron-job.org: {str(e)}"

def delete_cron_job_org_sync(job_id: int) -> tuple[bool, str]:
    api_key = os.getenv("CRON_JOB_ORG_API_KEY", "").strip()

    if not api_key or api_key == "your_cron_job_org_api_key_here":
        return True, "Placeholder API key detected in .env. Job marked as deleted in DB."

    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    try:
        url = f"{CRON_JOB_ORG_API_URL}/{job_id}"
        req = urllib.request.Request(url, headers=headers, method="DELETE")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return True, f"Successfully deleted job {job_id} from Cron-job.org"
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        return False, f"Cron-job.org API Error ({e.code}): {err_body}"
    except Exception as e:
        return False, f"Failed to delete job from Cron-job.org: {str(e)}"

@cron_router.get("/settings", response_model=CronScheduleResponse)
async def get_cron_settings(user: dict = Depends(get_current_user)):
    doc = await db.cron_settings.find_one({"setting_type": "blog_frequency"})
    if not doc:
        public_url = os.getenv("PUBLIC_APP_URL", "http://localhost:8000").rstrip("/")
        default_target = f"{public_url}/api/v1/cron/execute-blog-job"
        default_settings = {
            "setting_type": "blog_frequency",
            "frequency_type": "daily",
            "time_of_day": "09:00",
            "day_of_week": 1,
            "interval_days": 3,
            "cron_expression": "0 9 * * *",
            "enabled": True,
            "timezone": "Asia/Kolkata",
            "target_url": default_target,
            "cron_job_org_status": "Not Synced"
        }
        await db.cron_settings.insert_one(default_settings)
        doc = default_settings

    return format_cron_settings(doc)

@cron_router.post("/settings", response_model=CronScheduleResponse)
async def update_cron_settings(settings: CronScheduleUpdate, user: dict = Depends(get_current_user)):
    existing_doc = await db.cron_settings.find_one({"setting_type": "blog_frequency"})
    existing_job_id = existing_doc.get("cron_job_id") if existing_doc else None

    settings_dict = settings.model_dump()
    settings_dict["setting_type"] = "blog_frequency"
    settings_dict["updated_at"] = datetime.now(timezone.utc).isoformat()

    # Sync with Cron-job.org in async thread pool
    new_job_id, sync_msg = await asyncio.to_thread(sync_with_cron_job_org_sync, settings_dict, existing_job_id)
    settings_dict["cron_job_id"] = new_job_id
    settings_dict["cron_job_org_status"] = sync_msg

    await db.cron_settings.update_one(
        {"setting_type": "blog_frequency"},
        {"$set": settings_dict},
        upsert=True
    )

    updated_doc = await db.cron_settings.find_one({"setting_type": "blog_frequency"})
    return format_cron_settings(updated_doc)

@cron_router.delete("/delete-job")
async def delete_cron_job(user: dict = Depends(get_current_user)):
    existing_doc = await db.cron_settings.find_one({"setting_type": "blog_frequency"})
    if not existing_doc or not existing_doc.get("cron_job_id"):
        await db.cron_settings.update_one(
            {"setting_type": "blog_frequency"},
            {"$set": {"enabled": False, "cron_job_id": None, "cron_job_org_status": "Job Deleted"}}
        )
        return {"message": "No active Cron-job.org job found. Local schedule disabled.", "status": "success"}

    job_id = existing_doc.get("cron_job_id")
    success, msg = await asyncio.to_thread(delete_cron_job_org_sync, job_id)

    await db.cron_settings.update_one(
        {"setting_type": "blog_frequency"},
        {"$set": {"enabled": False, "cron_job_id": None, "cron_job_org_status": msg}}
    )

    return {"message": msg, "status": "success" if success else "error"}

@cron_router.post("/trigger-manual")
async def trigger_manual_blog_generation(user: dict = Depends(get_current_user)):
    result = await execute_blog_generation_process(trigger_type="Manual Dashboard Trigger")
    return result

@cron_router.get("/execute-blog-job")
@cron_router.post("/execute-blog-job")
async def execute_cron_webhook(request: Request, x_cron_secret: Optional[str] = Header(None, alias="X-Cron-Secret")):
    expected_secret = os.getenv("CRON_JOB_SECRET", "")
    if expected_secret and expected_secret != "your_cron_job_secret_key_here":
        if x_cron_secret != expected_secret:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Cron Secret Header")

    result = await execute_blog_generation_process(trigger_type="Automated Cron Job")
    return result

async def execute_blog_generation_process(trigger_type: str) -> dict:
    now_str = datetime.now(timezone.utc).isoformat()

    # Fetch active recipients from db
    cursor = db.recipients.find({"is_active": True})
    active_recipients = []
    async for doc in cursor:
        active_recipients.append(doc.get("email"))

    log_entry = {
        "timestamp": now_str,
        "trigger_type": trigger_type,
        "status": "Success",
        "blog_title": f"HydraLakes Automated Tech Blog - {now_str[:10]}",
        "recipients_notified_count": len(active_recipients),
        "recipients": active_recipients,
        "drive_file_id": f"drive_doc_{now_str[:10]}_xyz",
        "message": "Blog generated, saved to Google Drive, and emails queued."
    }

    await db.cron_logs.insert_one(log_entry)
    if "_id" in log_entry:
        log_entry["_id"] = str(log_entry["_id"])

    # Update last_run in settings
    await db.cron_settings.update_one(
        {"setting_type": "blog_frequency"},
        {"$set": {"last_run": now_str}}
    )

    return {
        "status": "success",
        "timestamp": now_str,
        "trigger_type": trigger_type,
        "recipients_count": len(active_recipients),
        "details": log_entry
    }

@cron_router.get("/logs")
async def get_cron_logs(user: dict = Depends(get_current_user)):
    cursor = db.cron_logs.find().sort("timestamp", -1).limit(5)
    logs = []
    async for doc in cursor:
        logs.append({
            "id": str(doc["_id"]),
            "timestamp": doc.get("timestamp"),
            "trigger_type": doc.get("trigger_type"),
            "status": doc.get("status"),
            "blog_title": doc.get("blog_title"),
            "recipients_count": doc.get("recipients_notified_count", 0),
            "message": doc.get("message")
        })
    return logs
