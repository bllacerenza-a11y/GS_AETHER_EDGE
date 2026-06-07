# 🌍 AETHER - Plataforma de Inteligência Climática (Cloud & Edge)

**Global Solution - ODS 13 (Ação Contra a Mudança Global do Clima)**

## 👥 Equipe de Desenvolvimento
* **Bruno Bastos** - RM: 569434
* **Arthur Sgarbi** - RM: 569774
* **Pedro Oliveira** - RM: 572468

---

## 🔗 Links Importantes (Avaliação)
* **Simulação (Wokwi): https://wokwi.com/projects/465729595873688577
**
---

## 🎯 Objetivo da Solução
O objetivo do AETHER é mitigar o "apagão de dados" durante desastres climáticos (como inundações e incêndios). A solução visa garantir que as equipes de resgate e Defesa Civil continuem recebendo telemetrias críticas do ambiente, mesmo quando a infraestrutura convencional de comunicação (internet/cabos) for destruída, utilizando Inteligência de Borda (Edge Computing) e rotinas de Data Recovery.

## 📖 Descrição do Projeto
Este repositório centraliza todo o ecossistema **AETHER**, uma plataforma inteligente focada em atuar de forma autônoma para prever, monitorar e alertar sobre catástrofes climáticas. A arquitetura é dividida em dois pilares: Inteligência de Nuvem (para processamento de massa de dados e dashboard) e Inteligência de Borda (microcontroladores resilientes em campo).

---

## 🛠️ Componentes Utilizados
* 1x Microcontrolador ESP32
* 1x Sensor de Temperatura e Umidade DHT22
* 1x Slide Switch (Chave deslizante para simular o cabo de rede/internet)
* 1x LED Verde (Indicador de Estado Nominal)
* 1x LED Vermelho (Indicador de Emergência / Falha de Rede)
* Resistores de 220Ω (para os LEDs)
* Jumpers para conexão

## 🔌 Estrutura do Circuito (Pinagem)
A montagem no simulador Wokwi obedece à seguinte estrutura lógica:
* **Sensor DHT22:** Pino de dados conectado à porta digital **D4**.
* **LED Verde:** Conectado à porta digital **D21**.
* **LED Vermelho:** Conectado à porta digital **D19**.
* **Slide Switch (Simulador de Rede):** Pino central conectado à porta digital **D18**. Um polo lateral conectado ao **3V3** (HIGH - Rede ON) e o outro polo ao **GND** (LOW - Rede OFF).

---

## ⚙️ Explicação do Funcionamento (Arquitetura do Sistema)

Para garantir a máxima fidelidade no desenvolvimento, simulação e avaliação do ecossistema, os componentes de **Nuvem (Backend Python)** e **Borda (Firmware ESP32)** foram unificados neste repositório. O backend atua como o servidor central de telemetria e o simulador de hardware consome rotas dinâmicas, espelhando exatamente o comportamento de um ambiente de produção real.

### 1. O Sistema Nervoso na Borda (Node IoT Edge / ESP32)
* **Sensores de Campo:** O ESP32 lê continuamente os dados do DHT22 local.
* **Resiliência (Edge Computing):** O hardware possui uma Máquina de Estados própria. Se houver falha de rede (Slide Switch em LOW) ou detecção de calor extremo (> 40°C), o ESP32 corta o processamento pesado, aciona o LED Vermelho localmente e salva os dados críticos em um **Buffer FIFO** na própria memória (Offline).
* **Data Recovery:** Assim que a rede é restabelecida, o Edge Node descarrega os pacotes perdidos para a nuvem de forma ordenada, garantindo que o histórico nunca seja perdido.

### 2. O Cérebro na Nuvem (Backend Python / FastAPI)
* **Inteligência:** Utiliza modelos preditivos cruzando dados meteorológicos em tempo real.
* **Autonomia:** Possui um *Background Worker* assíncrono que varre as regiões cadastradas silenciosamente e dispara alertas no banco de dados.

---

## 📂 Estrutura do Repositório (Mono-repo)

> 🚨 **ATENÇÃO AVALIADORES: O FOCO PRINCIPAL DESTE PROJETO É O CÓDIGO C++ (`sketch.ino`)** 🚨
> 
> Para fins da disciplina de IoT/Edge Computing, o **coração absoluto deste projeto** é o firmware embarcado contido no arquivo **`sketch.ino`**. 
> Todas as demais pastas de Backend (Python, IA e Banco de Dados) foram construídas como uma **infraestrutura complementar** para provar a integração real do nosso hardware com a nuvem, demonstrando uma aplicação ponta a ponta.

