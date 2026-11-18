#include "../../firmware/monitor/monitor.ino"

extern "C" void iniciar() { setup(); }
extern "C" void amostrar() { loop(); }
