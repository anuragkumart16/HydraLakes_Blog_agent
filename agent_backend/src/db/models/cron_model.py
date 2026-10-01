from pydantic import BaseModel
from typing import Optional

class CronScheduleUpdate(BaseModel):
    frequency_type: str  # 'daily', 'weekly', 'every_x_days', 'custom'
    time_of_day: Optional[str] = "09:00"
    day_of_week: Optional[int] = 1
    interval_days: Optional[int] = 3
    cron_expression: Optional[str] = "0 9 * * *"
    enabled: bool = True
    timezone: Optional[str] = "Asia/Kolkata"
    target_url: Optional[str] = None

class CronScheduleResponse(BaseModel):
    id: Optional[str] = None
    frequency_type: str
    time_of_day: str
    day_of_week: int
    interval_days: int
    cron_expression: str
    enabled: bool
    timezone: str
    target_url: Optional[str] = None
    cron_job_id: Optional[int] = None
    last_run: Optional[str] = None
    updated_at: Optional[str] = None
    cron_job_org_status: Optional[str] = None
