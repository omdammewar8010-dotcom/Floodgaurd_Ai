from fastapi import APIRouter, HTTPException, status
from typing import List
import time
from app.services.data_store import data_store
from app.services.firebase_service import firebase_service
from app.schemas.alert import FloodAlert

router = APIRouter()

@router.get("/alerts", response_model=List[FloodAlert], summary="Get active and recent flood alerts")
async def get_alerts():
    return list(data_store.alerts.values())

@router.post("/alerts", response_model=FloodAlert, status_code=status.HTTP_201_CREATED, summary="Issue a new emergency alert")
async def create_alert(alert: FloodAlert):
    data_store.alerts[alert.id] = alert
    firebase_service.publish_alert(alert.id, alert.model_dump())
    return alert
