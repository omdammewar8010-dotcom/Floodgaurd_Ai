import time
import math
from typing import Dict, List, Any, Optional
from app.schemas.zone import FloodZone, LatLng, ContributingFactor
from app.schemas.sensor import SensorDevice, SensorLocation
from app.schemas.route import RoadSegment, GeoPoint
from app.schemas.report import CitizenReport
from app.schemas.alert import FloodAlert
from app.schemas.resource import EmergencyResource, ResourceLocation

class DataStore:
    def __init__(self):
        self.zones: Dict[str, FloodZone] = {}
        self.sensors: Dict[str, SensorDevice] = {}
        self.roads: Dict[str, RoadSegment] = {}
        self.alerts: Dict[str, FloodAlert] = {}
        self.reports: Dict[str, CitizenReport] = {}
        self.resources: Dict[str, EmergencyResource] = {}
        self.simulation_state = {
            "scenario": "normal",
            "rainfallMmHr": 5.0,
            "drainageSaturationPercent": 15.0,
            "systemStatus": "All Systems Normal"
        }
        self._seed_initial_data()

    def _seed_initial_data(self):
        now_ms = int(time.time() * 1000)

        # 1. 10 Flood Zones (Pune City)
        zones_data = [
            ("zone_shivajinagar", "Shivajinagar Lowlands", 18.5314, 73.8446, 552.0, 18.5, "LOW", 0.15, 18000),
            ("zone_deccan", "Deccan Mutha Riverfront", 18.5167, 73.8417, 549.5, 15.0, "LOW", 0.18, 22000),
            ("zone_sangamwadi", "Sangamwadi Confluence", 18.5362, 73.8675, 545.0, 22.0, "LOW", 0.22, 14000),
            ("zone_yerwada", "Yerwada Mula River Basin", 18.5529, 73.8797, 546.2, 19.0, "LOW", 0.12, 31000),
            ("zone_baner", "Baner Ramnadi Basin", 18.5590, 73.7868, 565.0, 12.0, "LOW", 0.10, 25000),
            ("zone_kothrud", "Kothrud Paud Road Basin", 18.5074, 73.8077, 570.0, 14.0, "LOW", 0.08, 28000),
            ("zone_swargate", "Swargate Canal Underpass", 18.5018, 73.8586, 554.0, 16.0, "LOW", 0.14, 35000),
            ("zone_koregaon", "Koregaon Park Nala Corridor", 18.5362, 73.8940, 550.0, 17.0, "LOW", 0.11, 16000),
            ("zone_hadapsar", "Hadapsar Industrial Lowlands", 18.5089, 73.9259, 553.5, 20.0, "LOW", 0.09, 42000),
            ("zone_aundh", "Aundh Mula Basin", 18.5580, 73.8075, 556.0, 13.5, "LOW", 0.10, 20000)
        ]

        for zid, name, lat, lng, elev, drain, risk, rscore, pop in zones_data:
            # Generate small polygon around center
            offset = 0.008
            poly = [
                LatLng(latitude=lat + offset, longitude=lng - offset),
                LatLng(latitude=lat + offset, longitude=lng + offset),
                LatLng(latitude=lat - offset, longitude=lng + offset),
                LatLng(latitude=lat - offset, longitude=lng - offset)
            ]
            self.zones[zid] = FloodZone(
                zoneId=zid,
                name=name,
                city="Pune",
                boundary=poly,
                center=LatLng(latitude=lat, longitude=lng),
                baselineElevationMeters=elev,
                drainageCapacityM3s=drain,
                currentRiskLevel=risk,
                currentRiskScore=rscore,
                estimatedOnsetMinutes=None,
                averageWaterLevelCm=8.5,
                rainfallRateMmHr=5.0,
                drainageUtilizationPercent=15.0,
                contributingFactors=[
                    ContributingFactor(factor="Baseline Elevation", impact="medium", description=f"{elev}m above sea level", weight=0.2),
                    ContributingFactor(factor="Drainage Capacity", impact="low", description=f"Storm water outflow rate {drain} m³/s", weight=0.25)
                ],
                affectedPopulation=pop,
                activeSensorsCount=2,
                lastEvaluated=now_ms
            )

        # 2. 20+ Sensors
        sensors_data = [
            ("FG-PUN-001", "Shivajinagar Railway Subway", "zone_shivajinagar", 18.5320, 73.8450, 12.0, 5.0),
            ("FG-PUN-002", "JM Road Sambhaji Park Nala", "zone_shivajinagar", 18.5280, 73.8430, 9.5, 5.0),
            ("FG-PUN-003", "Alka Talkies Bridge Pier", "zone_deccan", 18.5145, 73.8465, 14.0, 6.0),
            ("FG-PUN-004", "Z-Bridge Riverside Walk", "zone_deccan", 18.5190, 73.8420, 10.0, 5.0),
            ("FG-PUN-005", "Sangam Bridge Culvert", "zone_sangamwadi", 18.5350, 73.8650, 15.0, 7.0),
            ("FG-PUN-006", "RTO Low-Lying Storm Drain", "zone_sangamwadi", 18.5310, 73.8700, 11.0, 6.0),
            ("FG-PUN-007", "Yerwada Shanti Nagar Nala", "zone_yerwada", 18.5510, 73.8780, 8.0, 4.0),
            ("FG-PUN-008", "Bund Garden Weir Intake", "zone_yerwada", 18.5400, 73.8820, 16.5, 6.0),
            ("FG-PUN-009", "Baner Balewadi Highway Culvert", "zone_baner", 18.5620, 73.7840, 7.0, 3.0),
            ("FG-PUN-010", "Ramnadi Sutarwadi Inflow", "zone_baner", 18.5550, 73.7900, 11.5, 4.0),
            ("FG-PUN-011", "Chandani Chowk Descent Channel", "zone_kothrud", 18.5050, 73.7920, 6.0, 3.0),
            ("FG-PUN-012", "Karve Statue Storm Trunk", "zone_kothrud", 18.5020, 73.8150, 9.0, 4.0),
            ("FG-PUN-013", "Swargate Flyover Sump", "zone_swargate", 18.5010, 73.8580, 13.0, 5.0),
            ("FG-PUN-014", "Sarasbaug Peshwe Lake Overflow", "zone_swargate", 18.5040, 73.8520, 10.5, 5.0),
            ("FG-PUN-015", "North Main Road Nala No 2", "zone_koregaon", 18.5370, 73.8920, 8.5, 4.0),
            ("FG-PUN-016", "Koregaon Park South Canal", "zone_koregaon", 18.5320, 73.8980, 7.0, 4.0),
            ("FG-PUN-017", "Magarpatta Low Dip Collector", "zone_hadapsar", 18.5120, 73.9280, 6.5, 3.0),
            ("FG-PUN-018", "Gadital Bus Depot Culvert", "zone_hadapsar", 18.5040, 73.9310, 9.0, 4.0),
            ("FG-PUN-019", "Aundh Chest Hospital Underbridge", "zone_aundh", 18.5600, 73.8050, 10.0, 5.0),
            ("FG-PUN-020", "Spicer College River Bend", "zone_aundh", 18.5540, 73.8150, 12.0, 5.0)
        ]

        for sid, name, zid, lat, lng, wlevel, rain in sensors_data:
            self.sensors[sid] = SensorDevice(
                id=sid,
                deviceId=sid,
                name=name,
                zoneId=zid,
                location=SensorLocation(latitude=lat, longitude=lng, zoneId=zid, landmark=name),
                waterLevel=wlevel,
                rateOfRiseCmMin=0.05,
                rainfall=rain,
                temperature=26.5,
                humidity=78.0,
                battery=96.0,
                status="active",
                isOnline=True,
                lastUpdated=now_ms
            )

        # 3. 30+ Road Segments with Realistic Connectivity
        roads_data = [
            ("RD-001", "Jangali Maharaj (JM) Road", 18.5204, 73.8467, 18.5320, 73.8450, 1.8, 551.0, 5.0, False, 0.15),
            ("RD-002", "Fergusson College (FC) Road", 18.5190, 73.8400, 18.5310, 73.8390, 1.7, 556.0, 2.0, False, 0.08),
            ("RD-003", "Shivajinagar Railway Subway", 18.5310, 73.8430, 18.5330, 73.8480, 0.6, 548.0, 12.0, False, 0.25),
            ("RD-004", "Karve Road (Deccan to Kothrud)", 18.5140, 73.8420, 18.5030, 73.8120, 3.4, 560.0, 4.0, False, 0.10),
            ("RD-005", "Tilak Road (Alka to Swargate)", 18.5120, 73.8480, 18.5020, 73.8560, 2.1, 555.0, 6.0, False, 0.12),
            ("RD-006", "Sinhagad Road River Section", 18.4980, 73.8380, 18.4750, 73.8200, 4.0, 549.0, 8.0, False, 0.20),
            ("RD-007", "Sangamwadi Bridge Link Road", 18.5340, 73.8560, 18.5410, 73.8720, 2.3, 546.0, 7.0, False, 0.18),
            ("RD-008", "Bund Garden Bridge Road", 18.5370, 73.8780, 18.5450, 73.8860, 1.5, 548.0, 6.0, False, 0.14),
            ("RD-009", "Yerwada Ahmednagar Highway", 18.5480, 73.8820, 18.5680, 73.9050, 3.2, 552.0, 5.0, False, 0.11),
            ("RD-010", "Baner Main High Street", 18.5550, 73.7820, 18.5660, 73.7910, 2.0, 566.0, 3.0, False, 0.07),
            ("RD-011", "Pashan-Sus Elevated Bypass", 18.5420, 73.7780, 18.5580, 73.7690, 2.8, 578.0, 0.0, False, 0.03),
            ("RD-012", "Paud Road Flyover Expressway", 18.5060, 73.8100, 18.5030, 73.7910, 2.5, 572.0, 1.0, False, 0.05),
            ("RD-013", "Swargate Underpass Transit corridor", 18.5010, 73.8570, 18.5030, 73.8610, 0.8, 550.0, 9.0, False, 0.22),
            ("RD-014", "Shankar Sheth Road", 18.5030, 73.8630, 18.5060, 73.8880, 2.8, 555.0, 4.0, False, 0.09),
            ("RD-015", "Koregaon Park North Main Road", 18.5360, 73.8900, 18.5390, 73.9100, 2.2, 551.0, 5.0, False, 0.12),
            ("RD-016", "Kalyani Nagar Bridge", 18.5440, 73.8980, 18.5510, 73.9030, 1.2, 549.0, 8.0, False, 0.19),
            ("RD-017", "Hadapsar Gadital Junction", 18.5040, 73.9280, 18.5110, 73.9350, 1.4, 554.0, 6.0, False, 0.13),
            ("RD-018", "Magarpatta Inner Ring Road", 18.5130, 73.9250, 18.5240, 73.9330, 2.0, 558.0, 2.0, False, 0.06),
            ("RD-019", "University Road (Pune Vidyapeeth)", 18.5320, 73.8310, 18.5520, 73.8220, 2.6, 562.0, 3.0, False, 0.08),
            ("RD-020", "Aundh DP Road River Causeway", 18.5570, 73.8020, 18.5630, 73.8180, 1.9, 547.0, 10.0, False, 0.24),
            ("RD-021", "Senapati Bapat Road", 18.5280, 73.8320, 18.5390, 73.8290, 1.6, 565.0, 1.5, False, 0.05),
            ("RD-022", "Laxmi Road Heritage Corridor", 18.5150, 73.8520, 18.5180, 73.8640, 1.5, 553.0, 4.5, False, 0.11),
            ("RD-023", "Bajirao Road", 18.5120, 73.8540, 18.5220, 73.8550, 1.3, 554.0, 5.0, False, 0.12),
            ("RD-024", "Deccan Riverbed Causeway", 18.5170, 73.8430, 18.5240, 73.8460, 1.1, 545.0, 15.0, False, 0.35),
            ("RD-025", "Mula-Mutha Confluence Overpass", 18.5390, 73.8710, 18.5440, 73.8780, 1.0, 556.0, 2.0, False, 0.06),
            ("RD-026", "Kothrud Chandani Chowk Artery", 18.5080, 73.8050, 18.5030, 73.7850, 2.4, 582.0, 0.0, False, 0.02),
            ("RD-027", "Satara Road Market Yard Artery", 18.4980, 73.8590, 18.4720, 73.8610, 3.0, 560.0, 3.5, False, 0.08),
            ("RD-028", "Camp East Street Connector", 18.5180, 73.8780, 18.5260, 73.8840, 1.2, 557.0, 2.5, False, 0.07),
            ("RD-029", "Pune Station Approach Ramp", 18.5280, 73.8740, 18.5310, 73.8730, 0.5, 553.0, 5.5, False, 0.13),
            ("RD-030", "Bremen Chowk Aundh Connector", 18.5580, 73.8080, 18.5490, 73.8160, 1.4, 559.0, 2.0, False, 0.06)
        ]

        for rid, name, lat1, lng1, lat2, lng2, lkm, elev, wdepth, closed, rscore in roads_data:
            self.roads[rid] = RoadSegment(
                roadId=rid,
                name=name,
                coordinates=[GeoPoint(latitude=lat1, longitude=lng1), GeoPoint(latitude=lat2, longitude=lng2)],
                lengthKm=lkm,
                elevationMeters=elev,
                currentWaterDepthCm=wdepth,
                isClosed=closed,
                riskScore=rscore,
                passableForCars=(wdepth < 15.0),
                passableForBuses=(wdepth < 35.0)
            )

        # 4. Emergency Resources
        resources_data = [
            ("RES-001", "NDRF Quick Deployment Boat Team 1", "rescue_boat", 8, "available", 18.5300, 73.8470, "Shivajinagar HQ"),
            ("RES-002", "NDRF Inflatable Rescue Craft 2", "rescue_boat", 6, "available", 18.5380, 73.8690, "Sangamwadi Boat Club"),
            ("RES-003", "PMC High-Capacity Dewatering Pump 101", "dewatering_pump", 0, "available", 18.5315, 73.8440, "Shivajinagar Depot"),
            ("RES-004", "PMC Trailer Dewatering Pump 102", "dewatering_pump", 0, "available", 18.5020, 73.8580, "Swargate Central Yard"),
            ("RES-005", "Advanced Life Support Ambulance 04", "ambulance", 2, "available", 18.5220, 73.8410, "Deccan Sassoon Annex"),
            ("RES-006", "Sassoon Emergency Trauma Van 07", "ambulance", 2, "available", 18.5270, 73.8710, "Pune Central Hospital"),
            ("RES-007", "Fire & Rescue 4x4 Emergency Rig 1", "quick_response_vehicle", 5, "available", 18.5110, 73.8490, "Tilak Road Fire Station"),
            ("RES-008", "Disaster Response Flood Truck 2", "quick_response_vehicle", 6, "available", 18.5560, 73.7890, "Baner Disaster Post")
        ]

        for res_id, name, rtype, cap, status, lat, lng, base in resources_data:
            self.resources[res_id] = EmergencyResource(
                id=res_id,
                name=name,
                type=rtype,
                capacity=cap,
                status=status,
                location=ResourceLocation(latitude=lat, longitude=lng, currentBase=base),
                lastStatusUpdate=now_ms
            )

        # 5. Pre-seeded Alerts
        self.alerts["ALT-001"] = FloodAlert(
            id="ALT-001",
            zoneId="zone_shivajinagar",
            zoneName="Shivajinagar Lowlands",
            severity="INFO",
            title="Precautionary Drainage Monitoring Active",
            message="Light precipitation observed. All storm water pumps running at normal baseline capacity.",
            estimatedOnsetMinutes=None,
            recommendedAction="Normal commute permitted. Keep monitoring weather updates.",
            roadsToAvoid=[],
            issuedAt=now_ms - 1800000,
            expiresAt=now_ms + 7200000,
            isActive=True
        )

        # 6. Pre-seeded Citizen Report
        self.reports["REP-001"] = CitizenReport(
            id="REP-001",
            userId="citizen-8821",
            userName="Rohan Joshi",
            latitude=18.5312,
            longitude=73.8448,
            address="JM Road, near Sambhaji Garden Gate",
            hazardType="road_flooding",
            waterDepthEstimateCm=14.0,
            description="Water starting to accumulate near curb drain during recent shower.",
            photoUrl="https://images.unsplash.com/photo-1547683905-f686c993aae5?auto=format&fit=crop&w=600&q=80",
            aiVerified=True,
            aiConfidence=0.92,
            aiDetectedHazard="Pavement water logging detected",
            status="verified",
            createdAt=now_ms - 900000
        )

data_store = DataStore()
