"""
AETHER Climate Risk Analyzer — SDG 13 (Climate Action)
Analyzes 6 extreme climate events using real-time meteorological data.

Risk types aligned with ODS 13:
  1. Inundação (Flood)             — heavy rain + saturated soil + low elevation
  2. Seca (Drought)                — no rain + dry soil + low humidity
  3. Onda de Calor (Heat Wave)     — extreme temperature + high apparent temp
  4. Tempestade Severa (Storm)     — strong winds + gusts + heavy precipitation
  5. Deslizamento de Terra (Landslide) — steep terrain + rain + saturated soil
  6. Incêndio Florestal (Wildfire) — high temp + dry air + dry soil + wind
"""

import joblib
import pandas as pd
import os
from typing import Dict, Any, List
from app.core.config import settings


# ── Severity thresholds ─────────────────────────────────────────

def _classify_severity(probability: float) -> str:
    """Maps a 0-1 probability to a severity label."""
    if probability > 0.8:
        return "CRIT"
    elif probability > 0.5:
        return "HIGH"
    elif probability > 0.3:
        return "MOD"
    return "LOW"


# ── Individual Risk Calculators ─────────────────────────────────

def _calc_flood_risk(data: dict, slope: float, model=None) -> float:
    """
    Flood risk based on precipitation, soil moisture, and elevation.
    Uses XGBoost model if available, otherwise heuristic.
    """
    if model is not None:
        features = pd.DataFrame([{
            "precipitation": data["precipitation_mm"],
            "soil_moisture": data["soil_moisture"],
            "elevation": data["elevation"],
            "slope": slope,
        }])
        return float(model.predict_proba(features)[0][1])

    # Heuristic: combines rainfall intensity, soil saturation, and terrain
    rain_factor = min(data["precip_today_mm"] / 50.0, 1.0)
    moisture_factor = min(data["soil_moisture"] / 0.8, 1.0)
    elevation_factor = max(0.0, 1.0 - (data["elevation"] / 500.0))
    current_rain = min(data["precipitation_mm"] / 20.0, 1.0)

    prob = (
        rain_factor * 0.35
        + moisture_factor * 0.25
        + elevation_factor * 0.15
        + current_rain * 0.25
    )
    return min(prob, 1.0)


def _calc_drought_risk(data: dict) -> float:
    """
    Drought risk based on lack of rain, dry soil, and low humidity.
    Thresholds based on meteorological drought indices.
    """
    # No rain = high drought potential
    rain_absence = max(0.0, 1.0 - (data["precip_today_mm"] / 5.0))
    # Dry soil (below 0.2 = very dry)
    soil_dryness = max(0.0, 1.0 - (data["soil_moisture"] / 0.4))
    # Low humidity (below 30% = very dry air)
    humidity_dryness = max(0.0, 1.0 - (data["humidity"] / 50.0))
    # High temperature accelerates evapotranspiration
    heat_factor = min(max(0.0, (data["temperature_c"] - 25.0) / 20.0), 1.0)

    prob = (
        rain_absence * 0.35
        + soil_dryness * 0.30
        + humidity_dryness * 0.20
        + heat_factor * 0.15
    )
    return min(prob, 1.0)


def _calc_heatwave_risk(data: dict) -> float:
    """
    Heat wave risk based on temperature extremes and apparent temperature.
    WHO defines heat wave as temp > 5°C above regional 30-year average for 5+ days.
    Simplified: uses absolute thresholds.
    """
    # Max temperature factor (35°C+ = dangerous, 40°C+ = extreme)
    temp_factor = min(max(0.0, (data["temp_max_today_c"] - 30.0) / 15.0), 1.0)
    # Apparent (feels-like) temperature
    apparent_factor = min(max(0.0, (data["apparent_temperature_c"] - 32.0) / 15.0), 1.0)
    # Low humidity makes heat more bearable, high humidity makes it worse
    humidity_factor = min(data["humidity"] / 100.0, 1.0)
    # Multi-day heat persistence (check if forecast stays hot)
    forecast_temps = data.get("temp_max_forecast_c", [data["temp_max_today_c"]])
    hot_days = sum(1 for t in forecast_temps if t > 33.0)
    persistence = min(hot_days / 3.0, 1.0)

    prob = (
        temp_factor * 0.35
        + apparent_factor * 0.25
        + humidity_factor * 0.15
        + persistence * 0.25
    )
    return min(prob, 1.0)


