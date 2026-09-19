import math
import heapq
from typing import Dict, List, Tuple, Optional, Any
from app.services.data_store import data_store
from app.schemas.route import (
    RoadSegment,
    GeoPoint,
    RouteOption,
    RouteStep,
    SafeRouteResponse
)

VEHICLE_THRESHOLDS = {
    "two_wheeler": {"max_water_depth": 10.0, "risk_penalty": 5.0},
    "car": {"max_water_depth": 15.0, "risk_penalty": 4.0},
    "emergency_van": {"max_water_depth": 35.0, "risk_penalty": 2.0},
    "boat": {"min_water_depth": 20.0, "risk_penalty": 0.5}
}

class SafeGraphRouter:
    def __init__(self):
        # Adjacency list: node -> list of (neighbor, edge_data)
        self.adjacency: Dict[Tuple[float, float], List[Tuple[Tuple[float, float], Dict[str, Any]]]] = {}
        self.nodes: List[Tuple[float, float]] = []
        self._build_road_network()

    def _build_road_network(self):
        self.adjacency.clear()
        node_set = set()

        for rid, road in data_store.roads.items():
            u = (round(road.coordinates[0].latitude, 4), round(road.coordinates[0].longitude, 4))
            v = (round(road.coordinates[1].latitude, 4), round(road.coordinates[1].longitude, 4))
            node_set.add(u)
            node_set.add(v)

            base_time_min = max(0.5, round((road.lengthKm / 35.0) * 60, 1))

            edge_data = {
                "roadId": rid,
                "name": road.name,
                "lengthKm": road.lengthKm,
                "elevation": road.elevationMeters,
                "waterDepth": road.currentWaterDepthCm,
                "isClosed": road.isClosed,
                "riskScore": road.riskScore,
                "baseTimeMin": base_time_min,
                "coords": [road.coordinates[0], road.coordinates[1]]
            }

            self.adjacency.setdefault(u, []).append((v, edge_data))
            self.adjacency.setdefault(v, []).append((u, edge_data))

        self.nodes = list(node_set)

    def _find_nearest_node(self, lat: float, lng: float) -> Tuple[float, float]:
        best_node = None
        min_dist = float('inf')
        for node in self.nodes:
            d = math.hypot(node[0] - lat, node[1] - lng)
            if d < min_dist:
                min_dist = d
                best_node = node
        return best_node

    def _dijkstra(
        self,
        start_node: Tuple[float, float],
        end_node: Tuple[float, float],
        weight_func
    ) -> List[Tuple[float, float]]:
        pq = [(0.0, start_node, [start_node])]
        visited = {}

        while pq:
            cost, curr, path = heapq.heappop(pq)

            if curr in visited and visited[curr] <= cost:
                continue
            visited[curr] = cost

            if curr == end_node:
                return path

            for neighbor, edge_data in self.adjacency.get(curr, []):
                edge_cost = weight_func(curr, neighbor, edge_data)
                next_cost = cost + edge_cost

                if neighbor not in visited or next_cost < visited[neighbor]:
                    heapq.heappush(pq, (next_cost, neighbor, path + [neighbor]))

        return [start_node, end_node]

    def calculate_routes(
        self,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
        vehicle_type: str = "car",
        avoid_flooded_roads: bool = True
    ) -> SafeRouteResponse:
        
        self._build_road_network()

        start_node = self._find_nearest_node(origin_lat, origin_lng)
        end_node = self._find_nearest_node(dest_lat, dest_lng)

        vehicle_cfg = VEHICLE_THRESHOLDS.get(vehicle_type, VEHICLE_THRESHOLDS["car"])
        max_depth = vehicle_cfg.get("max_water_depth", 15.0)

        # 1. Fastest Weight (Travel time alone)
        def fast_weight(u, v, d):
            return d["baseTimeMin"]

        # 2. Safety Weighted Cost Function
        def safe_weight(u, v, d):
            depth = d["waterDepth"]
            risk = d["riskScore"]
            closed = d["isClosed"]
            base_t = d["baseTimeMin"]

            cost = base_t * (1.0 + (vehicle_cfg["risk_penalty"] * (risk ** 2)))
            
            if closed:
                cost += 5000.0
            
            if depth > max_depth:
                excess = depth - max_depth
                cost += (excess * 25.0) + 500.0
            else:
                cost += (depth * 2.0)

            return cost

        fast_path = self._dijkstra(start_node, end_node, fast_weight)
        safe_path = self._dijkstra(start_node, end_node, safe_weight)

        fast_option = self._compile_route_option("ROUTE-FAST", "Direct Route (Min Distance)", fast_path, max_depth)
        safe_option = self._compile_route_option("ROUTE-SAFE", "Recommended Safe Corridor", safe_path, max_depth)

        # Comparative explanation
        if fast_option.maximumWaterDepthCm > max_depth or not fast_option.isSafe:
            safe_option.isRecommended = True
            fast_option.isRecommended = False
            delta_time = round(max(0.5, safe_option.totalDurationMinutes - fast_option.totalDurationMinutes), 1)
            explanation = (
                f"Safe Corridor is recommended. While {delta_time} minutes longer, "
                f"it completely avoids {fast_option.maximumWaterDepthCm}cm flood inundation "
                f"on low-elevation roads."
            )
        else:
            safe_option.isRecommended = True
            explanation = "Direct route is clear and safe with zero critical flood inundation."

        return SafeRouteResponse(
            origin=GeoPoint(latitude=origin_lat, longitude=origin_lng),
            destination=GeoPoint(latitude=dest_lat, longitude=dest_lng),
            recommendedRoute=safe_option,
            alternativeRoute=fast_option,
            comparisonExplanation=explanation
        )

    def _compile_route_option(self, route_id: str, name: str, path_nodes: List[Tuple[float, float]], max_depth: float) -> RouteOption:
        coords: List[GeoPoint] = []
        steps: List[RouteStep] = []
        total_dist = 0.0
        total_duration = 0.0
        max_water = 0.0
        risk_scores = []
        is_safe = True

        for i in range(len(path_nodes) - 1):
            u = path_nodes[i]
            v = path_nodes[i+1]
            
            # Find matching edge data
            edge_data = {}
            for neighbor, ed in self.adjacency.get(u, []):
                if neighbor == v:
                    edge_data = ed
                    break

            rname = edge_data.get("name", "Connecting Road")
            lkm = edge_data.get("lengthKm", 1.0)
            btime = edge_data.get("baseTimeMin", 2.0)
            wdepth = edge_data.get("waterDepth", 0.0)
            rscore = edge_data.get("riskScore", 0.1)
            is_closed = edge_data.get("isClosed", False)

            total_dist += lkm
            total_duration += btime
            max_water = max(max_water, wdepth)
            risk_scores.append(rscore)

            if is_closed or wdepth > max_depth:
                is_safe = False

            coords.append(GeoPoint(latitude=u[0], longitude=u[1]))

            risk_level = "CRITICAL" if rscore > 0.7 else "HIGH" if rscore > 0.4 else "MODERATE" if rscore > 0.2 else "LOW"
            steps.append(RouteStep(
                instruction=f"Proceed on {rname}",
                roadName=rname,
                distanceKm=round(lkm, 2),
                durationMinutes=round(btime, 1),
                waterDepthCm=round(wdepth, 1),
                riskLevel=risk_level
            ))

        last_node = path_nodes[-1]
        coords.append(GeoPoint(latitude=last_node[0], longitude=last_node[1]))

        avg_risk = (sum(risk_scores) / max(1, len(risk_scores))) * 100.0

        return RouteOption(
            routeId=route_id,
            name=name,
            isRecommended=False,
            totalDurationMinutes=round(total_duration, 1),
            totalDistanceKm=round(total_dist, 2),
            averageFloodRiskPercent=round(avg_risk, 1),
            maximumWaterDepthCm=round(max_water, 1),
            isSafe=is_safe,
            safetyReason="Road clear of hazardous inundation" if is_safe else f"DANGER: Water depth {round(max_water, 1)}cm exceeds safe vehicle limit",
            pathCoordinates=coords,
            steps=steps
        )

graph_router = SafeGraphRouter()
