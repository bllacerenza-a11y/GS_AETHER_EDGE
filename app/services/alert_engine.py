from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import Alert
from typing import List, Dict, Any

SEVERITY_PT = {"LOW": "BAIXO", "MOD": "MODERADO", "HIGH": "ALTO", "CRIT": "CRÍTICO"}
SEVERITY_ICON = {"LOW": "🟢", "MOD": "🟡", "HIGH": "🟠", "CRIT": "🔴"}


class AlertEngine:
    @staticmethod
    async def evaluate_and_alert(
        db: AsyncSession,
        analysis_id: int,
        risk_type: str,
        severity: str,
        prob: float,
        region_name: str = "",
    ):
        """Generates an alert if the risk severity is HIGH or CRIT (single risk)."""
        if severity in ["HIGH", "CRIT"]:
            icon = SEVERITY_ICON.get(severity, "⚠️")
            sev_pt = SEVERITY_PT.get(severity, severity)
            region_label = region_name or "região analisada"

            message = (
                f"{icon} ALERTA {sev_pt}: Probabilidade de {prob * 100:.1f}% de "
                f"{risk_type.upper()} detectada em {region_label}. "
                f"Tome precauções imediatas!"
            )
            new_alert = Alert(
                analysis_id=analysis_id,
                region_name=region_name,
                risk_type=risk_type,
                message=message,
                severity=severity,
                is_active=True,
            )
            db.add(new_alert)
            await db.commit()
            return new_alert
        return None

    @staticmethod
    async def evaluate_multi_risk_alerts(
        db: AsyncSession,
        analysis_id: int,
        risks: List[Dict[str, Any]],
        region_name: str = "",
    ) -> List[Alert]:
        """Evaluates all risk results and generates alerts for HIGH/CRIT risks."""
        alerts = []
        region_label = region_name or "região analisada"

        for risk in risks:
            sev_key = risk.get("severity_key", "LOW")
            if sev_key in ["HIGH", "CRIT"]:
                risk_icon = risk.get("risk_icon", "⚠️")
                sev_icon = SEVERITY_ICON.get(sev_key, "⚠️")
                sev_pt = SEVERITY_PT.get(sev_key, sev_key)
                risk_name = risk.get("risk_type", "Desconhecido")
                prob_pct = risk.get("probability_percent", 0)

                message = (
                    f"{risk_icon}{sev_icon} ALERTA {sev_pt} de {risk_name}: "
                    f"Probabilidade de {prob_pct}% em {region_label}. "
                    f"{risk.get('recommendation', 'Tome precauções!')}"
                )
                new_alert = Alert(
                    analysis_id=analysis_id,
                    region_name=region_name,
                    risk_type=risk.get("risk_type_key", "unknown"),
                    message=message,
                    severity=sev_key,
                    is_active=True,
                )
                db.add(new_alert)
                alerts.append(new_alert)

        if alerts:
            await db.commit()
        return alerts