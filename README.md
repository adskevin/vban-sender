# VBAN Emitter

Aplicação desktop para capturar áudio e transmitir via protocolo [VBAN](https://www.vb-audio.com/Voicemeeter/VBANProtocol_Specifications.pdf) (UDP) para outro PC na rede — por exemplo, um **PC gamer** enviando **áudio do desktop** e **microfone** em faixas separadas para um **PC de streaming** com OBS e o plugin VBAN.

## Requisitos (Linux — desenvolvimento)

```bash
sudo apt install python3-venv python3-tk libportaudio2
```

`python3-tk` é obrigatório — o CustomTkinter usa Tkinter, que não vem via pip.

Opcional (se quiser instalar o pacote `pyVBAN` completo com PyAudio):

```bash
sudo apt install portaudio19-dev
```

## Executar em desenvolvimento

```bash
cd vban-sender
./scripts/install.sh
source .venv/bin/activate
python app.py
```

Ou manualmente (não use `pip install pyVBAN` sozinho — ele tenta compilar **PyAudio**):

```bash
pip install -r requirements.txt
pip install -r requirements-vban.txt --no-deps
```

O projeto usa `pyVBAN` apenas para montar pacotes de áudio. Um stub em `_stubs/pyaudio` evita compilar PyAudio no Linux (a captura é feita com `sounddevice`).

As configurações são salvas em `~/.config/vban-emitter/config.json` (dev) ou ao lado do `.exe` (Windows).

## Uso — duas faixas

O app envia até **dois streams VBAN** na mesma porta UDP, com nomes diferentes:

| Faixa | Conteúdo | Stream padrão |
|-------|----------|---------------|
| **Áudio do desktop** | Som do sistema | `Desktop` |
| **Microfone** | Entrada de voz | `Mic` |

1. Informe o **IPv4** do PC receptor e a **porta UDP** (padrão `6980`).
2. Em cada faixa, marque **Transmitir…**, escolha o **dispositivo** e o **nome do stream**.
3. Clique em **Iniciar** (pelo menos uma faixa deve estar ativa).

### Escolha do dispositivo

- **Linux (desktop):** no combo de desktop, escolha **Monitor of …** (PulseAudio/PipeWire).
- **Windows (desktop):** habilite **Stereo Mix** nas configurações de som, ou selecione um dispositivo com “loopback” / “Stereo Mix” na lista. Se a lista mostrar todas as entradas, use a dica exibida na interface.

- **Microfone:** lista apenas entradas que não são monitor/loopback.

No PC receptor (OBS), adicione **duas fontes VBAN** — uma para cada nome de stream (`Desktop`, `Mic`, ou os nomes que você configurou).

## Build do executável Windows (.exe)

O PyInstaller não gera um `.exe` Windows confiável rodando nativamente no Linux. O build oficial usa **GitHub Actions** em `windows-latest`.

### Disparar o build a partir do Linux

Com o [GitHub CLI](https://cli.github.com/) autenticado:

```bash
./scripts/build-windows.sh
```

O script dispara o workflow, aguarda a conclusão e baixa `dist/VBANEmitter.exe`.

### Alternativa manual

Faça push para `main` ou `master`, ou dispare o workflow **Build Windows EXE** no GitHub. Baixe o artefato `VBANEmitter-windows` na aba Actions.

No Windows, o executável salva `config.json` na mesma pasta do `.exe`.

## Estrutura do projeto

```
app.py              # Entry point
core/emitter.py     # Captura (sounddevice) e envio VBAN (pyVBAN)
core/session.py     # Orquestra múltiplas faixas
core/devices.py     # Listagem de dispositivos desktop/mic
core/config.py      # Persistência JSON
ui/main_window.py   # Interface CustomTkinter
build.spec          # PyInstaller (Windows)
```

## Referências

- [Especificação VBAN](https://www.vb-audio.com/Voicemeeter/VBANProtocol_Specifications.pdf)
- [pyVBAN](https://pypi.org/project/pyVBAN/)
- [sounddevice](https://python-sounddevice.readthedocs.io/)
- [VBAN Audio para OBS](https://obsproject.com/forum/resources/vban-audio.1623/)