```text

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
AETHER_PROJECT/               # 🚨 CÓDIGO PRINCIPAL (C++) - Firmware de Borda (ESP32/Wokwi) - sketch.ino
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

Todo e qualquer tipo de código além do c++ contido no sketch.ino, é complementar justamente pela integração que o nosso projeto apresenta com o backend de python, integração essa que simularia o envio de dados obtidos através de satélites e aparatos espaciais como starlink, para o arduíno fisico presente em fazendas, lavouras e afins.
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

# 🌍 AETHER - Plataforma de Inteligência Climática (Cloud & Edge)

**Global Solution - ODS 13 (Ação Contra a Mudança Global do Clima)**

## 👥 Equipe de Desenvolvimento
* **Bruno Bastos** - RM: 569434
* **Arthur Sgarbi** - RM: 569774
* **Pedro Oliveira** - RM: 572468

---

## 🔗 Links Importantes (Avaliação)
* **Simulação (Wokwi):** [Cole o link do seu Wokwi público aqui]
* **Vídeo Pitch/Demonstração:** [Cole o link do seu vídeo do YouTube aqui]

---

## 🎯 Objetivo da Solução
O objetivo do AETHER é mitigar o "apagão de dados" durante desastres climáticos (como inundações e incêndios). A solução visa garantir que as equipes de resgate e Defesa Civil continuem recebendo telemetrias críticas do ambiente, mesmo quando a infraestrutura convencional de comunicação (internet/cabos) for destruída, utilizando Inteligência de Borda (Edge Computing) e rotinas de Data Recovery.

## 📖 Descrição do Projeto
Este repositório centraliza todo o ecossistema **AETHER**, uma plataforma inteligente focada em atuar de forma autônoma para prever, monitorar e alertar sobre catástrofes climáticas. A arquitetura é dividida em dois pilares: Inteligência de Nuvem (para processamento de massa de dados e dashboard) e Inteligência de Borda (microcontroladores resilientes em campo).

---

## 🛠️ Componentes Utilizados
* 1x Microcontrolador ESP32
* 1x Sensor de Temperatura e Umidade DHT22
* 1x Slide Switch (Chave deslizante para simular o cabo de rede/internet)
* 1x LED Verde (Indicador de Estado Nominal)
* 1x LED Vermelho (Indicador de Emergência / Falha de Rede)
* Resistores de 220Ω (para os LEDs)
* Jumpers para conexão

## 🔌 Estrutura do Circuito (Pinagem)
A montagem no simulador Wokwi obedece à seguinte estrutura lógica:
* **Sensor DHT22:** Pino de dados conectado à porta digital **D4**.
* **LED Verde:** Conectado à porta digital **D21**.
* **LED Vermelho:** Conectado à porta digital **D19**.
* **Slide Switch (Simulador de Rede):** Pino central conectado à porta digital **D18**. Um polo lateral conectado ao **3V3** (HIGH - Rede ON) e o outro polo ao **GND** (LOW - Rede OFF).

---

## ⚙️ Explicação do Funcionamento (Arquitetura do Sistema)

Para garantir a máxima fidelidade no desenvolvimento, simulação e avaliação do ecossistema, os componentes de **Nuvem (Backend Python)** e **Borda (Firmware ESP32)** foram unificados neste repositório. O backend atua como o servidor central de telemetria e o simulador de hardware consome rotas dinâmicas, espelhando exatamente o comportamento de um ambiente de produção real.

### 1. O Sistema Nervoso na Borda (Node IoT Edge / ESP32)
* **Sensores de Campo:** O ESP32 lê continuamente os dados do DHT22 local.
* **Resiliência (Edge Computing):** O hardware possui uma Máquina de Estados própria. Se houver falha de rede (Slide Switch em LOW) ou detecção de calor extremo (> 40°C), o ESP32 corta o processamento pesado, aciona o LED Vermelho localmente e salva os dados críticos em um **Buffer FIFO** na própria memória (Offline).
* **Data Recovery:** Assim que a rede é restabelecida, o Edge Node descarrega os pacotes perdidos para a nuvem de forma ordenada, garantindo que o histórico nunca seja perdido.

### 2. O Cérebro na Nuvem (Backend Python / FastAPI)
* **Inteligência:** Utiliza modelos preditivos cruzando dados meteorológicos em tempo real.
* **Autonomia:** Possui um *Background Worker* assíncrono que varre as regiões cadastradas silenciosamente e dispara alertas no banco de dados.

---

## 📂 Estrutura do Repositório (Mono-repo)

> 🚨 **ATENÇÃO AVALIADORES: O FOCO PRINCIPAL DESTE PROJETO É O CÓDIGO C++ (`sketch.ino`)** 🚨
> 
> Para fins da disciplina de IoT/Edge Computing, o **coração absoluto deste projeto** é o firmware embarcado contido no arquivo **`sketch.ino`**. 
> Todas as demais pastas de Backend (Python, IA e Banco de Dados) foram construídas como uma **infraestrutura complementar** para provar a integração real do nosso hardware com a nuvem, demonstrando uma aplicação ponta a ponta.

```text
AETHER_PROJECT/
├── sketch.ino                # 🚨 CÓDIGO PRINCIPAL (C++) - Firmware de Borda (ESP32/Wokwi)
│
├── app/                      # ☁️ BACKEND COMPLEMENTAR (Lógica em Python)
│   ├── api/                  # Rotas e Endpoints do FastAPI consumidas pelo C++
│   ├── ai/                   # Preditor de riscos utilizando XGBoost
│   ├── core/                 # Configurações e modelos do Banco de Dados
│   └── main.py               # Ponto de entrada da API e Worker Assíncrono
├── scripts/                  # Scripts utilitários e de inicialização
└── requirements.txt          # Lista de dependências do Python
