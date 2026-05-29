# AETHER Backend MVP 🌍🤖

Geospatial Artificial Intelligence platform for climate risk prediction.
Built with **FastAPI**, **XGBoost**, **GeoPandas**, and **Open-Meteo** real-time data.

---

## Architecture

```
GS_AETHER/
├── app/
│   ├── api/              # FastAPI routes (v1_router)
│   ├── ai/               # XGBoost risk predictor
│   ├── core/             # Config & database models
│   ├── data_pipeline/    # Open-Meteo climate data client
│   ├── geospatial/       # Shapely/GeoPandas processing
│   ├── models/           # Pydantic schemas
│   ├── services/         # Alert engine
│   └── main.py           # FastAPI application entry point
├── ai_models/            # Trained ML models (.joblib)
├── scripts/              # Bootstrap & utility scripts
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env
```

## Local Setup

### 1. Clone & enter directory
```bash
git clone <repo-url>
cd GS_AETHER
```

### 2. Create virtual environment
```bash
python -m venv venv
```

### 3. Activate virtual environment
```bash
# Windows
.\venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

### 4. Install dependencies
```bash
pip install -r requirements.txt
```

### 5. Bootstrap the AI model (first time only)
```bash
python scripts/bootstrap_ai.py
```

### 6. Run the server
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/` | Health check |
| `POST` | `/api/v1/analyze/flood` | Analyze flood risk for a location |
| `GET`  | `/api/v1/alerts/active` | List all active alerts |

### Example: Analyze Flood Risk
```bash
curl -X POST http://localhost:8000/api/v1/analyze/flood \
  -H "Content-Type: application/json" \
  -d '{"latitude": -23.55, "longitude": -46.63}'
```

---

## Docker

```bash
docker-compose up --build
```

---

## Tech Stack

- **FastAPI** — High-performance async web framework
- **XGBoost** — Gradient boosted trees for risk prediction
- **GeoPandas / Shapely** — Geospatial data processing
- **Open-Meteo API** — Free real-time climate data
- **SQLAlchemy** — ORM with SQLite (MVP) / PostgreSQL-ready
- **Pydantic** — Data validation and serialization