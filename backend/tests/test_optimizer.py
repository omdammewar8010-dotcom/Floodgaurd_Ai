import pytest
from app.analytics.resource_optimizer import EmergencyResourceOptimizer
from app.services.data_store import data_store

def test_resource_optimizer_ranking():
    optimizer = EmergencyResourceOptimizer()
    
    # Escalate one zone to CRITICAL
    shivaji = data_store.zones.get("zone_shivajinagar")
    orig_risk = shivaji.currentRiskScore
    orig_level = shivaji.currentRiskLevel
    orig_onset = shivaji.estimatedOnsetMinutes

    try:
        shivaji.currentRiskScore = 0.95
        shivaji.currentRiskLevel = "CRITICAL"
        shivaji.estimatedOnsetMinutes = 12

        res = optimizer.optimize_allocations()
        assert len(res.rankedZones) == 10
        # Highest risk zone should be ranked near top
        top_zone = res.rankedZones[0]
        assert top_zone.zoneId == "zone_shivajinagar"
        assert top_zone.priorityScore >= 60.0
        assert len(top_zone.recommendedActions) > 0
        assert len(top_zone.suggestedAllocations) > 0
        assert "MCDA optimizer prioritized" in res.dispatchPlanExplanation
    finally:
        shivaji.currentRiskScore = orig_risk
        shivaji.currentRiskLevel = orig_level
        shivaji.estimatedOnsetMinutes = orig_onset
