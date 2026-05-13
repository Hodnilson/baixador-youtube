#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================
  YT Downloader - Baixador de Musicas e Videos do YouTube
  Interface Grafica Premium com Download em Lote
  Compativel com Python 3.7+ / Windows 7/10/11 / Linux
==========================================================
"""

import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import subprocess
import sys
import os
import re


# ---------------------------------------------------------------
# CONFIGURACOES GLOBAIS
# ---------------------------------------------------------------
MAX_DOWNLOADS_SIMULTANEOS = 3
VERSAO = "1.0.0"


# ---------------------------------------------------------------
# FUNCAO DE DOWNLOAD (roda em thread separada)
# ---------------------------------------------------------------
def baixar_midia(url, pasta_destino, formato, log_callback=None, progress_callback=None):
    """
    Baixa um video ou audio do YouTube usando yt-dlp via subprocess.
    Retorna um dicionario com o resultado.
    """
    url = url.strip()
    if not url:
        return {"url": url, "sucesso": False, "erro": "URL vazia"}

    # Validar URL basica
    if not ("youtube.com" in url or "youtu.be" in url):
        return {"url": url, "sucesso": False, "erro": "URL invalida (nao e do YouTube)"}

    # Montar comando yt-dlp
    cmd = [sys.executable, "-m", "yt_dlp"]

    if formato == "mp3":
        cmd.extend([
            "-x",                          # Extrair audio
            "--audio-format", "mp3",       # Converter para MP3
            "--audio-quality", "0",        # Melhor qualidade
            "--embed-thumbnail",           # Embutir capa do video no MP3
        ])
    else:
        cmd.extend([
            "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "--merge-output-format", "mp4",
        ])

    # Opcoes gerais
    cmd.extend([
        "-o", str(Path(pasta_destino) / "%(title)s.%(ext)s"),
        "--no-playlist",              # Nao baixar playlists inteiras
        "--no-overwrites",            # Nao sobrescrever
        "--restrict-filenames",       # Nomes de arquivo seguros
        "--encoding", "utf-8",
        url
    ])

    if log_callback:
        log_callback("  [INICIO] Baixando: {}".format(url[:60]))

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace"
        )

        # Ler a saida linha por linha para mostrar progresso
        for line in process.stdout:
            line = line.strip()
            if line and log_callback:
                # Filtrar apenas linhas relevantes de progresso
                if "[download]" in line or "[ExtractAudio]" in line:
                    log_callback("    {}".format(line[:80]))

        process.wait()

        if process.returncode == 0:
            if log_callback:
                log_callback("  [OK] Concluido: {}".format(url[:60]))
            return {"url": url, "sucesso": True, "erro": None}
        else:
            if log_callback:
                log_callback("  [ERRO] Falha no download: {}".format(url[:60]))
            return {"url": url, "sucesso": False, "erro": "yt-dlp retornou erro (codigo {})".format(process.returncode)}

    except FileNotFoundError:
        msg = "yt-dlp nao encontrado. Instale com: pip install yt-dlp"
        if log_callback:
            log_callback("  [ERRO] {}".format(msg))
        return {"url": url, "sucesso": False, "erro": msg}
    except Exception as e:
        if log_callback:
            log_callback("  [ERRO] {}".format(str(e)[:80]))
        return {"url": url, "sucesso": False, "erro": str(e)}


# ---------------------------------------------------------------
# INTERFACE GRAFICA (GUI)
# ---------------------------------------------------------------
class YTDownloaderApp(tk.Tk):

    # -- Paleta de Cores Dark Mode --
    BG_DARK      = "#0f0f1a"
    BG_PANEL     = "#1a1a2e"
    BG_INPUT     = "#16213e"
    COR_ACCENT   = "#e94560"
    COR_ACCENT2  = "#c73e54"
    COR_VERDE    = "#00d474"
    COR_TEXTO    = "#eaeaea"
    COR_DIM      = "#8892a4"
    COR_BORDA    = "#2a2a4a"
    COR_HEADER   = "#e94560"

    def __init__(self):
        super(YTDownloaderApp, self).__init__()

        self.title("YT Downloader v{}".format(VERSAO))
        self.geometry("700x620")
        self.resizable(False, False)
        self.configure(bg=self.BG_DARK)

        # Centralizar janela
        self.update_idletasks()
        w, h = 700, 620
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry("{}x{}+{}+{}".format(w, h, x, y))

        # Variaveis
        self.pasta_destino = tk.StringVar(value=str(Path.home() / "Downloads"))
        self.formato_var = tk.StringVar(value="mp3")
        self.baixando = False

        self._criar_interface()

    def _criar_interface(self):
        # ========== HEADER ==========
        header = tk.Frame(self, bg=self.COR_HEADER, height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(
            header,
            text="YT Downloader  |  Baixe Musicas e Videos",
            font=("Segoe UI", 14, "bold"),
            bg=self.COR_HEADER,
            fg="white"
        ).pack(expand=True)

        # ========== CORPO PRINCIPAL ==========
        body = tk.Frame(self, bg=self.BG_DARK, padx=20, pady=15)
        body.pack(fill=tk.BOTH, expand=True)

        # -- Secao: Links --
        tk.Label(
            body,
            text="Cole os links do YouTube abaixo (um por linha):",
            font=("Segoe UI", 10),
            bg=self.BG_DARK,
            fg=self.COR_TEXTO,
            anchor=tk.W
        ).pack(fill=tk.X, pady=(0, 5))

        # Caixa de texto para colar links
        frame_links = tk.Frame(body, bg=self.COR_BORDA, bd=1)
        frame_links.pack(fill=tk.X, pady=(0, 12))

        self.txt_links = tk.Text(
            frame_links,
            height=6,
            font=("Consolas", 10),
            bg=self.BG_INPUT,
            fg=self.COR_TEXTO,
            insertbackground=self.COR_TEXTO,
            relief="flat",
            bd=5,
            wrap=tk.WORD,
            selectbackground=self.COR_ACCENT,
            selectforeground="white"
        )
        self.txt_links.pack(fill=tk.X)

        # Texto placeholder
        self.txt_links.insert("1.0", "https://www.youtube.com/watch?v=...\nhttps://youtu.be/...")
        self.txt_links.bind("<FocusIn>", self._limpar_placeholder)

        # -- Secao: Opcoes --
        frame_opcoes = tk.Frame(body, bg=self.BG_DARK)
        frame_opcoes.pack(fill=tk.X, pady=(0, 12))

        # Formato
        frame_formato = tk.Frame(frame_opcoes, bg=self.BG_DARK)
        frame_formato.pack(side=tk.LEFT)

        tk.Label(
            frame_formato,
            text="Formato:",
            font=("Segoe UI", 10, "bold"),
            bg=self.BG_DARK,
            fg=self.COR_TEXTO
        ).pack(side=tk.LEFT, padx=(0, 8))

        for texto, valor in [("MP3 (Audio)", "mp3"), ("MP4 (Video)", "mp4")]:
            rb = tk.Radiobutton(
                frame_formato,
                text=texto,
                variable=self.formato_var,
                value=valor,
                font=("Segoe UI", 10),
                bg=self.BG_DARK,
                fg=self.COR_TEXTO,
                selectcolor=self.BG_PANEL,
                activebackground=self.BG_DARK,
                activeforeground=self.COR_ACCENT,
                indicatoron=True
            )
            rb.pack(side=tk.LEFT, padx=(0, 10))

        # -- Secao: Pasta de destino --
        frame_pasta = tk.Frame(body, bg=self.BG_DARK)
        frame_pasta.pack(fill=tk.X, pady=(0, 12))

        tk.Label(
            frame_pasta,
            text="Salvar em:",
            font=("Segoe UI", 10, "bold"),
            bg=self.BG_DARK,
            fg=self.COR_TEXTO
        ).pack(side=tk.LEFT, padx=(0, 8))

        entry_pasta = tk.Entry(
            frame_pasta,
            textvariable=self.pasta_destino,
            font=("Segoe UI", 9),
            bg=self.BG_INPUT,
            fg=self.COR_TEXTO,
            insertbackground=self.COR_TEXTO,
            relief="flat",
            highlightthickness=1,
            highlightcolor=self.COR_ACCENT,
            highlightbackground=self.COR_BORDA
        )
        entry_pasta.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6, padx=(0, 8))

        btn_pasta = tk.Button(
            frame_pasta,
            text="Alterar",
            font=("Segoe UI", 9, "bold"),
            bg=self.BG_PANEL,
            fg=self.COR_TEXTO,
            activebackground=self.COR_BORDA,
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            command=self._selecionar_pasta
        )
        btn_pasta.pack(side=tk.RIGHT, ipady=4, ipadx=6)

        # -- Secao: Barra de Progresso --
        self.lbl_status = tk.Label(
            body,
            text="Pronto para baixar.",
            font=("Segoe UI", 9),
            bg=self.BG_DARK,
            fg=self.COR_DIM,
            anchor=tk.W
        )
        self.lbl_status.pack(fill=tk.X, pady=(0, 4))

        self.progress_canvas = tk.Canvas(
            body, height=16, bg=self.BG_INPUT,
            highlightthickness=1, highlightbackground=self.COR_BORDA, bd=0
        )
        self.progress_canvas.pack(fill=tk.X, pady=(0, 12))
        self.progress_fill = self.progress_canvas.create_rectangle(
            0, 0, 0, 16, fill=self.COR_ACCENT, width=0
        )

        # -- Secao: Log Visual --
        tk.Label(
            body,
            text="Log de atividade:",
            font=("Segoe UI", 9),
            bg=self.BG_DARK,
            fg=self.COR_DIM,
            anchor=tk.W
        ).pack(fill=tk.X, pady=(0, 4))

        frame_log = tk.Frame(body, bg=self.COR_BORDA, bd=1)
        frame_log.pack(fill=tk.BOTH, expand=True, pady=(0, 12))

        self.log_text = tk.Text(
            frame_log,
            height=8,
            font=("Consolas", 9),
            bg=self.BG_INPUT,
            fg=self.COR_DIM,
            relief="flat",
            bd=5,
            state=tk.DISABLED,
            wrap=tk.WORD
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # -- Secao: Botoes de Acao --
        frame_botoes = tk.Frame(body, bg=self.BG_DARK)
        frame_botoes.pack(fill=tk.X)

        self.btn_limpar = tk.Button(
            frame_botoes,
            text="Limpar Tudo",
            font=("Segoe UI", 10),
            bg=self.BG_PANEL,
            fg=self.COR_TEXTO,
            activebackground=self.COR_BORDA,
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            command=self._limpar_tudo
        )
        self.btn_limpar.pack(side=tk.LEFT, ipady=8, ipadx=15)

        self.btn_baixar = tk.Button(
            frame_botoes,
            text="Baixar Tudo",
            font=("Segoe UI", 12, "bold"),
            bg=self.COR_ACCENT,
            fg="white",
            activebackground=self.COR_ACCENT2,
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            command=self._iniciar_downloads
        )
        self.btn_baixar.pack(side=tk.RIGHT, fill=tk.X, expand=True, ipady=8, padx=(10, 0))

    # ---------------------------------------------------------------
    # METODOS AUXILIARES
    # ---------------------------------------------------------------
    def _limpar_placeholder(self, event=None):
        """Remove o texto placeholder quando o usuario clica na caixa."""
        conteudo = self.txt_links.get("1.0", tk.END).strip()
        if "youtube.com/watch?v=..." in conteudo:
            self.txt_links.delete("1.0", tk.END)

    def _log(self, mensagem):
        """Adiciona uma linha ao log visual (thread-safe via after)."""
        def _inserir():
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, mensagem + "\n")
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        self.after(0, _inserir)

    def _set_progress(self, atual, total):
        """Atualiza a barra de progresso."""
        def _atualizar():
            self.progress_canvas.update_idletasks()
            largura = self.progress_canvas.winfo_width()
            if total > 0:
                pct = atual / total
            else:
                pct = 0
            fill_w = int(pct * largura)
            cor = self.COR_VERDE if atual == total else self.COR_ACCENT
            self.progress_canvas.coords(self.progress_fill, 0, 0, fill_w, 16)
            self.progress_canvas.itemconfig(self.progress_fill, fill=cor)
            self.lbl_status.config(
                text="Baixando {} de {} ...".format(atual, total) if atual < total
                else "Concluido! {} downloads finalizados.".format(total),
                fg=self.COR_VERDE if atual == total else self.COR_TEXTO
            )
        self.after(0, _atualizar)

    def _selecionar_pasta(self):
        """Abre o dialogo para selecionar pasta de destino."""
        pasta = filedialog.askdirectory(
            title="Selecione a pasta de destino",
            initialdir=self.pasta_destino.get()
        )
        if pasta:
            self.pasta_destino.set(pasta)

    def _limpar_tudo(self):
        """Limpa links, log e reseta a barra."""
        if self.baixando:
            messagebox.showwarning("Aguarde", "Ha downloads em andamento. Aguarde finalizar.")
            return
        self.txt_links.delete("1.0", tk.END)
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state=tk.DISABLED)
        self._set_progress(0, 1)
        self.lbl_status.config(text="Pronto para baixar.", fg=self.COR_DIM)

    def _iniciar_downloads(self):
        """Coleta os links e inicia o download em lote."""
        if self.baixando:
            messagebox.showwarning("Aguarde", "Ja ha downloads em andamento.")
            return

        # Coletar links
        conteudo = self.txt_links.get("1.0", tk.END).strip()
        if not conteudo or "youtube.com/watch?v=..." in conteudo:
            messagebox.showwarning("Atencao", "Cole pelo menos um link do YouTube na caixa de texto.")
            return

        links = [l.strip() for l in conteudo.splitlines() if l.strip()]
        if not links:
            messagebox.showwarning("Atencao", "Nenhum link valido encontrado.")
            return

        # Validar pasta
        pasta = self.pasta_destino.get()
        if not pasta or not Path(pasta).exists():
            messagebox.showerror("Erro", "A pasta de destino nao existe.\nSelecione uma pasta valida.")
            return

        formato = self.formato_var.get()
        total = len(links)

        self.baixando = True
        self.btn_baixar.config(state=tk.DISABLED)
        self.btn_limpar.config(state=tk.DISABLED)

        # Limpar log
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state=tk.DISABLED)

        self._log("=" * 50)
        self._log("  Iniciando download de {} arquivo(s)".format(total))
        self._log("  Formato: {}  |  Pasta: {}".format(formato.upper(), pasta))
        self._log("=" * 50)

        def _processar_lote():
            concluidos = 0
            erros = 0

            with ThreadPoolExecutor(max_workers=MAX_DOWNLOADS_SIMULTANEOS) as executor:
                futures = {}
                for link in links:
                    future = executor.submit(
                        baixar_midia,
                        url=link,
                        pasta_destino=pasta,
                        formato=formato,
                        log_callback=self._log
                    )
                    futures[future] = link

                for future in as_completed(futures):
                    resultado = future.result()
                    concluidos += 1

                    if resultado["sucesso"]:
                        self._log("  [PRONTO] {}/{}".format(concluidos, total))
                    else:
                        erros += 1
                        self._log("  [FALHA] {} - {}".format(
                            resultado["url"][:40],
                            resultado.get("erro", "Erro desconhecido")
                        ))

                    self._set_progress(concluidos, total)

            # Relatorio final
            self._log("")
            self._log("=" * 50)
            self._log("  RELATORIO FINAL")
            self._log("  Total: {}  |  Sucesso: {}  |  Erros: {}".format(
                total, total - erros, erros
            ))
            self._log("=" * 50)

            def _finalizar():
                self.baixando = False
                self.btn_baixar.config(state=tk.NORMAL)
                self.btn_limpar.config(state=tk.NORMAL)

                if erros == 0:
                    messagebox.showinfo(
                        "Download Concluido",
                        "{} arquivo(s) baixados com sucesso!\n\nSalvos em:\n{}".format(total, pasta)
                    )
                else:
                    messagebox.showwarning(
                        "Download Concluido com Erros",
                        "Sucesso: {}\nErros: {}\n\nVerifique o log para mais detalhes.".format(
                            total - erros, erros
                        )
                    )

            self.after(0, _finalizar)

        threading.Thread(target=_processar_lote, daemon=True).start()


# ---------------------------------------------------------------
# PONTO DE ENTRADA
# ---------------------------------------------------------------
if __name__ == "__main__":
    try:
        app = YTDownloaderApp()
        app.mainloop()
    except Exception as e:
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "Erro Fatal",
                "Erro ao iniciar o programa:\n{}".format(str(e))
            )
        except Exception:
            pass
        sys.exit(1)
