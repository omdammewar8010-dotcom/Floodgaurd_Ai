import time
import uuid
from fastapi import APIRouter, HTTPException, status
from typing import List
from app.services.data_store import data_store
from app.schemas.report import CitizenReport, CitizenReportCreate

router = APIRouter()

@router.get("/reports", response_model=List[CitizenReport], summary="Get all citizen flood and hazard reports")
async def get_all_reports():
    return sorted(list(data_store.reports.values()), key=lambda r: r.createdAt, reverse=True)

@router.post("/reports", response_model=CitizenReport, status_code=status.HTTP_201_CREATED, summary="Submit a citizen hazard report with AI verification")
async def submit_citizen_report(report_in: CitizenReportCreate):
    now_ms = int(time.time() * 1000)
    report_id = f"REP-{uuid.uuid4().hex[:6].upper()}"

    # AI Verification analysis
    # Simulates computer vision / multi-modal analysis on hazard context & image
    desc_lower = report_in.description.lower()
    is_high_risk = any(w in desc_lower for w in ["submerged", "waist", "deep", "drowning", "blocked", "overflow", "stuck"])
    
    confidence = 0.94 if (report_in.waterDepthEstimateCm > 15.0 or is_high_risk) else 0.86
    detected_class = "Severe Road Inundation" if report_in.waterDepthEstimateCm > 25.0 else "Urban Street Ponding & Surface Runoff"

    new_report = CitizenReport(
        id=report_id,
        userId=report_in.userId or "anonymous",
        userName=report_in.userName or "Citizen Reporter",
        latitude=report_in.latitude,
        longitude=report_in.longitude,
        address=report_in.address,
        hazardType=report_in.hazardType,
        waterDepthEstimateCm=report_in.waterDepthEstimateCm,
        description=report_in.description,
        photoUrl=report_in.photoUrl or "https://images.unsplash.com/photo-1547683905-f686c993aae5?auto=format&fit=crop&w=600&q=80",
        aiVerified=True,
        aiConfidence=confidence,
        aiDetectedHazard=detected_class,
        status="verified",
        createdAt=now_ms
    )

    data_store.reports[report_id] = new_report
    return new_report
