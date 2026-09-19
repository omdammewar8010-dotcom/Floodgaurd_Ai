from fastapi import APIRouter
from typing import List
from app.services.data_store import data_store
from app.schemas.resource import EmergencyResource, ResourceOptimizationResponse
from app.analytics.resource_optimizer import resource_optimizer

router = APIRouter()

@router.get("/resources", response_model=List[EmergencyResource], summary="List all emergency assets and deployment statuses")
async def get_emergency_resources():
    return list(data_store.resources.values())

@router.get("/resources/optimize", response_model=ResourceOptimizationResponse, summary="Get AI-assisted emergency resource allocation priority rankings")
async def optimize_resources():
    return resource_optimizer.optimize_allocations()
