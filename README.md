# VBAN Sender

Aplicação desktop para capturar áudio e transmitir via protocolo [VBAN](https://www.vb-audio.com/Voicemeeter/VBANProtocol_Specifications.pdf) (UDP) para outro PC na rede — por exemplo, um **PC gamer** enviando **áudio do desktop** e **microfone** em faixas separadas para um **PC de streaming** com OBS e o plugin VBAN.

## Requisitos (Linux — desenvolvimento)

```bash
sudo apt install python3-venv python3-tk libportaudio2
```

`python3-tk` é obrigatório — o CustomTkinter usa Tkinter, que não vem via pip.

## Executar em desenvolvimento

```bash
cd vban-sender
./scripts/install.sh
source .venv/bin/activate
python app.py
```

Os pacotes VBAN são montados em [`core/vban_packet.py`](core/vban_packet.py) (compatível com o protocolo [pyVBAN](https://pypi.org/project/pyVBAN/); o pacote PyPI não é necessário para rodar o app).

As configurações são salvas em `~/.config/vban-sender/config.json` (dev) ou ao lado do `.exe` (Windows).

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

## Build do executável Windows (`VBANSender.exe`)

O build no GitHub Actions roda **somente ao publicar uma versão** (push de tag `v*`, ex.: `v1.0.0`).

```bash
git tag v1.0.0
git push origin v1.0.0
```

Na aba **Actions**, baixe o artefato `VBANSender-windows` com o `VBANSender.exe`.

### Atalho a partir do Linux

Com o [GitHub CLI](https://cli.github.com/) autenticado:

```bash
./scripts/build-windows.sh v1.0.0
```

O script envia a tag, aguarda o workflow e baixa `dist/VBANSender.exe`.

No Windows, o executável salva `config.json` na mesma pasta do `.exe`.

## Estrutura do projeto

```
app.py              # Entry point
core/emitter.py     # Captura (sounddevice) e envio VBAN
core/vban_packet.py # Montagem de pacotes VBAN
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
