import os

try:
    import numpy as np
    import pandas as pd
    from xgboost import XGBClassifier
    import joblib
except ImportError as exc:
    raise ImportError(
        "Missing required dependencies. Install numpy, pandas, xgboost, and joblib."
    ) from exc

def generate_and_train_model():
    print("🚀 Bootstrapping AETHER AI Model...")
    
    # 1. Generate synthetic geospatial/climate data
    # (High rain, high moisture, low elevation = flood)
    np.random.seed(42)
    n_samples = 1000
    
    precip = np.random.uniform(0, 150, n_samples)
    moisture = np.random.uniform(0.1, 1.0, n_samples)
    elevation = np.random.uniform(0, 2000, n_samples)
    slope = np.random.uniform(0, 1, n_samples)
    
    # Risk rule for synthetic data labeling
    risk = ((precip > 60) & (moisture > 0.6) & (elevation < 500)).astype(int)
    
    df = pd.DataFrame({
        "precipitation": precip,
        "soil_moisture": moisture,
        "elevation": elevation,
        "slope": slope
    })
    
    # 2. Train XGBoost Model
    print("🧠 Training XGBoost Classifier...")
    model = XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.1, random_state=42)
    model.fit(df, risk)
    
    # 3. Save Model
    model_dir = "./ai_models"
    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, "xgboost_flood_model.joblib")
    
    joblib.dump(model, model_path)
    print(f"✅ Model successfully saved to {model_path}")

if __name__ == "__main__":
    generate_and_train_model()