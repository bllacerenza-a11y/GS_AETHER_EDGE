#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include "DHT.h" 

// ==========================================
// ⚙️ CONFIGURAÇÕES DE HARDWARE
// ==========================================
#define DHTPIN 4          
#define DHTTYPE DHT22     
#define LED_VERDE 21      // Indicador de Estado Nominal / Recovery
#define LED_VERMELHO 19   // Indicador de Emergência / Falha de Rede

DHT dht(DHTPIN, DHTTYPE);

// ==========================================
// 🌐 CONFIGURAÇÕES DE REDE E API
// ==========================================
const char* ssid = "Wokwi-GUEST";
const char* password = "";

// ⚠️ ATENÇÃO: Troque pelo link do seu Ngrok ou Render (Mantenha sem a barra / no final)
String serverHost = "https://SEU_LINK_AQUI.ngrok-free.app";

// Endpoints da sua API FastAPI
String endpointClima = serverHost + "/iot/clima";
String endpointUrgencia = serverHost + "/iot/urgencia";

// ==========================================
// 🧠 MÁQUINA DE ESTADOS E BUFFER LÓGICO
// ==========================================
enum EstadoRede { NOMINAL, EMERGENCIA, RECOVERY };
EstadoRede estadoAtual = NOMINAL;

// Estrutura para armazenar dados offline
struct Leituras {
  float temperatura;
  float umidade;
};

const int MAX_BUFFER = 10; // Capacidade de retenção de dados offline
Leituras bufferOffline[MAX_BUFFER];
int itensNoBuffer = 0;

// Limite térmico para disparar alerta crítico (Simulação de Incêndio/Onda de Calor)
const float LIMITE_TEMP_CRITICA = 40.0; 

// Controle de tempo (Evita usar delay() que trava o processador)
unsigned long tempoAnterior = 0;
const long intervaloEnvio = 5000; // Analisa a cada 5 segundos

void setup() {
  Serial.begin(115200);
  
  pinMode(LED_VERDE, OUTPUT);
  pinMode(LED_VERMELHO, OUTPUT);
  
  dht.begin(); 

  Serial.println("\n🚀 Iniciando Nó de Borda AETHER...");
  conectarWiFi();
}

void loop() {
  unsigned long tempoAtual = millis();

  // Executa o ciclo de análise apenas no intervalo definido
  if (tempoAtual - tempoAnterior >= intervaloEnvio) {
    tempoAnterior = tempoAtual;
    
    bool redeConectada = (WiFi.status() == WL_CONNECTED);
    float tempAtual = dht.readTemperature();
    float umidAtual = dht.readHumidity();

    // Trava de segurança: Se o sensor falhar, ignora o ciclo
    if (isnan(tempAtual) || isnan(umidAtual)) {
      Serial.println("⚠️ ERRO FISICO: Falha de leitura no sensor DHT22!");
      return;
    }

    // 🔄 LÓGICA DE TRANSIÇÃO DE ESTADOS
    if (redeConectada && tempAtual <= LIMITE_TEMP_CRITICA) {
      if (estadoAtual == EMERGENCIA) {
        estadoAtual = RECOVERY; // A rede voltou, precisa sincronizar
      } else if (estadoAtual != RECOVERY) {
        estadoAtual = NOMINAL;
      }
    } else {
      estadoAtual = EMERGENCIA; // Caiu a rede ou calor extremo
    }

    // ⚡ EXECUÇÃO DE ACORDO COM O ESTADO ATUAL
    switch (estadoAtual) {
      
      case NOMINAL:
        acionarAtuadores(true, false); // Verde LIGADO, Vermelho DESLIGADO
        Serial.println("\n🟢 [ESTADO 1] NOMINAL - Transmissão de Dados Padrão");
        enviarJSONClima(tempAtual, umidAtual);
        break;

      case EMERGENCIA:
        acionarAtuadores(false, true); // Verde DESLIGADO, Vermelho LIGADO
        Serial.println("\n🔴 [ESTADO 2] EMERGÊNCIA ATIVADA");
        
        if (!redeConectada) {
          Serial.println("❌ Falha de Conexão. Retendo dados na borda...");
          salvarNoBuffer(tempAtual, umidAtual);
        } else if (tempAtual > LIMITE_TEMP_CRITICA) {
          Serial.println("🔥 Alerta de Risco Climático Extremo!");
          enviarAlertaUrgencia(tempAtual, umidAtual);
        }
        break;

      case RECOVERY:
        // Efeito visual piscante para indicar sincronização
        acionarAtuadores(true, false); delay(100); acionarAtuadores(false, false);
        Serial.println("\n🔵 [ESTADO 3] DATA RECOVERY (FIFO) INICIADO");
        
        if (itensNoBuffer > 0) {
          Serial.print("🔄 Sincronizando pacote. Restam: ");
          Serial.println(itensNoBuffer);
          
          // Envia o dado mais antigo do buffer
          if (enviarJSONClima(bufferOffline[itensNoBuffer - 1].temperatura, bufferOffline[itensNoBuffer - 1].umidade)) {
             itensNoBuffer--; // Remove do buffer apenas se o envio for um sucesso
          }
        } else {
          Serial.println("✅ Sincronização concluída. Retornando ao fluxo Nominal.");
          estadoAtual = NOMINAL;
        }
        break;
    }
  }
}

