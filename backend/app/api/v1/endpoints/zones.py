from fastapi import APIRouter, HTTPException
from typing import List
from app.services.data_store import data_store
from app.schemas.zone import FloodZone

router = APIRouter()

@router.get("/zones", response_model=List[FloodZone], summary="Get all flood zones with live risk levels")
async def get_all_zones():
    return list(data_store.zones.values())

@router.get("/zones/{zone_id}", response_model=FloodZone, summary="Get specific flood zone details")
async def get_zone(zone_id: str):
    if zone_id not in data_store.zones:
        raise HTTPException(status_code=404, detail=f"Zone '{zone_id}' not found")
    return data_store.zones[zone_id]
