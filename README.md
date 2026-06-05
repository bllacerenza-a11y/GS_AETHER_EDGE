# 🌍 AETHER - Plataforma de Inteligência Climática (Cloud & Edge)

Este repositório centraliza todo o ecossistema **AETHER**, uma plataforma inteligente focada na **ODS 13 da ONU** (Ação contra a Mudança Global do Clima). O sistema atua de forma autônoma para prever, monitorar e alertar sobre catástrofes climáticas, utilizando uma arquitetura dividida em Inteligência de Nuvem e Inteligência de Borda.

---

## 🏗️ Arquitetura do Sistema

O ecossistema AETHER foi desenhado para ser resiliente e escalável, dividindo as responsabilidades em dois pilares principais:

### ☁️ 1. O Cérebro na Nuvem (Backend Python / FastAPI)
* **Inteligência:** Utiliza 6 heurísticas matemáticas avançadas (Inundação, Seca, Onda de Calor, Tempestade, Deslizamento e Incêndio) cruzando dados da API Open-Meteo.
* **Autonomia:** Possui um *Background Worker* (`scheduler.py`) que varre as cidades cadastradas silenciosamente e dispara alertas no banco de dados sem intervenção humana.
* **Tecnologias:** FastAPI, AsyncIO, SQLite, Pydantic e Algoritmos de Trend Analysis (Sem dependência de APIs de IA pagas).

### 🔌 2. O Sistema Nervoso na Borda (Node IoT Edge / ESP32)
* **Sensores de Campo:** Microcontrolador ESP32 equipado com sensor DHT22 simulado via Wokwi para coletar dados físicos no local.
* **Resiliência (Edge Computing):** O hardware possui uma Máquina de Estados própria. Se houver falha de rede ou detecção de calor extremo, o ESP32 corta o processamento, aciona um alerta tático (LED Vermelho) localmente e salva os dados em um *Buffer FIFO* offline.
* **Data Recovery:** Assim que a rede é restabelecida, o Edge Node descarrega os pacotes perdidos para a nuvem de forma ordenada.

```text
AETHER_PROJECT/
├── app/                      # ☁️ BACKEND (Lógica em Python)
│   ├── api/                  # Rotas e Endpoints do FastAPI (v1_router)
│   ├── ai/                   # Preditor de riscos utilizando XGBoost
│   ├── core/                 # Configurações e modelos do Banco de Dados
│   ├── data_pipeline/        # Cliente de dados climáticos Open-Meteo
│   ├── geospatial/           # Processamento e Geometria (Shapely/GeoPandas)
│   ├── models/               # Schemas de validação de dados (Pydantic)
│   ├── services/             # Motor de regras e engine de alertas
│   └── main.py               # Ponto de entrada da API e Worker Assíncrono
├── ai_models/                # Modelos de IA pré-treinados
├── scripts/                  # Scripts utilitários e de inicialização
├── sketch.ino                # 🔌 BORDA (C++) - Firmware principal do ESP32/Wokwi
├── requirements.txt          # Lista de dependências do Python
├── Dockerfile                # Instruções de Containerização do Backend
└── docker-compose.yml        # Orquestração de serviços em nuvem
```

---

# 🌍 AETHER - Plataforma de Inteligência Climática (Cloud & Edge)

**Global Solution - ODS 13 (Ação Contra a Mudança Global do Clima)**

## 👥 Equipe de Desenvolvimento
* **Bruno Bastos** - RM: 569434
* **Arthur Sgarbi** - RM: 569774
* **Pedro Oliveira** - RM: 572468

---

Este repositório centraliza todo o ecossistema **AETHER**, uma plataforma inteligente focada em atuar de forma autônoma para prever, monitorar e alertar sobre catástrofes climáticas, utilizando uma arquitetura dividida em Inteligência de Nuvem e Inteligência de Borda.

---

## 🏗️ Arquitetura do Sistema e Unificação de Código

Para garantir a máxima fidelidade no desenvolvimento, simulação e avaliação do ecossistema, os componentes de **Nuvem (Backend Python)** e **Borda (Firmware ESP32)** foram unificados neste repositório. 

Essa abordagem permite que a **ponte de comunicação** entre o mundo físico (sensores) e o digital (algoritmos de IA) seja testada de ponta a ponta em ambiente de desenvolvimento. O backend atua como o servidor central de telemetria e o simulador de hardware consome rotas dinâmicas, espelhando exatamente o comportamento de um ambiente de produção real.

### Passo 1: Ligando a API (Nuvem)
Você pode rodar o backend localmente ou enviá-lo para a nuvem (como o **Render**):
1. Instale as dependências: `pip install -r requirements.txt`
2. Inicie o servidor: `uvicorn app.


```text
┌─────────────────────────────────┐          Túnel de Rede         ┌──────────────────────────────────┐
│       BORDA (Wokwi/ESP32)       │ ─────────────────────────────> │       NUVEM (FastAPI/Python)     │
│  - Monitoramento local DHT22    │   Encaminhamento de Porta HTTP  │  - Processamento Assíncrono      │
│  - Tomada de Decisão em Borda   │   (localhost.run / ssh tunnel)  │  - Banco de Dados SQLite         │
│  - Buffer FIFO de Contingência  │                                │  - Heurísticas e IA (XGBoost)    │
└─────────────────────────────────┘                                └──────────────────────────────────┘