def _calc_storm_risk(data: dict) -> float:
    """
    Severe storm risk based on wind speed, gusts, precipitation, and pressure.
    Beaufort scale: >62 km/h = storm, >88 km/h = severe, >117 km/h = hurricane-force.
    """
    # Current wind speed factor
    wind_factor = min(max(0.0, (data["wind_speed_kmh"] - 20.0) / 80.0), 1.0)
    # Wind gusts (most dangerous component)
    gust_factor = min(max(0.0, (data["wind_gusts_kmh"] - 40.0) / 80.0), 1.0)
    # Heavy precipitation
    rain_factor = min(data["precipitation_mm"] / 30.0, 1.0)
    # Low pressure indicates storm systems (< 1000 hPa = concerning)
    pressure_factor = min(max(0.0, (1015.0 - data["surface_pressure_hpa"]) / 30.0), 1.0)
    # Daily max wind/gust
    daily_wind = min(max(0.0, (data["wind_max_today_kmh"] - 30.0) / 70.0), 1.0)
    daily_gust = min(max(0.0, (data["gust_max_today_kmh"] - 50.0) / 70.0), 1.0)

    prob = (
        gust_factor * 0.25
        + wind_factor * 0.15
        + rain_factor * 0.15
        + pressure_factor * 0.15
        + daily_wind * 0.10
        + daily_gust * 0.20
    )
    return min(prob, 1.0)


def _calc_landslide_risk(data: dict, slope: float) -> float:
    """
    Landslide risk based on slope steepness, rainfall, and soil saturation.
    Critical factors: steep terrain + saturated soil + heavy rain.
    """
    # Slope is the most important factor (steep terrain = high risk)
    slope_factor = min(slope / 0.5, 1.0)  # slope > 0.5 = very steep
    # Saturated soil destabilizes terrain
    moisture_factor = min(data["soil_moisture"] / 0.7, 1.0)
    # Accumulated rainfall triggers slides
    rain_factor = min(data["precip_today_mm"] / 60.0, 1.0)
    # Current rain intensity
    current_rain = min(data["precipitation_mm"] / 15.0, 1.0)
    # High elevation areas tend to have more slope instability
    elevation_factor = min(max(0.0, (data["elevation"] - 200.0) / 1000.0), 1.0)

    prob = (
        slope_factor * 0.30
        + moisture_factor * 0.25
        + rain_factor * 0.20
        + current_rain * 0.15
        + elevation_factor * 0.10
    )
    return min(prob, 1.0)


def _calc_wildfire_risk(data: dict) -> float:
    """
    Wildfire risk based on high temperature, low humidity, dry soil, and wind.
    Based on simplified Canadian Forest Fire Weather Index (FWI) principles.
    """
    # High temperature dries vegetation
    temp_factor = min(max(0.0, (data["temperature_c"] - 25.0) / 20.0), 1.0)
    # Low humidity = dry air = fire spreads faster
    humidity_dryness = max(0.0, 1.0 - (data["humidity"] / 60.0))
    # Dry soil = dry vegetation
    soil_dryness = max(0.0, 1.0 - (data["soil_moisture"] / 0.3))
    # Wind spreads fire
    wind_factor = min(data["wind_speed_kmh"] / 50.0, 1.0)
    # No rain = no natural fire suppression
    no_rain = max(0.0, 1.0 - (data["precip_today_mm"] / 2.0))

    prob = (
        temp_factor * 0.25
        + humidity_dryness * 0.25
        + soil_dryness * 0.20
        + wind_factor * 0.15
        + no_rain * 0.15
    )
    return min(prob, 1.0)


# ── Main Analyzer ───────────────────────────────────────────────

# Risk type metadata
RISK_METADATA = {
    "flood": {
        "name_pt": "Inundação",
        "icon": "🌊",
        "description": "Risco de enchentes e alagamentos causados por chuvas intensas e solo saturado.",
    },
    "drought": {
        "name_pt": "Seca",
        "icon": "🏜️",
        "description": "Risco de seca prolongada com impacto na agricultura e abastecimento de água.",
    },
    "heatwave": {
        "name_pt": "Onda de Calor",
        "icon": "🌡️",
        "description": "Risco de temperaturas extremas com impacto na saúde pública.",
    },
    "storm": {
        "name_pt": "Tempestade Severa",
        "icon": "🌪️",
        "description": "Risco de ventos destrutivos, granizo e precipitação intensa.",
    },
    "landslide": {
        "name_pt": "Deslizamento de Terra",
        "icon": "⛰️",
        "description": "Risco de deslizamentos em encostas devido a chuvas e solo instável.",
    },
    "wildfire": {
        "name_pt": "Incêndio Florestal",
        "icon": "🔥",
        "description": "Risco de incêndios florestais devido a calor, baixa umidade e ventos.",
    },
}

SEVERITY_PT = {"LOW": "BAIXO", "MOD": "MODERADO", "HIGH": "ALTO", "CRIT": "CRÍTICO"}
SEVERITY_ICON = {"LOW": "🟢", "MOD": "🟡", "HIGH": "🟠", "CRIT": "🔴"}

