import json
from fastapi import APIRouter, Depends, HTTPException, Request, 
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.dependencies import get_db
from app.models.schemas import (
    RegionInput,
    LocationInput,
    ClimateRiskResponse,
    RiskResponse,
    AlertResponse,
    ClimateSnapshot,
    RiskDetail,
    LeituraIoT,
)
from app.core.database import RiskAnalysis, Alert
from app.data_pipeline.open_meteo import OpenMeteoClient
from app.geospatial.processor import GeospatialProcessor
from app.ai.climate_analyzer import ClimateAnalyzer, SEVERITY_PT, SEVERITY_ICON
from app.ai.trend_analysis import TrendAnalyzer
from app.services.alert_engine import AlertEngine
from app.services.geocoder import Geocoder

router = APIRouter()
analyzer = ClimateAnalyzer()


# ── Helpers ─────────────────────────────────────────────────────


def _build_climate_snapshot(data: dict) -> ClimateSnapshot:
    """Creates a ClimateSnapshot from raw Open-Meteo data."""
    return ClimateSnapshot(
        temperature_c=round(data.get("temperature_c", 0), 1),
        apparent_temperature_c=round(data.get("apparent_temperature_c", 0), 1),
        humidity_percent=round(data.get("humidity", 0), 1),
        precipitation_mm=round(data.get("precipitation_mm", 0), 2),
        daily_precipitation_mm=round(data.get("precip_today_mm", 0), 2),
        soil_moisture=round(data.get("soil_moisture", 0), 3),
        wind_speed_kmh=round(data.get("wind_speed_kmh", 0), 1),
        wind_gusts_kmh=round(data.get("wind_gusts_kmh", 0), 1),
        surface_pressure_hpa=round(data.get("surface_pressure_hpa", 0), 1),
        elevation_meters=round(data.get("elevation", 0), 1),
    )


async def _run_full_analysis(
    lat: float, lon: float, region_name: str, db: AsyncSession
) -> dict:
    """
    Core SDG 13 analysis pipeline: fetches climate data, runs all 6 risk analyses,
    saves to database, generates alerts if needed.
    """

    # 1. Fetch comprehensive climate data
    climate_data = await OpenMeteoClient.get_environmental_data(lat, lon)

    # 2. Geospatial processing
    slope = GeospatialProcessor.calculate_slope(climate_data["elevation"])
    wkt_geom = GeospatialProcessor.generate_risk_buffer_wkt(lat, lon)

    # 3. Run all 6 risk analyses
    risk_results = analyzer.analyze_all_risks(climate_data, slope)

    # 4. Determine overall risk level (highest severity across all risks)
    severity_order = {"LOW": 0, "MOD": 1, "HIGH": 2, "CRIT": 3}
    max_severity = max(risk_results, key=lambda r: severity_order.get(r["severity_key"], 0))
    overall_severity_key = max_severity["severity_key"]
    threats_above_mod = [r for r in risk_results if severity_order.get(r["severity_key"], 0) >= 1]
    primary_threat = risk_results[0]  # Already sorted by probability desc

    # 5. Save to database
    analysis = RiskAnalysis(
        region_name=region_name,
        latitude=lat,
        longitude=lon,
        risk_type="multi",
        probability_score=primary_threat["probability"],
        severity=overall_severity_key,
        geom_wkt=wkt_geom,
        temperature_c=climate_data.get("temperature_c", 0),
        apparent_temperature_c=climate_data.get("apparent_temperature_c", 0),
        precipitation_mm=climate_data.get("precipitation_mm", 0),
        daily_precipitation_mm=climate_data.get("precip_today_mm", 0),
        soil_moisture=climate_data.get("soil_moisture", 0),
        humidity_percent=climate_data.get("humidity", 0),
        wind_speed_kmh=climate_data.get("wind_speed_kmh", 0),
        wind_gusts_kmh=climate_data.get("wind_gusts_kmh", 0),
        surface_pressure_hpa=climate_data.get("surface_pressure_hpa", 0),
        elevation_meters=climate_data.get("elevation", 0),
        risks_json=json.dumps(
            [{k: v for k, v in r.items() if k != "probability"} for r in risk_results],
            ensure_ascii=False,
        ),
    )
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)

    # 6. Generate alerts for HIGH/CRIT risks
    await AlertEngine.evaluate_multi_risk_alerts(db, analysis.id, risk_results, region_name)

    # 7. Generate Trend Insights
    trend_insight = TrendAnalyzer.generate_overall_insight(climate_data)

    # 8. Build response
    return {
        "id": analysis.id,
        "region": region_name,
        "latitude": lat,
        "longitude": lon,
        "overall_risk_level": SEVERITY_PT.get(overall_severity_key, overall_severity_key),
        "overall_risk_icon": SEVERITY_ICON.get(overall_severity_key, "⚪"),
        "total_risks_detected": len(threats_above_mod),
        "primary_threat": f"{primary_threat['risk_icon']} {primary_threat['risk_type']}",
        "risks": [
            RiskDetail(
                risk_type=r["risk_type"],
                risk_icon=r["risk_icon"],
                description=r["description"],
                probability_percent=r["probability_percent"],
                severity=r["severity"],
                severity_icon=r["severity_icon"],
                recommendation=r["recommendation"],
            )
            for r in risk_results
        ],
        "climate_conditions": _build_climate_snapshot(climate_data),
        "trend_analysis": trend_insight,
        "sdg_alignment": "ODS 13 — Ação Contra a Mudança Global do Clima",
        "analyzed_at": analysis.timestamp,
    }


