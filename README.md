# AETHER Backend MVP 🌍🤖

Plataforma de Inteligência Artificial Geoespacial para previsão de riscos climáticos.
Construída com **FastAPI**, **XGBoost**, **GeoPandas**, e dados em tempo real da **Open-Meteo**.

---

## Arquitetura

```text
GS_AETHER/
├── app/
│   ├── api/              # Rotas FastAPI (v1_router)
│   ├── ai/               # Preditor de riscos XGBoost
│   ├── core/             # Configuração & modelos de banco de dados
│   ├── data_pipeline/    # Cliente de dados climáticos Open-Meteo
│   ├── geospatial/       # Processamento Shapely/GeoPandas
│   ├── models/           # Schemas Pydantic
│   ├── services/         # Motor de alertas (Alert engine)
│   └── main.py           # Ponto de entrada da aplicação FastAPI / Menu Terminal
├── ai_models/            # Modelos de IA treinados (.joblib)
├── scripts/              # Scripts utilitários e de inicialização
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env
```

## Configuração Local

### 1. Clonar & entrar na pasta
```bash
git clone <repo-url>
cd GS_AETHER
```

### 2. Criar ambiente virtual
```bash
python -m venv venv
```

### 3. Ativar o ambiente virtual
```bash
# Windows
.\venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

### 4. Instalar dependências
```bash
pip install -r requirements.txt
```

### 5. Inicializar o modelo de IA (Apenas na primeira vez)
```bash
python scripts/bootstrap_ai.py
```

### 6. Modos de Execução

**A. Menu no Terminal (Modo de Avaliação da Global Solution)**
Execute o script principal diretamente para acessar o menu interativo via terminal (CLI). Este modo foi desenvolvido para demonstrar os conceitos acadêmicos fundamentais de programação (`if-elif-else`, estruturas de repetição, listas e funções) enquanto se integra perfeitamente com os módulos reais de IA.
```bash
python app/main.py
```

**B. Servidor FastAPI (Modo Backend Profissional)**
Você pode iniciar o backend web completo selecionando a Opção 2 no Menu do Terminal, ou rodando diretamente via uvicorn:
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

A API e a interface interativa Swagger estarão disponíveis em `http://127.0.0.1:8000/docs`.

---

## Endpoints da API

| Método | Endpoint | Descrição |
|--------|----------|-------------|
| `GET`  | `/health` | Checagem de saúde (Health check) |
| `POST` | `/api/v1/analyze/flood` | Analisar risco de inundação para um local |
| `GET`  | `/api/v1/alerts/active` | Listar todos os alertas ativos |

### Exemplo: Analisar Risco de Inundação
```bash
curl -X POST http://127.0.0.1:8000/api/v1/analyze/flood \
  -H "Content-Type: application/json" \
  -d '{"latitude": -23.55, "longitude": -46.63}'
```

---

## Docker

```bash
docker-compose up --build
```

---

## Tecnologias Utilizadas (Tech Stack)

- **FastAPI** — Framework web assíncrono de alta performance
- **XGBoost** — Árvores de decisão impulsionadas por gradiente para previsão de riscos
- **GeoPandas / Shapely** — Processamento de dados geoespaciais
- **Open-Meteo API** — Dados climáticos em tempo real (Gratuito)
- **SQLAlchemy** — ORM com SQLite (MVP) / Preparado para PostgreSQL
- **Pydantic** — Validação e serialização de dados