// ==========================================
// 🛠️ FUNÇÕES AUXILIARES
// ==========================================

void conectarWiFi() {
  Serial.print("Conectando à rede Wi-Fi ");
  Serial.print(ssid);
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n✅ Wi-Fi Conectado com sucesso!");
}

void acionarAtuadores(bool verde, bool vermelho) {
  digitalWrite(LED_VERDE, verde ? HIGH : LOW);
  digitalWrite(LED_VERMELHO, vermelho ? HIGH : LOW);
}

void salvarNoBuffer(float t, float u) {
  if (itensNoBuffer < MAX_BUFFER) {
    bufferOffline[itensNoBuffer].temperatura = t;
    bufferOffline[itensNoBuffer].umidade = u;
    itensNoBuffer++;
    Serial.print("💾 Dado salvo no Buffer Local. Ocupação: ");
    Serial.println(String(itensNoBuffer) + "/" + String(MAX_BUFFER));
  } else {
    Serial.println("⚠️ OVERFLOW: Buffer Local CHEIO! O dado mais antigo foi descartado.");
  }
}

// Envia o POST com a formatação exata que o Pydantic do FastAPI exige
bool enviarJSONClima(float t, float u) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(endpointClima);
    http.addHeader("Content-Type", "application/json");

    StaticJsonDocument<200> doc;
    doc["id_estacao"] = "AETHER-NODE-01";
    doc["temperatura"] = t;
    doc["umidade_ar"] = u;

    String requestBody;
    serializeJson(doc, requestBody);

    int httpResponseCode = http.POST(requestBody);
    http.end();

    if (httpResponseCode > 0) {
      Serial.print("📡 Pacote Enviado -> Código HTTP: ");
      Serial.println(httpResponseCode);
      return true;
    } else {
      Serial.print("❌ Erro no envio HTTP: ");
      Serial.println(httpResponseCode);
      return false;
    }
  }
  return false;
}

// Envia um POST de texto simples (Banda Estreita) para a rota de alerta
void enviarAlertaUrgencia(float t, float u) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(endpointUrgencia);
    http.addHeader("Content-Type", "text/plain");

    String mensagem = "PERIGO: Temperatura extrema detectada (" + String(t) + "C). Possivel foco de incendio.";
    
    int httpResponseCode = http.POST(mensagem);
    http.end();
    
    Serial.print("🚨 Alerta Despachado -> Código HTTP: ");
    Serial.println(httpResponseCode);
  }
}