async def _run_single_analysis(
    risk_type: str, lat: float, lon: float, region_name: str, db: AsyncSession
) -> dict:
    """Runs a single-risk analysis (backward compatibility)."""

    climate_data = await OpenMeteoClient.get_environmental_data(lat, lon)
    slope = GeospatialProcessor.calculate_slope(climate_data["elevation"])
    wkt_geom = GeospatialProcessor.generate_risk_buffer_wkt(lat, lon)

    risk = analyzer.analyze_single_risk(risk_type, climate_data, slope)

    analysis = RiskAnalysis(
        region_name=region_name,
        latitude=lat,
        longitude=lon,
        risk_type=risk["risk_type_key"],
        probability_score=risk["probability"],
        severity=risk["severity_key"],
        geom_wkt=wkt_geom,
        temperature_c=climate_data.get("temperature_c", 0),
        apparent_temperature_c=climate_data.get("apparent_temperature_c", 0),
        precipitation_mm=climate_data.get("precipitation_mm", 0),
        daily_precipitation_mm=climate_data.get("precip_today_mm", 0),
        soil_moisture=climate_data.get("soil_moisture", 0),
        humidity_percent=climate_data.get("humidity", 0),
        wind_speed_kmh=climate_data.get("wind_speed_kmh", 0),
        wind_gusts_kmh=climate_data.get("wind_gusts_kmh", 0),
        surface_pressure_hpa=climate_data.get("surface_pressure_hpa", 0),
        elevation_meters=climate_data.get("elevation", 0),
    )
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)

    await AlertEngine.evaluate_and_alert(
        db, analysis.id, risk["risk_type_key"], risk["severity_key"],
        risk["probability"], region_name,
    )

    return {
        "id": analysis.id,
        "region": region_name,
        "latitude": lat,
        "longitude": lon,
        "risk_type": risk["risk_type"],
        "risk_probability_percent": risk["probability_percent"],
        "severity": risk["severity"],
        "severity_icon": risk["severity_icon"],
        "recommendation": risk["recommendation"],
        "climate_conditions": _build_climate_snapshot(climate_data),
        "analyzed_at": analysis.timestamp,
    }


# ── ENDPOINTS ───────────────────────────────────────────────────


@router.post(
    "/analyze/climate",
    response_model=ClimateRiskResponse,
    summary="🌍 Análise completa de riscos climáticos (ODS 13)",
    description=(
        "Análise completa de 6 eventos climáticos extremos alinhados ao ODS 13 da ONU. "
        "Informe o nome de uma cidade ou região e receba: Inundação, Seca, Onda de Calor, "
        "Tempestade, Deslizamento e Incêndio Florestal."
    ),
)
async def analyze_climate_risks(data: RegionInput, db: AsyncSession = Depends(get_db)):
    geo = await Geocoder.geocode(data.region)
    if geo is None:
        raise HTTPException(
            status_code=404,
            detail=f"Região '{data.region}' não encontrada. Tente: 'Recife, PE, Brasil'.",
        )
    return await _run_full_analysis(geo["latitude"], geo["longitude"], geo["display_name"], db)


@router.post(
    "/analyze/climate/coordinates",
    response_model=ClimateRiskResponse,
    summary="🌍 Análise completa por coordenadas (ODS 13)",
    description="Mesmo que /analyze/climate, mas usando latitude e longitude.",
)
async def analyze_climate_risks_by_coords(
    location: LocationInput, db: AsyncSession = Depends(get_db)
):
    region_name = f"Lat {location.latitude}, Lon {location.longitude}"
    return await _run_full_analysis(location.latitude, location.longitude, region_name, db)


