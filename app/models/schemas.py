from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ──────────────────────────── INPUTS ────────────────────────────


class RegionInput(BaseModel):
    """User-friendly input: just type the name of a region or city."""

    region: str = Field(
        ...,
        description="Nome da região, cidade ou local para análise",
        json_schema_extra={"examples": ["São Paulo", "Rio de Janeiro", "Recife, PE"]},
    )


class LocationInput(BaseModel):
    """Legacy input for direct lat/lon coordinates."""

    latitude: float = Field(..., ge=-90, le=90, description="Latitude (-90 a 90)")
    longitude: float = Field(
        ..., ge=-180, le=180, description="Longitude (-180 a 180)"
    )


class RegionSubscribe(BaseModel):
    """Input for subscribing to autonomous background monitoring."""
    region: str = Field(..., description="Nome da região para adicionar ao monitoramento automático.")


# ──────────────────────────── RESPONSES ─────────────────────────


class ClimateSnapshot(BaseModel):
    """Current climate conditions at the analyzed location."""

    temperature_c: float = Field(..., description="Temperatura atual (°C)")
    apparent_temperature_c: float = Field(
        ..., description="Sensação térmica (°C)"
    )
    humidity_percent: float = Field(
        ..., description="Umidade relativa do ar (%)"
    )
    precipitation_mm: float = Field(
        ..., description="Precipitação atual (mm)"
    )
    daily_precipitation_mm: float = Field(
        ..., description="Precipitação acumulada do dia (mm)"
    )
    soil_moisture: float = Field(
        ..., description="Umidade do solo (0 a 1)"
    )
    wind_speed_kmh: float = Field(
        ..., description="Velocidade do vento (km/h)"
    )
    wind_gusts_kmh: float = Field(
        ..., description="Rajadas de vento (km/h)"
    )
    surface_pressure_hpa: float = Field(
        ..., description="Pressão atmosférica (hPa)"
    )
    elevation_meters: float = Field(
        ..., description="Elevação do terreno (m)"
    )


class TrendInsight(BaseModel):
    """7-day forecast trend analysis insights."""
    trend_status: str = Field(..., description="'improving', 'worsening', or 'stable'")
    trend_icon: str = Field(..., description="Ícone representativo da tendência (📈, 📉, ➡️)")
    summary: str = Field(..., description="Resumo inteligente da tendência climática gerado pelo backend.")
    temperature_insight: str = Field(..., description="Detalhes sobre a variação de temperatura.")
    precipitation_insight: str = Field(..., description="Detalhes sobre a variação de chuva.")

class RiskDetail(BaseModel):
    """Individual risk analysis for one event type."""

    risk_type: str = Field(
        ..., description="Tipo de evento climático (ex: Inundação, Seca)"
    )
    risk_icon: str = Field(..., description="Ícone do tipo de risco")
    description: str = Field(
        ..., description="Descrição do tipo de risco climático"
    )
    probability_percent: float = Field(
        ..., description="Probabilidade de ocorrência (0-100%)"
    )
    severity: str = Field(
        ...,
        description="Nível de severidade: BAIXO, MODERADO, ALTO ou CRÍTICO",
    )
    severity_icon: str = Field(..., description="Ícone visual do nível")
    recommendation: str = Field(
        ..., description="Recomendação de ação para o usuário"
    )


class ClimateRiskResponse(BaseModel):
    """Complete multi-risk climate analysis aligned with SDG 13."""

    id: int
    region: str = Field(..., description="Nome da região analisada")
    latitude: float
    longitude: float
    overall_risk_level: str = Field(
        ..., description="Nível geral de risco da região"
    )
    overall_risk_icon: str = Field(
        ..., description="Ícone do nível geral de risco"
    )
    total_risks_detected: int = Field(
        ..., description="Número de riscos com nível MODERADO ou superior"
    )
    primary_threat: str = Field(
        ..., description="Principal ameaça identificada"
    )
    risks: List[RiskDetail] = Field(
        ..., description="Lista de todos os 6 riscos analisados (ODS 13)"
    )
    climate_conditions: ClimateSnapshot = Field(
        ..., description="Condições climáticas atuais no local"
    )
    trend_analysis: TrendInsight = Field(
        ..., description="Análise inteligente de tendência para os próximos 7 dias"
    )
    sdg_alignment: str = Field(
        default="ODS 13 — Ação Contra a Mudança Global do Clima",
        description="Objetivo de Desenvolvimento Sustentável da ONU",
    )
    analyzed_at: datetime = Field(
        ..., description="Data e hora da análise"
    )

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "region": "Recife, Pernambuco, Região Nordeste, Brasil",
                    "latitude": -8.05,
                    "longitude": -34.88,
                    "overall_risk_level": "MODERADO",
                    "overall_risk_icon": "🟡",
                    "total_risks_detected": 2,
                    "primary_threat": "🌡️ Onda de Calor",
                    "risks": [
                        {
                            "risk_type": "Onda de Calor",
                            "risk_icon": "🌡️",
                            "description": "Risco de temperaturas extremas.",
                            "probability_percent": 45.2,
                            "severity": "MODERADO",
                            "severity_icon": "🟡",
                            "recommendation": "Hidrate-se e evite exposição solar.",
                        }
                    ],
                    "climate_conditions": {
                        "temperature_c": 32.5,
                        "apparent_temperature_c": 36.0,
                        "humidity_percent": 72.0,
                        "precipitation_mm": 0.0,
                        "daily_precipitation_mm": 2.1,
                        "soil_moisture": 0.35,
                        "wind_speed_kmh": 15.0,
                        "wind_gusts_kmh": 28.0,
                        "surface_pressure_hpa": 1012.0,
                        "elevation_meters": 9.0,
                    },
                    "sdg_alignment": "ODS 13 — Ação Contra a Mudança Global do Clima",
                    "analyzed_at": "2026-05-28T21:00:00",
                }
            ]
        },
    }


# ── Legacy single-risk response (backward compatibility) ───────


class RiskResponse(BaseModel):
    """Human-readable single risk analysis result."""

    id: int
    region: str = Field(..., description="Nome da região analisada")
    latitude: float
    longitude: float
    risk_type: str = Field(
        ..., description="Tipo de risco analisado (ex: Inundação)"
    )
    risk_probability_percent: float = Field(
        ..., description="Probabilidade de risco em porcentagem (0-100%)"
    )
    severity: str = Field(
        ...,
        description="Nível de severidade: BAIXO, MODERADO, ALTO ou CRÍTICO",
    )
    severity_icon: str = Field(..., description="Ícone visual do nível")
    recommendation: str = Field(
        ..., description="Recomendação de ação para o usuário"
    )
    climate_conditions: ClimateSnapshot = Field(
        ..., description="Condições climáticas atuais no local"
    )
    analyzed_at: datetime = Field(
        ..., description="Data e hora da análise"
    )

    model_config = {"from_attributes": True}


class AlertResponse(BaseModel):
    """Active alert notification."""

    id: int
    region: str = Field("", description="Região do alerta")
    message: str = Field(..., description="Mensagem do alerta")
    severity: str = Field("", description="Nível de severidade")
    severity_icon: str = Field("", description="Ícone visual")
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}