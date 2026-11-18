// Interface de ensaio para compilar o mesmo .ino em WebAssembly.
#pragma once
using byte = unsigned char;
constexpr byte DHT22 = 22, A0 = 14, OUTPUT = 1;
#define F(texto) texto
#define isnan(x) __builtin_isnan(x)

extern "C" {
void inicio_serial(unsigned long baud);
void configurar(byte pino, byte modo);
void escrever(byte pino, byte valor);
int adc(byte pino);
float sensor();
void aguardar(unsigned long ms);
unsigned long tempo();
void texto(const char *s);
void inteiro(unsigned long v);
void decimal(float v, int casas);
}

class DHT {
public:
  constexpr DHT(byte, byte) {}
  void begin() {}
  float readTemperature() { return sensor(); }
};
struct Porta {
  void begin(unsigned long baud) { inicio_serial(baud); }
  void print(const char *s) { texto(s); }
  void print(unsigned long v) { inteiro(v); }
  void print(int v) { inteiro(v); }
  void print(float v, int casas) { decimal(v, casas); }
  void println(const char *s) { texto(s); texto("\n"); }
};
static Porta Serial;
inline void pinMode(byte p, byte m) { configurar(p, m); }
inline void digitalWrite(byte p, byte v) { escrever(p, v); }
inline int analogRead(byte p) { return adc(p); }
inline void delay(unsigned long ms) { aguardar(ms); }
inline unsigned long millis() { return tempo(); }
