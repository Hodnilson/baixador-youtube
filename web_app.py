#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================
  YT Downloader Web - Versao para Navegador / Mobile
  Servidor local com Flask + yt-dlp
  Acesse pelo celular na mesma rede Wi-Fi
==========================================================
"""

from flask import Flask, render_template, request, send_file, jsonify, after_this_request
from pathlib import Path
import subprocess
import sys
import os
import uuid
import threading
import time
import glob

app = Flask(__name__)

# Pasta temporaria para downloads
DOWNLOAD_DIR = Path(__file__).parent / "downloads_temp"
DOWNLOAD_DIR.mkdir(exist_ok=True)

# Dicionario para rastrear status dos downloads
downloads_status = {}


def limpar_arquivos_antigos():
    """Remove arquivos temporarios com mais de 30 minutos."""
    while True:
        try:
            agora = time.time()
            for arquivo in DOWNLOAD_DIR.iterdir():
                if arquivo.is_file() and (agora - arquivo.stat().st_mtime) > 1800:
                    arquivo.unlink()
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
        "arquivo": None,
        "erro": None
    }

    def _processar():
        cmd = [sys.executable, "-m", "yt_dlp"]

        if formato == "mp3":
            if FFMPEG_DISPONIVEL:
                cmd.extend(["-x", "--audio-format", "mp3", "--audio-quality", "0"])
            else:
                cmd.extend(["-f", "bestaudio[ext=m4a]/bestaudio"])
        else:
            if FFMPEG_DISPONIVEL:
                cmd.extend([
                    "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                    "--merge-output-format", "mp4"
                ])
            else:
                cmd.extend(["-f", "best[ext=mp4]/best"])

        cmd.extend([
            "-o", str(pasta_download / "%(title)s.%(ext)s"),
            "--no-playlist",
            "--no-overwrites",
            "--restrict-filenames",
            "--encoding", "utf-8",
            url
        ])

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace"
            )

            for line in process.stdout:
                line = line.strip()
                if "[download]" in line and "%" in line:
                    downloads_status[download_id]["progresso"] = line[:80]

            process.wait()

            if process.returncode == 0:
                # Encontrar o arquivo baixado
                arquivos = list(pasta_download.iterdir())
                if arquivos:
                    downloads_status[download_id]["status"] = "concluido"
                    downloads_status[download_id]["arquivo"] = arquivos[0].name
                    downloads_status[download_id]["progresso"] = "Download concluido!"
                else:
                    downloads_status[download_id]["status"] = "erro"
                    downloads_status[download_id]["erro"] = "Arquivo nao encontrado apos download."
            else:
                downloads_status[download_id]["status"] = "erro"
                downloads_status[download_id]["erro"] = "Falha no download (codigo {})".format(process.returncode)

        except FileNotFoundError:
            downloads_status[download_id]["status"] = "erro"
            downloads_status[download_id]["erro"] = "yt-dlp nao encontrado. Instale com: pip install yt-dlp"
        except Exception as e:
            downloads_status[download_id]["status"] = "erro"
            downloads_status[download_id]["erro"] = str(e)[:200]

    threading.Thread(target=_processar, daemon=True).start()

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
    print("  YT Downloader Web - Servidor Iniciado!")
    print("=" * 55)
    print("  Acesse no PC:      http://localhost:5000")
    print("  Acesse no Celular:  http://{}:5000".format(ip_local))
    print("  ffmpeg:            {}".format("Disponivel" if FFMPEG_DISPONIVEL else "Nao encontrado"))
    print("=" * 55)
    print("  Para parar o servidor, pressione Ctrl+C")
    print("=" * 55)
    print("")

    app.run(host="0.0.0.0", port=5000, debug=False)
