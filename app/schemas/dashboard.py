# app/schemas/dashboard.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class DashboardStats(BaseModel):
    total_employees: int
    total_departments: int
    total_payroll: float
    payrolls_this_month: int
    last_updated: str

class ActivityItem(BaseModel):
    type: str
    action: str
    details: str
    amount: Optional[float] = None
    timestamp: str

class RecentActivity(BaseModel):
    activities: List[ActivityItem]
    total: int