RECOMMENDATIONS = {
    "flood": {
        "LOW": "Sem risco significativo de inundação. Continue monitorando.",
        "MOD": "Risco moderado de alagamento. Evite áreas baixas e próximas a rios.",
        "HIGH": "ATENÇÃO: Risco alto de inundação! Prepare plano de evacuação e evite deslocamentos desnecessários.",
        "CRIT": "PERIGO: Risco crítico de inundação! Procure abrigo elevado imediatamente. Siga a Defesa Civil.",
    },
    "drought": {
        "LOW": "Condições normais de umidade. Sem risco de seca.",
        "MOD": "Sinais de estiagem. Economize água e monitore reservatórios.",
        "HIGH": "ATENÇÃO: Seca severa! Reduza consumo de água. Risco para agricultura.",
        "CRIT": "CRISE HÍDRICA: Seca extrema! Racionamento pode ser necessário. Impacto grave na agricultura.",
    },
    "heatwave": {
        "LOW": "Temperatura dentro da normalidade. Sem riscos à saúde.",
        "MOD": "Calor acima do normal. Hidrate-se e evite exposição solar entre 10h-16h.",
        "HIGH": "ATENÇÃO: Onda de calor! Risco à saúde de idosos e crianças. Evite atividades ao ar livre.",
        "CRIT": "PERIGO: Calor extremo! Risco de morte por hipertermia. Procure ambiente climatizado.",
    },
    "storm": {
        "LOW": "Ventos normais. Sem risco de tempestade.",
        "MOD": "Ventos moderados. Recolha objetos soltos em áreas externas.",
        "HIGH": "ATENÇÃO: Tempestade severa! Evite sair de casa. Risco de queda de árvores e destelhamento.",
        "CRIT": "PERIGO: Ventos destrutivos! Procure abrigo reforçado imediatamente. Risco a estruturas.",
    },
    "landslide": {
        "LOW": "Terreno estável. Sem risco de deslizamento.",
        "MOD": "Solo úmido em encostas. Monitore sinais de movimentação do terreno.",
        "HIGH": "ATENÇÃO: Risco alto de deslizamento! Evacue áreas de encosta. Observe rachaduras no solo.",
        "CRIT": "PERIGO: Deslizamento iminente! Evacuação imediata de encostas e morros!",
    },
    "wildfire": {
        "LOW": "Condições úmidas. Risco mínimo de incêndio.",
        "MOD": "Ar seco e quente. Evite queimadas e fogueiras ao ar livre.",
        "HIGH": "ATENÇÃO: Alto risco de incêndio florestal! Não descarte lixo em vegetação. Denuncie focos de fumaça.",
        "CRIT": "EMERGÊNCIA: Condições extremas para incêndio! Qualquer faísca pode causar desastre. Evacuação pode ser necessária.",
    },
}


class ClimateAnalyzer:
    """
    Unified climate risk analyzer for SDG 13 extreme events.
    Evaluates all 6 risk types simultaneously using real-time data.
    """

    def __init__(self):
        model_path = os.path.join(settings.MODEL_DIR, "xgboost_flood_model.joblib")
        self.flood_model = None
        if os.path.exists(model_path):
            self.flood_model = joblib.load(model_path)

    def analyze_all_risks(
        self, climate_data: dict, slope: float
    ) -> List[Dict[str, Any]]:
        """
        Runs all 6 risk analyses and returns a list of results sorted by probability (highest first).
        """
        calculators = {
            "flood": lambda: _calc_flood_risk(climate_data, slope, self.flood_model),
            "drought": lambda: _calc_drought_risk(climate_data),
            "heatwave": lambda: _calc_heatwave_risk(climate_data),
            "storm": lambda: _calc_storm_risk(climate_data),
            "landslide": lambda: _calc_landslide_risk(climate_data, slope),
            "wildfire": lambda: _calc_wildfire_risk(climate_data),
        }

        results = []
        for risk_key, calc_fn in calculators.items():
            probability = calc_fn()
            severity = _classify_severity(probability)
            meta = RISK_METADATA[risk_key]

            results.append({
                "risk_type_key": risk_key,
                "risk_type": meta["name_pt"],
                "risk_icon": meta["icon"],
                "description": meta["description"],
                "probability": probability,
                "probability_percent": round(probability * 100, 1),
                "severity_key": severity,
                "severity": SEVERITY_PT[severity],
                "severity_icon": SEVERITY_ICON[severity],
                "recommendation": RECOMMENDATIONS[risk_key][severity],
            })

        # Sort by probability descending (most dangerous first)
        results.sort(key=lambda r: r["probability"], reverse=True)
        return results

    def analyze_single_risk(
        self, risk_type: str, climate_data: dict, slope: float
    ) -> Dict[str, Any]:
        """Analyzes a single risk type. Falls back to flood if type not found."""
        all_results = self.analyze_all_risks(climate_data, slope)
        for r in all_results:
            if r["risk_type_key"] == risk_type:
                return r
        return all_results[0]
