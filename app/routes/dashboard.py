# app/routes/dashboard.py
from fastapi import APIRouter, Depends, HTTPException, status
import asyncpg
from typing import List

from app.controllers.dashboard_controller import dashboard_controller
from app.schemas.dashboard import DashboardStats, RecentActivity, ActivityItem
from app.db.connection import get_connection

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(conn: asyncpg.Connection = Depends(get_connection)):
    """
    Obtiene estadísticas generales para el dashboard
    """
    try:
        stats = await dashboard_controller.get_dashboard_stats(conn)
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo estadísticas: {str(e)}"
        )

@router.get("/activity", response_model=RecentActivity)
async def get_recent_activity(
    conn: asyncpg.Connection = Depends(get_connection),
    limit: int = 10
):
    """
    Obtiene actividad reciente del sistema
    """
    try:
        activities = await dashboard_controller.get_recent_activity(conn, limit)
        return {
            "activities": activities,
            "total": len(activities)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo actividad: {str(e)}"
        )