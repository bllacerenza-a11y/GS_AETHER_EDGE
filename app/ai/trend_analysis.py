from typing import List, Dict, Any

class TrendAnalyzer:
    """Analyzes 7-day forecast trends to generate intelligent insights."""

    @staticmethod
    def analyze_temperature_trend(temps: List[float]) -> Dict[str, Any]:
        """Analyzes a 7-day temperature array."""
        if len(temps) < 3:
            return {"status": "stable", "message": "Dados insuficientes para análise de tendência."}
        
        current = temps[0]
        max_future = max(temps[1:])
        min_future = min(temps[1:])
        avg_future = sum(temps[1:]) / len(temps[1:])
        
        if max_future > current + 3.0:
            return {
                "status": "worsening", 
                "message": f"Tendência de forte aquecimento. A temperatura pode atingir {max_future:.1f}°C nos próximos dias."
            }
        elif avg_future < current - 2.0:
            return {
                "status": "improving", 
                "message": f"Tendência de resfriamento. A média dos próximos dias cairá para {avg_future:.1f}°C."
            }
        else:
            return {
                "status": "stable", 
                "message": "As temperaturas devem se manter estáveis ao longo da semana."
            }

    @staticmethod
    def analyze_precipitation_trend(precips: List[float]) -> Dict[str, Any]:
        """Analyzes a 7-day precipitation array."""
        if len(precips) < 3:
            return {"status": "stable", "message": "Dados insuficientes."}
            
        current = precips[0]
        total_future = sum(precips[1:])
        max_daily = max(precips[1:])
        
        if max_daily > 30.0:
            return {
                "status": "worsening",
                "message": f"Alerta de chuvas intensas na previsão (pico de {max_daily:.1f}mm em um único dia)."
            }
        elif current > 10.0 and total_future < 5.0:
            return {
                "status": "improving",
                "message": "A chuva atual deve perder força significativamente nos próximos dias."
            }
        elif total_future == 0.0:
            return {
                "status": "worsening",
                "message": "Nenhuma precipitação prevista para a próxima semana, agravando riscos de seca e incêndio."
            }
        else:
            return {
                "status": "stable",
                "message": "Padrão de chuvas dentro do esperado para os próximos dias."
            }

    @staticmethod
    def generate_overall_insight(climate_data: dict) -> Dict[str, str]:
        """Generates a combined insight based on temperature and precipitation trends."""
        temp_trend = TrendAnalyzer.analyze_temperature_trend(climate_data.get("temp_max_forecast_c", []))
        precip_trend = TrendAnalyzer.analyze_precipitation_trend(climate_data.get("precip_forecast_mm", []))
        
        # Determine overall trend status
        if precip_trend["status"] == "worsening" or temp_trend["status"] == "worsening":
            overall_status = "worsening"
            icon = "📈"
        elif precip_trend["status"] == "improving" and temp_trend["status"] == "improving":
            overall_status = "improving"
            icon = "📉"
        else:
            overall_status = "stable"
            icon = "➡️"
            
        return {
            "trend_status": overall_status,
            "trend_icon": icon,
            "temperature_insight": temp_trend["message"],
            "precipitation_insight": precip_trend["message"],
            "summary": f"{icon} {precip_trend['message']} {temp_trend['message']}"
        }
