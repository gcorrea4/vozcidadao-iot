// Execute este programa passando o caminho do módulo compilado conforme TESTES.md.
const { readFileSync } = require("node:fs");
const assert = require("node:assert/strict");

async function verificar() {
  let entrada, linha = "", agora = 0, memoria;
  const saidas = new Map(), modos = new Map();
  const ambiente = {
    inicio_serial: baud => assert.equal(baud, 9600),
    configurar: (p, m) => modos.set(p, m),
    escrever: (p, v) => saidas.set(p, v),
    adc: p => { assert.equal(p, 14); return entrada.adc; },
    sensor: () => entrada.t,
    aguardar: ms => { assert.equal(ms, 2500); agora += ms; },
    tempo: () => agora,
    texto: endereco => {
      const bytes = new Uint8Array(memoria.buffer);
      const fim = bytes.indexOf(0, endereco);
      assert.ok(fim >= endereco);
      linha += new TextDecoder().decode(bytes.subarray(endereco, fim));
    },
    inteiro: v => { linha += v; },
    decimal: (v, casas) => { linha += v.toFixed(casas); }
  };
  const { instance } = await WebAssembly.instantiate(readFileSync(process.argv[2]), { env: ambiente });
  memoria = instance.exports.memory;
  instance.exports.iniciar();
  assert.deepEqual([...modos], [[8,1],[9,1],[10,1]]);
  const casos = [
    [24,280,"normal",8,false,false], [36,280,"calor",9,true,false],
    [24,853,"baixa_luz",9,false,true], [36,853,"alerta_duplo",10,true,true],
    [30,599,"normal",8,false,false], [30,600,"baixa_luz",9,false,true],
    [30.1,599,"calor",9,true,false], [NaN,853,"falha_dht",10,null,true],
    [24,280,"normal",8,false,false]
  ];
  for (const [t,adc,estado,pino,calor,escuro] of casos) {
    entrada = {t,adc};
    linha = "";
    instance.exports.amostrar();
    assert.deepEqual(JSON.parse(linha), {estacao:"praca-01",uptime_ms:agora,
      temperatura_c:Number.isNaN(t) ? null : t,ldr_adc:adc,calor,escuro,estado});
    for (const p of [8,9,10]) assert.equal(saidas.get(p), Number(p === pino));
    console.log("OK", "T="+t, "ADC="+adc, estado, "D"+pino);
  }
}
verificar().catch(erro => { console.error(erro); process.exitCode = 1; });
