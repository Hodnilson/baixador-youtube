# YT Downloader - Baixador de Musicas e Videos do YouTube

Um aplicativo Desktop com interface grafica premium para baixar musicas (MP3) e videos (MP4) do YouTube.

## Funcionalidades

- **Download em Lote:** Cole varios links de uma vez (um por linha) e baixe todos simultaneamente.
- **Download Paralelo:** Ate 3 downloads ao mesmo tempo, sem travar a interface.
- **MP3 ou MP4:** Escolha entre baixar apenas o audio (MP3, qualidade maxima) ou o video completo (MP4).
- **Log em Tempo Real:** Acompanhe o progresso de cada download na tela.
- **Interface Dark Mode:** Visual moderno e premium.
- **Multiplataforma:** Funciona no Windows e Linux.

## Como Usar

### Opcao 1: Executavel (sem instalar nada)
1. Baixe o executavel na aba **Releases** do repositorio.
2. Execute o arquivo e cole os links do YouTube.

### Opcao 2: Rodar pelo Python
1. Instale as dependencias:
```bash
pip install yt-dlp
```
2. Execute o script:
```bash
python yt_downloader.py
```

## Requisitos (apenas para rodar via Python)
- Python 3.7+
- yt-dlp (`pip install yt-dlp`)

## Como Gerar o Executavel
```bash
pip install pyinstaller
pyinstaller --onefile --windowed yt_downloader.py
```

---
Desenvolvido para facilitar o download de musicas e videos.
