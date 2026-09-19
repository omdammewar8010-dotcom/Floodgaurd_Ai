import time
from fastapi import APIRouter, HTTPException, status
from typing import List
from app.services.data_store import data_store
from app.services.firebase_service import firebase_service
from app.schemas.sensor import SensorDevice, SensorReadingCreate

router = APIRouter()

@router.get("/sensors", response_model=List[SensorDevice], summary="Get all IoT sensor devices and live telemetry")
async def get_all_sensors():
    return list(data_store.sensors.values())

@router.get("/sensors/{sensor_id}", response_model=SensorDevice, summary="Get details for a specific sensor node")
async def get_sensor(sensor_id: str):
    if sensor_id not in data_store.sensors:
        raise HTTPException(status_code=404, detail=f"Sensor '{sensor_id}' not found")
    return data_store.sensors[sensor_id]

@router.post("/sensors/data", status_code=status.HTTP_201_CREATED, summary="Ingest telemetry from physical or virtual ESP32 sensor")
async def ingest_sensor_data(reading: SensorReadingCreate):
    now_ms = reading.timestamp or int(time.time() * 1000)
    device_id = reading.deviceId

    # Calculate status based on water level
    device_status = "active"
    if reading.waterLevel > 35.0:
        device_status = "critical"
    elif reading.waterLevel > 20.0:
        device_status = "warning"

    if device_id in data_store.sensors:
        sensor = data_store.sensors[device_id]
        rate = round((reading.waterLevel - sensor.waterLevel) / max(1.0, (now_ms - sensor.lastUpdated) / 60000), 2)
        sensor.waterLevel = reading.waterLevel
        sensor.rateOfRiseCmMin = rate
        sensor.rainfall = reading.rainfall
        if reading.temperature is not None:
            sensor.temperature = reading.temperature
        if reading.humidity is not None:
            sensor.humidity = reading.humidity
        if reading.battery is not None:
            sensor.battery = reading.battery
        sensor.status = device_status
        sensor.lastUpdated = now_ms
    else:
        # Register new dynamic sensor
        data_store.sensors[device_id] = SensorDevice(
            id=device_id,
            deviceId=device_id,
            name=reading.location.landmark or f"Sensor Node {device_id}",
            zoneId=reading.location.zoneId,
            location=reading.location,
            waterLevel=reading.waterLevel,
            rateOfRiseCmMin=0.0,
            rainfall=reading.rainfall,
            temperature=reading.temperature or 25.0,
            humidity=reading.humidity or 80.0,
            battery=reading.battery or 100.0,
            status=device_status,
            isOnline=True,
            lastUpdated=now_ms
        )

    # Stream to Firebase RTDB
    firebase_service.stream_sensor_reading(device_id, reading.model_dump())

    return {
        "status": "success",
        "message": f"Telemetry ingested for {device_id}",
        "processedWaterLevel": reading.waterLevel,
        "deviceStatus": device_status,
        "timestamp": now_ms
    }
