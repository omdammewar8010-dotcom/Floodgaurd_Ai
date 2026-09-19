import os
import json
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, IsolationForest
from sklearn.metrics import accuracy_score, classification_report, mean_absolute_error, r2_score

FEATURE_COLUMNS = [
    "elevation_meters",
    "rain_intensity_mm_hr",
    "cumulative_rainfall_3h_mm",
    "soil_saturation_percent",
    "drainage_capacity_m3s",
    "drainage_saturation_percent",
    "current_water_level_cm",
    "water_level_rise_rate_10m"
]

def train_and_export_models(
    data_path: str = "datasets/historical_flood_telemetry.csv",
    output_dir: str = "ml/models"
):
    os.makedirs(output_dir, exist_ok=True)

    print(f"Loading training data from: {data_path}")
    df = pd.read_csv(data_path)

    X = df[FEATURE_COLUMNS]
    y_class = df["risk_class"]
    y_forecast = df[["future_water_level_15m_cm", "future_water_level_30m_cm", "future_water_level_60m_cm"]]

    # Split dataset
    X_train, X_test, y_c_train, y_c_test, y_f_train, y_f_test = train_test_split(
        X, y_class, y_forecast, test_size=0.2, random_state=42, stratify=y_class
    )

    # 1. Train Flood Risk Classifier
    print("Training Random Forest Flood Risk Classifier...")
    clf = RandomForestClassifier(n_estimators=120, max_depth=12, random_state=42, n_jobs=-1)
    clf.fit(X_train, y_c_train)

    y_c_pred = clf.predict(X_test)
    acc = accuracy_score(y_c_test, y_c_pred)
    print(f"Classifier Accuracy on Test Set: {acc * 100:.2f}%")
    print("Classification Report:")
    print(classification_report(y_c_test, y_c_pred, target_names=["LOW", "MODERATE", "HIGH", "CRITICAL"]))

    # 2. Train Multi-Step Water Level Forecaster
    print("Training Water Level Multi-Horizon Forecaster...")
    reg = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
    reg.fit(X_train, y_f_train)

    y_f_pred = reg.predict(X_test)
    mae_15 = mean_absolute_error(y_f_test.iloc[:, 0], y_f_pred[:, 0])
    mae_30 = mean_absolute_error(y_f_test.iloc[:, 1], y_f_pred[:, 1])
    mae_60 = mean_absolute_error(y_f_test.iloc[:, 2], y_f_pred[:, 2])
    r2_overall = r2_score(y_f_test, y_f_pred)
    print(f"Forecaster MAE: +15m: {mae_15:.2f}cm | +30m: {mae_30:.2f}cm | +60m: {mae_60:.2f}cm | R2: {r2_overall:.3f}")

    # 3. Train Anomaly Detector (Isolation Forest)
    print("Training Sensor & Drainage Anomaly Detector...")
    normal_samples = X[df["is_anomaly"] == 0]
    iso = IsolationForest(n_estimators=100, contamination=0.03, random_state=42)
    iso.fit(normal_samples)

    # 4. Feature Importance & Explainability Metadata
    importances = clf.feature_importances_
    feature_importance_dict = {
        col: round(float(imp), 4) for col, imp in zip(FEATURE_COLUMNS, importances)
    }

    metadata = {
        "features": FEATURE_COLUMNS,
        "feature_importances": feature_importance_dict,
        "risk_classes": {
            0: "LOW",
            1: "MODERATE",
            2: "HIGH",
            3: "CRITICAL"
        },
        "metrics": {
            "classification_accuracy": round(float(acc), 4),
            "forecaster_mae_15m": round(float(mae_15), 4),
            "forecaster_mae_30m": round(float(mae_30), 4),
            "forecaster_mae_60m": round(float(mae_60), 4),
            "forecaster_r2": round(float(r2_overall), 4)
        }
    }

    # Save artifacts
    clf_path = os.path.join(output_dir, "flood_classifier.joblib")
    reg_path = os.path.join(output_dir, "water_forecaster.joblib")
    iso_path = os.path.join(output_dir, "anomaly_detector.joblib")
    meta_path = os.path.join(output_dir, "feature_metadata.json")

    joblib.dump(clf, clf_path)
    joblib.dump(reg, reg_path)
    joblib.dump(iso, iso_path)
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"All ML models successfully trained and exported to: {output_dir}")
    return metadata

if __name__ == "__main__":
    train_and_export_models()
