"""Receptor de bancada. Executar com Python 3.10 ou superior."""
import argparse
import json
import math
import sqlite3
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer

ROTA = "/api/v1/leituras"
ESTACAO = "praca-01"


def validar(dado):
    if not isinstance(dado, dict) or dado.get("estacao") != ESTACAO:
        raise ValueError("Estação desconhecida")
    for chave, teto in (("uptime_ms", 2**32 - 1), ("ldr_adc", 1023)):
        valor = dado.get(chave)
        if type(valor) is not int or not 0 <= valor <= teto:
            raise ValueError(chave)
    escuro = dado.get("escuro")
    if type(escuro) is not bool:
        raise ValueError("escuro")
    temp, calor = dado["temperatura_c"], dado["calor"]
    if temp is None:
        if calor is not None:
            raise ValueError("calor requer temperatura")
        estado = "falha_dht"
    else:
        if type(temp) not in (int, float) or not -40 <= temp <= 80 or not math.isfinite(temp):
            raise ValueError("temperatura_c")
        if type(calor) is not bool:
            raise ValueError("calor")
        estado = ("alerta_duplo" if escuro else "calor") if calor else ("baixa_luz" if escuro else "normal")
    if dado.get("estado") != estado:
        raise ValueError("Estado incompatível com as flags")
    if dado.get("origem") not in ("serial", "replay"):
        raise ValueError("Origem desconhecida")
    campos = ("estacao", "uptime_ms", "temperatura_c", "ldr_adc", "calor", "escuro", "estado", "origem")
    return {campo: dado[campo] for campo in campos}


class API(BaseHTTPRequestHandler):
    def resposta(self, status, dado):
        corpo = json.dumps(dado, ensure_ascii=False, allow_nan=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(corpo)

    def do_POST(self):
        if self.path != ROTA:
            return self.resposta(404, {"erro": "Rota desconhecida"})
        if self.headers.get_content_type() != "application/json":
            return self.resposta(415, {"erro": "Envie application/json"})
        try:
            tamanho = int(self.headers.get("Content-Length", "0"))
            if not 0 < tamanho <= 2048:
                return self.resposta(413, {"erro": "Envie de 1 a 2048 bytes"})
            leitura = validar(json.loads(self.rfile.read(tamanho)))
        except (ValueError, KeyError, TypeError):
            return self.resposta(400, {"erro": "Leitura inválida"})
        leitura["recebido_em"] = datetime.now(timezone.utc).isoformat()
        db = self.server.db
        with db:
            db.execute("INSERT INTO leituras (json) VALUES (?)", (json.dumps(leitura),))
        self.resposta(201, leitura)

    def do_GET(self):
        if self.path != ROTA + "/ultima":
            return self.resposta(404, {"erro": "Rota desconhecida"})
        linha = self.server.db.execute("SELECT json FROM leituras ORDER BY id DESC LIMIT 1").fetchone()
        if linha is None:
            return self.resposta(404, {"erro": "Nenhuma leitura recebida"})
        self.resposta(200, json.loads(linha[0]))


def criar_servidor(porta, banco):
    servidor = HTTPServer(("127.0.0.1", porta), API)
    servidor.db = sqlite3.connect(banco, check_same_thread=False)
    with servidor.db:
        servidor.db.execute("CREATE TABLE IF NOT EXISTS leituras (id INTEGER PRIMARY KEY, json TEXT NOT NULL)")
    return servidor


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--porta", type=int, default=8765)
    parser.add_argument("--banco", default="leituras.sqlite3")
    args = parser.parse_args()
    with criar_servidor(args.porta, args.banco) as api:
        print(f"Última leitura em http://127.0.0.1:{api.server_port}{ROTA}/ultima", flush=True)
        try:
            api.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            api.db.close()
