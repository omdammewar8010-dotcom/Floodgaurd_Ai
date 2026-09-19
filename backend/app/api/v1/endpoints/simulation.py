from fastapi import APIRouter
from app.services.simulation_service import simulation_service
from app.services.data_store import data_store
from app.schemas.simulation import SimulationControl, DigitalTwinState

router = APIRouter()

@router.get("/simulation/state", response_model=DigitalTwinState, summary="Get current digital flood twin state")
async def get_simulation_state():
    total_sensors = len(data_store.sensors)
    avg_w = sum(s.waterLevel for s in data_store.sensors.values()) / max(1, total_sensors)
    closed_roads = len([r for r in data_store.roads.values() if r.isClosed])
    critical_zones = len([z for z in data_store.zones.values() if z.currentRiskLevel == "CRITICAL"])
    active_alerts = len([a for a in data_store.alerts.values() if a.isActive])

    return DigitalTwinState(
        scenario=data_store.simulation_state["scenario"],
        globalRainfallMmHr=data_store.simulation_state["rainfallMmHr"],
        drainageCapacityOverallPercent=data_store.simulation_state["drainageSaturationPercent"],
        totalFloodedRoadsCount=closed_roads,
        totalCriticalZonesCount=critical_zones,
        averageWaterLevelCm=round(avg_w, 1),
        activeSensors=total_sensors,
        activeAlertsCount=active_alerts,
        systemStatus=data_store.simulation_state["systemStatus"],
        lastUpdated=int(list(data_store.sensors.values())[0].lastUpdated if total_sensors > 0 else 0)
    )

@router.post("/simulation/scenario", response_model=DigitalTwinState, summary="Trigger simulated flood escalation scenario")
async def trigger_scenario(control: SimulationControl):
    return simulation_service.set_scenario(
        scenario=control.scenario,
        rainfall=control.rainfallIntensityMmHr,
        drainage_sat=control.drainageSaturationPercent
    )

@router.post("/simulation/reset", response_model=DigitalTwinState, summary="Reset simulation back to normal baseline")
async def reset_simulation():
    return simulation_service.set_scenario(scenario="normal", rainfall=5.0, drainage_sat=15.0)
