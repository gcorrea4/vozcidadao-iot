#include <DHT.h>

// Limiares didáticos. No módulo LDR do Wokwi, escurecer aumenta o ADC.
constexpr float LIMITE_CALOR_C = 30.0;
constexpr int LIMITE_ESCURO_ADC = 600;
constexpr unsigned long INTERVALO_MS = 2500;
constexpr byte PINO_DHT = 2;
constexpr byte VERDE = 8;
constexpr byte AMARELO = 9;
constexpr byte VERMELHO = 10;
DHT dht(PINO_DHT, DHT22);

void setup() {
  Serial.begin(9600);
  pinMode(VERDE, OUTPUT);
  pinMode(AMARELO, OUTPUT);
  pinMode(VERMELHO, OUTPUT);
  dht.begin();
}

void loop() {
  delay(INTERVALO_MS);
  const float temperatura = dht.readTemperature();
  const int luz = analogRead(A0);
  const bool falha = isnan(temperatura);
  const bool calor = !falha && temperatura > LIMITE_CALOR_C;
  const bool escuro = luz >= LIMITE_ESCURO_ADC;
  const bool alertaDuplo = calor && escuro;

  digitalWrite(VERDE, !falha && !calor && !escuro);
  digitalWrite(AMARELO, !falha && (calor != escuro));
  digitalWrite(VERMELHO, falha || alertaDuplo);

  // Uma linha por amostra. null preserva a distinção entre falha e 0 °C.
  Serial.print(F("{\"estacao\":\"praca-01\",\"uptime_ms\":"));
  Serial.print(millis());
  Serial.print(F(",\"temperatura_c\":"));
  if (falha) Serial.print(F("null"));
  else Serial.print(temperatura, 1);
  Serial.print(F(",\"ldr_adc\":"));
  Serial.print(luz);
  Serial.print(F(",\"calor\":"));
  if (falha) Serial.print(F("null"));
  else Serial.print(calor ? F("true") : F("false"));
  Serial.print(F(",\"escuro\":"));
  Serial.print(escuro ? F("true") : F("false"));
  Serial.print(F(",\"estado\":\""));
  if (falha) Serial.print(F("falha_dht"));
  else if (alertaDuplo) Serial.print(F("alerta_duplo"));
  else if (calor) Serial.print(F("calor"));
  else if (escuro) Serial.print(F("baixa_luz"));
  else Serial.print(F("normal"));
  Serial.println(F("\"}"));
}
