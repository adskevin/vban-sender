# VBAN Emitter — Especificação para o Cursor

## Visão Geral

Aplicação desktop Python com GUI para capturar áudio de um dispositivo de entrada e transmiti-lo via protocolo VBAN (UDP) para outro PC na rede local. O caso de uso principal é um **PC gamer** enviando áudio para um **PC de streaming** que recebe via OBS + plugin VBAN.

O app deve ser empacotável como `.exe` standalone via PyInstaller, sem exigir instalação de Python ou dependências no sistema do usuário final.

---

## Stack

| Componente | Biblioteca |
|---|---|
| GUI | `customtkinter` |
| Captura de áudio | `sounddevice` |
| Protocolo VBAN | `pyVBAN` |
| Empacotamento | `PyInstaller` |

---

## Estrutura de Arquivos

```
vban-emitter/
├── app.py                  # Entry point
├── core/
│   └── emitter.py          # Lógica de captura e envio VBAN
├── ui/
│   └── main_window.py      # Janela principal com CustomTkinter
├── requirements.txt
├── build.spec              # Configuração do PyInstaller
└── README.md
```

---

## Funcionalidades

### Interface (main_window.py)

- **Dropdown — Dispositivo de Entrada**: lista todos os dispositivos de entrada de áudio disponíveis no sistema via `sounddevice.query_devices()`. Exibir nome do dispositivo. Selecionar o padrão do sistema por default.
- **Campo — IP do Receptor**: input de texto para o IP do PC que vai receber o stream (ex: `192.168.1.100`). Validar formato IPv4 antes de iniciar.
- **Campo — Nome do Stream**: input de texto, padrão `Stream1`. Usado para identificar o stream no receptor.
- **Campo — Porta UDP**: input numérico, padrão `6980`. Porta UDP utilizada pelo protocolo VBAN.
- **Botão — Iniciar / Parar**: toggle. Ao iniciar, muda para estado "Parar" com cor de destaque. Ao parar, volta ao estado original.
- **Indicador de Status**: label que exibe o estado atual:
  - `Parado` — cinza
  - `Transmitindo para 192.168.x.x...` — verde
  - `Erro: <mensagem>` — vermelho
- **Meter de Volume** (opcional, mas desejável): barra simples mostrando nível RMS do áudio capturado em tempo real, para confirmar que o áudio está sendo capturado.

### Lógica de Emissão (emitter.py)

- Classe `VBANEmitter` com métodos `start()` e `stop()`.
- Usar `sounddevice.InputStream` para capturar áudio do dispositivo selecionado.
- Sample rate: `48000 Hz`, canais: `2` (estéreo), formato: `int16`.
- Enviar pacotes via `pyVBAN` para o IP/porta/stream configurados.
- Rodar em thread separada para não bloquear a GUI.
- Tratar exceções e reportar erros via callback para a UI.

### Persistência de Configuração

- Salvar as configurações (IP, nome do stream, porta, dispositivo selecionado) em um arquivo `config.json` no diretório do executável.
- Carregar automaticamente na inicialização.

---

## Empacotamento (build.spec)

Configurar o PyInstaller para:

- `--onefile`: gerar um único `.exe`
- `--windowed`: sem janela de console
- Incluir explicitamente a DLL do PortAudio (`_sounddevice_data/`) como `--add-data`
- Incluir assets de ícone se houver (`--icon`)
- Nomear o output como `VBANEmitter.exe`

Exemplo de comando de build:
```bash
pyinstaller build.spec
```

O `build.spec` deve ser gerado via:
```bash
pyinstaller --onefile --windowed --name VBANEmitter app.py
```
E então ajustado manualmente para incluir os binários nativos do `sounddevice`.

---

## requirements.txt

```
customtkinter
sounddevice
pyVBAN
pyinstaller
```

---

## Comportamento Esperado

1. Usuário abre o `VBANEmitter.exe`
2. App carrega configurações salvas (se existirem)
3. Usuário seleciona o dispositivo de áudio, preenche IP e clica em **Iniciar**
4. App começa a capturar áudio e enviar via UDP para o receptor
5. Status muda para verde com o IP de destino
6. No PC receptor, o OBS com plugin VBAN já recebe o stream automaticamente
7. Ao clicar **Parar**, a transmissão é encerrada e o status volta para cinza

---

## Notas de Implementação

- O `sounddevice` no Windows usa **WASAPI** por padrão — preferir isso em vez de MME/DirectSound para menor latência.
- O pyVBAN pode não ter tipagem completa; verificar a API de `VBAN_Sender` antes de integrar.
- A thread de emissão deve ser do tipo `daemon=True` para encerrar junto com o processo principal.
- Evitar `time.sleep()` no loop de captura — usar o callback do `sounddevice.InputStream` que já é assíncrono.
- O meter de volume pode ser calculado como RMS do buffer de entrada: `numpy.sqrt(numpy.mean(data**2))`.

---

## Referências

- Protocolo VBAN: https://www.vb-audio.com/Voicemeeter/VBANProtocol_Specifications.pdf
- pyVBAN (PyPI): https://pypi.org/project/pyVBAN/
- sounddevice docs: https://python-sounddevice.readthedocs.io/
- CustomTkinter: https://github.com/TomSchimansky/CustomTkinter
- Plugin VBAN para OBS (receptor): https://obsproject.com/forum/resources/vban-audio.1623/
