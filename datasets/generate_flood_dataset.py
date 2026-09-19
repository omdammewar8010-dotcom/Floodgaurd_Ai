import os
import random
import numpy as np
import pandas as pd

def generate_synthetic_flood_data(num_samples: int = 6000, output_path: str = "datasets/historical_flood_telemetry.csv"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    random.seed(42)
    np.random.seed(42)

    records = []

    for i in range(num_samples):
        # Simulation parameters
        elevation = round(random.uniform(542.0, 585.0), 1) # Elevation in meters (riverbank to high ridge)
        elevation_factor = (585.0 - elevation) / 43.0 # 0.0 (high/safe) to 1.0 (lowest sink)

        # Baseline conditions
        rain_intensity = round(np.random.exponential(scale=18.0), 1)
        rain_intensity = min(130.0, rain_intensity) # Cap at extreme 130 mm/hr
        
        cumulative_3h = round(rain_intensity * random.uniform(1.2, 2.8) + random.uniform(0.0, 40.0), 1)
        
        soil_saturation = round(min(100.0, 20.0 + (cumulative_3h * 0.5) + random.uniform(0.0, 20.0)), 1)
        drainage_capacity = round(random.uniform(10.0, 25.0), 1) # m^3/s

        # Drainage saturation calculation
        runoff_rate = (rain_intensity * 0.7 * (soil_saturation / 100.0))
        drainage_saturation = round(min(100.0, (runoff_rate / (drainage_capacity * 0.4)) * 100.0), 1)

        # Water level dynamics
        current_water_level = round(max(3.0, (elevation_factor * 12.0) + (drainage_saturation * 0.25) + random.uniform(-2.0, 4.0)), 1)
        
        # Rate of rise (cm per 10 mins)
        if drainage_saturation > 75.0 or rain_intensity > 45.0:
            rise_rate = round((rain_intensity * 0.08) + (elevation_factor * 2.5) + random.uniform(0.5, 2.0), 2)
        else:
            rise_rate = round(max(-0.5, (rain_intensity * 0.02) - 0.2 + random.uniform(-0.2, 0.4)), 2)

        # Multi-step future water levels
        future_15m = round(max(0.0, current_water_level + (rise_rate * 1.5) + random.uniform(-0.5, 0.5)), 1)
        future_30m = round(max(0.0, current_water_level + (rise_rate * 3.0) + random.uniform(-1.0, 1.0)), 1)
        future_60m = round(max(0.0, current_water_level + (rise_rate * 5.8) + random.uniform(-1.8, 1.8)), 1)

        # Ground truth classification based on physical thresholds
        # Water depth > 35cm or rapid rise when saturated -> CRITICAL
        # Water depth > 22cm -> HIGH
        # Water depth > 14cm -> MODERATE
        # Otherwise -> LOW
        if future_30m >= 35.0 or (rise_rate >= 4.0 and current_water_level >= 20.0):
            risk_class = 3 # CRITICAL
            risk_label = "CRITICAL"
        elif future_30m >= 22.0 or (rise_rate >= 2.2 and current_water_level >= 14.0):
            risk_class = 2 # HIGH
            risk_label = "HIGH"
        elif future_30m >= 13.0 or rise_rate >= 1.2:
            risk_class = 1 # MODERATE
            risk_label = "MODERATE"
        else:
            risk_class = 0 # LOW
            risk_label = "LOW"

        # Sensor anomaly flag: sudden surge with zero rain (broken main or jammed gate)
        is_anomaly = (rise_rate > 3.0 and rain_intensity < 8.0) or (current_water_level > 30.0 and rain_intensity < 5.0 and cumulative_3h < 15.0)

        records.append({
            "elevation_meters": elevation,
            "elevation_factor": round(elevation_factor, 3),
            "rain_intensity_mm_hr": rain_intensity,
            "cumulative_rainfall_3h_mm": cumulative_3h,
            "soil_saturation_percent": soil_saturation,
            "drainage_capacity_m3s": drainage_capacity,
            "drainage_saturation_percent": drainage_saturation,
            "current_water_level_cm": current_water_level,
            "water_level_rise_rate_10m": rise_rate,
            "future_water_level_15m_cm": future_15m,
            "future_water_level_30m_cm": future_30m,
            "future_water_level_60m_cm": future_60m,
            "is_anomaly": int(is_anomaly),
            "risk_class": risk_class,
            "risk_label": risk_label
        })

    df = pd.DataFrame(records)
    df.to_csv(output_path, index=False)
    print(f"Generated {len(df)} synthetic flood telemetry records saved to: {output_path}")
    print("Class distribution:")
    print(df['risk_label'].value_counts())
    return df

if __name__ == "__main__":
    generate_synthetic_flood_data()
