import joblib
import pandas as pd
import os
from app.core.config import settings

class RiskPredictor:
    def __init__(self):
        # We look for a trained model. If not found, we use a fallback heuristic.
        # (See the bootstrap script below to generate this model)
        self.model_path = os.path.join(settings.MODEL_DIR, "xgboost_flood_model.joblib")
        self.model = None
        
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)

    def predict_flood_risk(self, climate_data: dict, slope: float) -> tuple[float, str]:
        if self.model:
            # Prepare features for XGBoost
            features = pd.DataFrame([{
                "precipitation": climate_data["precipitation_mm"],
                "soil_moisture": climate_data["soil_moisture"],
                "elevation": climate_data["elevation"],
                "slope": slope
            }])
            probability = float(self.model.predict_proba(features)[0][1])
        else:
            # Heuristic fallback if model isn't trained yet
            rain_factor = min(climate_data["precipitation_mm"] / 50.0, 1.0)
            moisture_factor = climate_data["soil_moisture"]
            probability = (rain_factor * 0.7) + (moisture_factor * 0.3)
        
        # Determine Severity
        severity = "LOW"
        if probability > 0.8: severity = "CRIT"
        elif probability > 0.5: severity = "HIGH"
        elif probability > 0.3: severity = "MOD"

        return min(probability, 1.0), severity