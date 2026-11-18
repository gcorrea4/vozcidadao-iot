# Ensaios do VozCidadã Monitor

Ensaios realizados em 18/11/2026. Foram usados o circuito Wokwi, o próprio sketch compilado para um ambiente de teste com entradas controladas e um receptor HTTP em loopback. As medidas do simulador representam situações demonstrativas.

## Sensores, classificação e LEDs

Abra [o circuito](https://wokwi.com/projects/481002576769421313), inicie a simulação e ajuste os componentes pelos controles do DHT22 e do módulo LDR. Aguarde pelo menos uma nova linha por ajuste. Nos testes de fronteira, a entrada de luz é especificada diretamente como contagem ADC.

| Caso e entrada | Esperado | Observado |
| --- | --- | --- |
| 24 °C e 400 lux | Verde, normal | Wokwi: 24,0 °C, ADC 280, verde e `normal`. [Captura](evidencias/01-normal.jpg) |
| 36 °C e 400 lux | Amarelo, apenas calor | Wokwi: 36,0 °C, ADC 280, amarelo e `calor`. [Captura](evidencias/02-calor.jpg) |
| 36 °C e 10 lux | Vermelho, calor e baixa luz | Wokwi: 36,0 °C, ADC 853, vermelho e `alerta_duplo`. [Captura](evidencias/03-alerta-duplo.jpg) |
| 24 °C e ADC 853, correspondente ao escurecimento observado | Amarelo, apenas baixa luz | Ensaio do sketch com entrada controlada: `baixa_luz`, apenas D9 ativo |
| 30 °C e ADC 599 | Verde no limite superior de temperatura | Ensaio do sketch: `normal`, D8 |
| 30 °C e ADC 600 | Amarelo no limiar inclusivo de escuridão | Ensaio do sketch: `baixa_luz`, D9 |
| 30,1 °C e ADC 599 | Amarelo por calor isolado | Ensaio do sketch: `calor`, D9 |
| Falha de leitura do DHT e ADC 853 | Vermelho, temperatura e calor nulos, escuridão válida | Ensaio do sketch com retorno NaN: `falha_dht`, D10. JSON conferido |
| Retorno a 24 °C e ADC 280 depois da falha | Verde e leitura válida na amostra seguinte | Ensaio do sketch: `normal`, D8 |

O [extrato serial](evidencias/serial-wokwi.ndjson) contém seis amostras efetivamente capturadas em três execuções do Wokwi. Os quatro primeiros registros pertencem à mesma execução. Seus intervalos foram 2.565, 2.566 e 2.566 ms. Os dois últimos registros vêm de execuções reiniciadas com novos ajustes; cada boot tem seu próprio contador.

### Repetir os nove casos do sketch

O ensaio compila o mesmo `.ino` do protótipo para WebAssembly. O adaptador em `testes/host` substitui as entradas do DHT e do ADC e observa pinos e serial. Ele verifica os sete campos JSON, a exclusividade do LED ativo e o tempo de espera solicitado pelo sketch. A temporização elétrica do DHT é exercitada pelo circuito Wokwi. O adaptador pertence exclusivamente aos testes.

Com Clang, o vinculador `wasm-ld` e Node.js, execute na raiz. Crie a pasta `build` caso ela ainda não exista.

```shell
clang++ --target=wasm32 -O1 -nostdlib -Itestes/host -Wl,--no-entry,--allow-undefined,--export=iniciar,--export=amostrar,--export-memory testes/host/ensaio.cpp -o build/ensaio.wasm
node testes/host/verificar.cjs build/ensaio.wasm
```

[Saída dos nove casos](evidencias/teste-firmware.txt)

## Comunicação

Execute `python -m unittest discover -s testes -v` na raiz. O teste inicia o receptor em porta TCP livre no endereço 127.0.0.1 e executa a ponte como processo separado. A ponte lê a captura do Wokwi. O teste confere as respostas, reabre o banco e compara as seis linhas armazenadas com o extrato original.

| Entrada | Esperado | Observado |
| --- | --- | --- |
| GET antes da primeira amostra | 404 | 404 |
| Seis linhas NDJSON válidas via ponte | Seis respostas 201 e seis registros com origem replay | Seis respostas 201 e seis registros equivalentes aos originais |
| GET após a sexta linha | 200 e último estado `alerta_duplo` | 200, 36 °C, ADC 853, uptime 20.493 ms e horário de recepção em UTC |
| POST com objeto vazio | 400, nenhuma inserção | 400 e banco com as seis amostras anteriores |
| Fechar e reabrir o banco temporário | Seis leituras preservadas em ordem | Comparação integral aprovada |

[Log HTTP do ensaio](evidencias/teste-http.txt)

O transporte HTTP foi executado com dados de simulação reproduzidos de um arquivo. A conexão USB física, o encaminhamento serial RFC2217 ao vivo e a consulta por um celular via Wi-Fi não foram medidos.

## Apresentação presencial

Comece pelo relato do morador e pela mudança de cor ao escurecer ou aquecer a estação. Em seguida, acompanhe a mesma amostra do JSON serial até a consulta HTTP. Mostre o horário de recepção e o valor de `origem`. Para discutir uma falha, explique como a equipe distinguiria uma leitura inválida, um atraso de comunicação e um alerta ambiental. O histórico apoia a investigação do bairro e a vistoria determina a causa.