@router.post(
    "/analyze/flood",
    response_model=RiskResponse,
    summary="Analisar risco de inundação",
    description="Análise individual de risco de inundação para uma região.",
)
async def analyze_flood_risk(data: RegionInput, db: AsyncSession = Depends(get_db)):
    geo = await Geocoder.geocode(data.region)
    if geo is None:
        raise HTTPException(status_code=404, detail=f"Região '{data.region}' não encontrada.")
    return await _run_single_analysis("flood", geo["latitude"], geo["longitude"], geo["display_name"], db)

from typing import Optional
from app.models.schemas import RegionSubscribe
from app.core.database import RegionSubscription
from sqlalchemy.exc import IntegrityError

@router.post(
    "/monitor/subscribe",
    summary="🔔 Assinar região para Monitoramento Autônomo",
    description="Cadastra uma cidade no radar do sistema. O AETHER passará a escanear a região silenciosamente em busca de anomalias climáticas."
)
async def subscribe_region(data: RegionSubscribe, db: AsyncSession = Depends(get_db)):
    geo = await Geocoder.geocode(data.region)
    if not geo:
        raise HTTPException(status_code=404, detail="Região não encontrada.")
        
    sub = RegionSubscription(
        region_name=geo["display_name"],
        latitude=geo["latitude"],
        longitude=geo["longitude"]
    )
    db.add(sub)
    try:
        await db.commit()
        return {"status": "success", "message": f"Região '{geo['display_name']}' adicionada ao monitoramento autônomo."}
    except IntegrityError:
        await db.rollback()
        return {"status": "info", "message": "Região já está sendo monitorada."}

@router.get(
    "/analyze/history",
    summary="📊 Histórico de Risco de uma Região",
    description="Retorna as avaliações passadas para construção de gráficos de curva de risco."
)
async def get_region_history(region: str, limit: int = 10, db: AsyncSession = Depends(get_db)):
    geo = await Geocoder.geocode(region)
    if not geo:
        raise HTTPException(status_code=404, detail="Região não encontrada.")
        
    result = await db.execute(
        select(RiskAnalysis)
        .filter(RiskAnalysis.region_name == geo["display_name"])
        .order_by(RiskAnalysis.timestamp.desc())
        .limit(limit)
    )
    analyses = result.scalars().all()
    
    return [
        {
            "id": a.id,
            "overall_severity": a.severity,
            "temperature_c": a.temperature_c,
            "precipitation_mm": a.precipitation_mm,
            "timestamp": a.timestamp,
        }
        for a in analyses
    ]


@router.get(
    "/alerts/active",
    response_model=list[AlertResponse],
    summary="🚨 Listar alertas ativos (com filtros)",
    description="Retorna alertas de risco climático ativos. Aceita filtros por região e severidade.",
)
async def get_active_alerts(
    region: Optional[str] = None, 
    severity: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Alert).filter(Alert.is_active == True)
    
    if region:
        query = query.filter(Alert.region_name.ilike(f"%{region}%"))
    if severity:
        query = query.filter(Alert.severity == severity.upper())
        
    result = await db.execute(query.order_by(Alert.created_at.desc()))
    return result.scalars().all()

# ================================================================
# 📡 ROTAS DO ECOSSISTEMA EDGE (NÓ IoT / ESP32)
# ================================================================
from datetime import datetime

@router.post(
    "/iot/clima",
    summary="📡 Receber dados nominais do Edge (ESP32)",
    description="Rota exclusiva para recebimento de JSON dos sensores físicos IoT baseados no ODS 13."
)
async def receber_dados_edge(dados: LeituraIoT):
    hora = datetime.now().strftime("%H:%M:%S")
    
    # Este print vai aparecer brilhando no terminal do VS Code durante o Pitch!
    print(f"\n[{hora}] 🟢 [ESTAÇÃO: {dados.id_estacao}] Temperatura: {dados.temperatura}°C | Umidade: {dados.umidade_ar}%")
    
    return {"status": "sucesso", "mensagem": "Dados do Node IoT sincronizados com a Nuvem"}


@router.post(
    "/iot/urgencia",
    summary="🚨 Receber alerta crítico do Edge (ESP32)",
    description="Rota de contingência (Banda Estreita) para receber texto puro quando há risco extremo na borda."
)
async def receber_alerta_borda(request: Request):
    payload = await request.body()
    alerta = payload.decode("utf-8")
    hora = datetime.now().strftime("%H:%M:%S")
    
    # Este print vermelho sinaliza a ativação da Inteligência Local (US03)
    print(f"\n[{hora}] 🔴 [EMERGÊNCIA EDGE] ALERTA TÁTICO: {alerta}")
    
    return {"status": "alerta_registrado"}