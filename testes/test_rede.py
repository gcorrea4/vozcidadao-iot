"""Integração real da ponte, HTTP em loopback e persistência SQLite."""
import json
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from rede.receptor import ROTA, criar_servidor

RAIZ = Path(__file__).resolve().parents[1]


class TesteRede(unittest.TestCase):
    def test_replay_consulta_e_rejeicao(self):
        captura = RAIZ / "evidencias" / "serial-wokwi.ndjson"
        linhas = [json.loads(s) for s in captura.read_text(encoding="utf-8").splitlines()]
        with tempfile.TemporaryDirectory() as temp:
            banco = str(Path(temp) / "ensaio.sqlite3")
            with criar_servidor(0, banco) as api:
                thread = threading.Thread(target=api.serve_forever, daemon=True)
                thread.start()
                url = f"http://127.0.0.1:{api.server_port}{ROTA}"
                try:
                    with self.assertRaises(HTTPError) as vazio:
                        urlopen(url + "/ultima", timeout=3)
                    self.assertEqual(vazio.exception.code, 404)
                    vazio.exception.close()
                    proc = subprocess.run(
                        [sys.executable, str(RAIZ / "rede/ponte.py"), "--arquivo", str(captura), "--url", url],
                        check=True, capture_output=True, text=True, timeout=30,
                    )
                    respostas = [s.split()[:2] for s in proc.stdout.splitlines()]
                    self.assertEqual(respostas, [["201", d["estado"]] for d in linhas])
                    with urlopen(url + "/ultima", timeout=3) as resposta:
                        self.assertEqual(resposta.status, 200)
                        ultima = json.load(resposta)
                    self.assertEqual(ultima.pop("origem"), "replay")
                    self.assertTrue(ultima.pop("recebido_em").endswith("+00:00"))
                    self.assertEqual(ultima, linhas[-1])
                    invalida = Request(url, data=b'{}', headers={"Content-Type": "application/json"})
                    with self.assertRaises(HTTPError) as rejeitada:
                        urlopen(invalida, timeout=3)
                    self.assertEqual(rejeitada.exception.code, 400)
                    rejeitada.exception.close()
                finally:
                    api.shutdown()
                    thread.join()
                    api.db.close()
            with criar_servidor(0, banco) as reaberto:
                try:
                    salvas = [json.loads(r[0]) for r in reaberto.db.execute("SELECT json FROM leituras ORDER BY id")]
                    for d in salvas:
                        self.assertEqual(d.pop("origem"), "replay")
                        d.pop("recebido_em")
                    self.assertEqual(salvas, linhas)
                finally:
                    reaberto.db.close()
