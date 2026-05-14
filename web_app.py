#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================
  YT Downloader Web - Versao para Navegador / Mobile
  Servidor local com Flask + yt-dlp (API nativa)
  Acesse pelo celular na mesma rede Wi-Fi
==========================================================
"""

from flask import Flask, render_template, request, send_file, jsonify
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import subprocess
import shutil
import sys
import os
import uuid
import threading
import time

try:
    import yt_dlp
except ImportError:
    print("ERRO: yt-dlp nao instalado. Execute: pip install yt-dlp")
    sys.exit(1)

app = Flask(__name__)

# Pasta temporaria para downloads
DOWNLOAD_DIR = Path(__file__).parent / "downloads_temp"
DOWNLOAD_DIR.mkdir(exist_ok=True)

# Dicionario para rastrear status dos downloads
downloads_status = {}

# Pool de threads global para limitar downloads simultaneos
MAX_DOWNLOADS_SIMULTANEOS = 3
download_pool = ThreadPoolExecutor(max_workers=MAX_DOWNLOADS_SIMULTANEOS)


def limpar_arquivos_antigos():
    """Remove subpastas temporarias com mais de 30 minutos."""
    while True:
        try:
            agora = time.time()
            for item in DOWNLOAD_DIR.iterdir():
                if item.is_dir() and (agora - item.stat().st_mtime) > 1800:
                    shutil.rmtree(item, ignore_errors=True)
                    # Limpar a entrada correspondente do dicionario de status
                    download_id = item.name
                    downloads_status.pop(download_id, None)
        except Exception:
            pass
        time.sleep(300)  # Verificar a cada 5 minutos


# Iniciar limpeza em background
thread_limpeza = threading.Thread(target=limpar_arquivos_antigos, daemon=True)
thread_limpeza.start()


def verificar_ffmpeg():
    """Verifica se o ffmpeg esta instalado."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


FFMPEG_DISPONIVEL = verificar_ffmpeg()


@app.route("/")
def index():
    """Pagina principal."""
    return render_template("index.html", ffmpeg=FFMPEG_DISPONIVEL)


@app.route("/baixar", methods=["POST"])
def baixar():
    """Endpoint para iniciar um download."""
    data = request.get_json()
    url = data.get("url", "").strip()
    formato = data.get("formato", "mp3").strip()

    if not url:
        return jsonify({"erro": "URL vazia"}), 400

    if not ("youtube.com" in url or "youtu.be" in url or "music.youtube" in url):
        return jsonify({"erro": "URL invalida. Cole um link do YouTube."}), 400

    # Gerar ID unico para este download
    download_id = str(uuid.uuid4())[:8]
    pasta_download = DOWNLOAD_DIR / download_id
    pasta_download.mkdir(exist_ok=True)

    downloads_status[download_id] = {
        "status": "baixando",
        "progresso": "Iniciando download...",
        "percentual": 0,
        "arquivo": None,
        "erro": None
    }

    def _processar():
        # Hook de progresso para atualizar o status em tempo real
        def _progress_hook(d):
            if d["status"] == "downloading":
                percent_str = d.get("_percent_str", "").strip()
                speed_str = d.get("_speed_str", "").strip()
                eta_str = d.get("_eta_str", "").strip()
                # Extrair o valor numerico da porcentagem
                try:
                    pct_val = float(d.get("downloaded_bytes", 0)) / float(d.get("total_bytes", 1)) * 100
                except (ValueError, ZeroDivisionError, TypeError):
                    pct_val = 0
                downloads_status[download_id]["progresso"] = "{} a {} (ETA: {})".format(
                    percent_str, speed_str, eta_str
                )
                downloads_status[download_id]["percentual"] = min(pct_val, 99)
            elif d["status"] == "finished":
                downloads_status[download_id]["progresso"] = "Processando arquivo..."
                downloads_status[download_id]["percentual"] = 99

        ydl_opts = {
            "outtmpl": str(pasta_download / "%(title)s.%(ext)s"),
            "noplaylist": True,
            "no_overwrites": True,
            "restrictfilenames": True,
            "encoding": "utf-8",
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [_progress_hook],
        }

        if formato == "mp3":
            if FFMPEG_DISPONIVEL:
                ydl_opts["format"] = "bestaudio/best"
                ydl_opts["postprocessors"] = [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "0",
                }]
            else:
                ydl_opts["format"] = "bestaudio[ext=m4a]/bestaudio"
        else:
            if FFMPEG_DISPONIVEL:
                ydl_opts["format"] = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
                ydl_opts["merge_output_format"] = "mp4"
            else:
                ydl_opts["format"] = "best[ext=mp4]/best"

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            # Encontrar o arquivo baixado
            arquivos = list(pasta_download.iterdir())
            if arquivos:
                downloads_status[download_id]["status"] = "concluido"
                downloads_status[download_id]["arquivo"] = arquivos[0].name
                downloads_status[download_id]["progresso"] = "Download concluido!"
                downloads_status[download_id]["percentual"] = 100
            else:
                downloads_status[download_id]["status"] = "erro"
                downloads_status[download_id]["erro"] = "Arquivo nao encontrado apos download."

        except yt_dlp.utils.DownloadError as e:
            downloads_status[download_id]["status"] = "erro"
            downloads_status[download_id]["erro"] = str(e)[:200]
        except Exception as e:
            downloads_status[download_id]["status"] = "erro"
            downloads_status[download_id]["erro"] = str(e)[:200]

    # Submeter ao pool em vez de criar thread solta
    download_pool.submit(_processar)

    return jsonify({"id": download_id, "mensagem": "Download iniciado!"})


@app.route("/status/<download_id>")
def status(download_id):
    """Verifica o status de um download."""
    if download_id not in downloads_status:
        return jsonify({"erro": "Download nao encontrado"}), 404
    return jsonify(downloads_status[download_id])


@app.route("/arquivo/<download_id>")
def arquivo(download_id):
    """Serve o arquivo baixado para o usuario."""
    if download_id not in downloads_status:
        return jsonify({"erro": "Download nao encontrado"}), 404

    info = downloads_status[download_id]
    if info["status"] != "concluido" or not info["arquivo"]:
        return jsonify({"erro": "Arquivo ainda nao esta pronto"}), 400

    caminho = DOWNLOAD_DIR / download_id / info["arquivo"]
    if not caminho.exists():
        return jsonify({"erro": "Arquivo nao encontrado no servidor"}), 404

    return send_file(
        str(caminho),
        as_attachment=True,
        download_name=info["arquivo"]
    )


if __name__ == "__main__":
    import socket

    # Descobrir IP local para acesso via celular
    hostname = socket.gethostname()
    try:
        ip_local = socket.gethostbyname(hostname)
    except Exception:
        ip_local = "127.0.0.1"

    print("")
    print("=" * 55)
    print("  YT Downloader Web v2.0 - Servidor Iniciado!")
    print("=" * 55)
    print("  Acesse no PC:      http://localhost:5000")
    print("  Acesse no Celular:  http://{}:5000".format(ip_local))
    print("  ffmpeg:            {}".format("Disponivel" if FFMPEG_DISPONIVEL else "Nao encontrado"))
    print("  Max downloads:     {}".format(MAX_DOWNLOADS_SIMULTANEOS))
    print("  Engine:            yt-dlp API nativa")
    print("=" * 55)
    print("  Para parar o servidor, pressione Ctrl+C")
    print("=" * 55)
    print("")

    app.run(host="0.0.0.0", port=5000, debug=False)
