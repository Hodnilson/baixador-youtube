# YT Downloader - Baixador de Musicas e Videos do YouTube

Aplicativo para baixar musicas (MP3) e videos (MP4) do YouTube. Disponivel em 3 versoes:

## Versoes Disponiveis

| Versao | Arquivo | Para quem |
|--------|---------|-----------|
| Desktop (Windows/Linux) | `yt_downloader.py` | Quem quer um app com janela no PC |
| Web (Celular/PC) | `web_app.py` | Quem quer acessar pelo navegador do celular |

---

## 1. Versao Desktop (Executavel)

### Funcionalidades
- Download em lote (varios links de uma vez)
- Download paralelo (3 simultaneos)
- Interface Dark Mode premium
- Log em tempo real

### Como usar
Baixe o executavel na aba **Releases** ou rode via Python:
```bash
pip install yt-dlp
python yt_downloader.py
```

---

## 2. Versao Web (Celular / Mobile)

### Funcionalidades
- Acesse de qualquer celular pelo navegador
- Design responsivo (funciona em qualquer tela)
- Barra de progresso animada
- Botao para salvar o arquivo direto no celular

### Como usar
```bash
pip install flask yt-dlp
python web_app.py
```
Depois acesse no navegador:
- No PC: `http://localhost:5000`
- No Celular: `http://SEU-IP:5000` (o IP aparece no terminal quando voce roda o comando)

---

## Requisitos
- Python 3.7+
- yt-dlp (`pip install yt-dlp`)
- Flask (`pip install flask`) - apenas para versao web
- ffmpeg (opcional, necessario para converter para MP3)

### Instalar ffmpeg
```bash
# Linux (Ubuntu/Debian)
sudo apt install -y ffmpeg

# Windows
# Baixe em: https://ffmpeg.org/download.html
```

---
Desenvolvido para facilitar o download de musicas e videos.
