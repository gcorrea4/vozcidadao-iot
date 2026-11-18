"""Encaminha uma linha JSON por POST. Entrada serial ao vivo ou arquivo para replay."""
import argparse
import json
import sys
from contextlib import nullcontext
from urllib.error import URLError
from urllib.request import Request, urlopen

URL = "http://127.0.0.1:8765/api/v1/leituras"


def enviar(linha, url, origem):
    leitura = json.loads(linha)
    if not isinstance(leitura, dict):
        raise ValueError("Objeto JSON esperado")
    leitura["origem"] = origem
    corpo = json.dumps(leitura, allow_nan=False).encode()
    req = Request(url, data=corpo, headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(req, timeout=4) as resposta:
        if resposta.status != 201:
            raise ValueError(f"Resposta inesperada: {resposta.status}")
        return json.load(resposta)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    entrada = parser.add_mutually_exclusive_group(required=True)
    entrada.add_argument("--serial", help="COM3, /dev/ttyACM0 ou rfc2217://127.0.0.1:4000")
    entrada.add_argument("--arquivo", help="NDJSON salvo do monitor serial, ou - para stdin")
    parser.add_argument("--url", default=URL)
    args = parser.parse_args()
    if args.serial:
        import serial
        fonte = serial.serial_for_url(args.serial, baudrate=9600, timeout=None)
    else:
        fonte = nullcontext(sys.stdin.buffer) if args.arquivo == "-" else open(args.arquivo, "rb")
    erros = 0
    with fonte as linhas:
        for linha in linhas:
            if not linha.strip():
                continue
            try:
                resposta = enviar(linha, args.url, "serial" if args.serial else "replay")
                print("201", resposta["estado"], resposta["recebido_em"], flush=True)
            except (ValueError, OSError, URLError) as erro:
                erros += 1
                print(f"Leitura descartada: {erro}", file=sys.stderr, flush=True)
    return int(erros != 0)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
