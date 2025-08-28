import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import webbrowser
import subprocess
from multiprocessing import freeze_support
import contextlib

# Importa yt_dlp se disponível
try:
    import yt_dlp
except ImportError:
    yt_dlp = None


# -------------------------
# Helper: resource_path
# -------------------------
def resource_path(relative_path):
    """
    Retorna o caminho absoluto do recurso, funcionando tanto no .py quanto no .exe (PyInstaller).
    """
    try:
        # PyInstaller cria essa variável apontando para a pasta temporária
        base_path = sys._MEIPASS
    except Exception:
        # Quando executando a partir do .py:
        if "__file__" in globals():
            base_path = os.path.abspath(os.path.dirname(__file__))
        else:
            base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# -------------------------
# Helper: abrir pasta (cross-platform)
# -------------------------
def open_folder(path):
    """Abre a pasta no explorador de arquivos (Windows: os.startfile)."""
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    try:
        if sys.platform.startswith("win"):
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.call(["open", path])
        else:
            # linux / outros
            try:
                subprocess.call(["xdg-open", path])
            except Exception:
                webbrowser.open(path)
    except Exception:
        # fallback para webbrowser se tudo mais falhar
        webbrowser.open(path)


# -------------------------
# Writer para redirecionar stdout/stderr do demucs para o log do Tkinter
# -------------------------
class GuiStreamWriter:
    def __init__(self, log_callback):
        self.log_callback = log_callback
        self._buffer = ""

    def write(self, data):
        if not data:
            return
        # Algumas libs escrevem em blocos; dividir em linhas
        self._buffer += data
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            text = line.rstrip()
            if text:
                self.log_callback(text)

    def flush(self):
        if self._buffer:
            text = self._buffer.rstrip()
            if text:
                self.log_callback(text)
            self._buffer = ""


# -------------------------
# Tela Inicial
# -------------------------
class TelaInicial:
    def __init__(self, master):
        self.master = master
        self.master.title("PlayAlongs")
        self.master.geometry("650x250")
        self.master.resizable(False, False)

        self.pasta_saida = os.path.join(os.path.expanduser("~"), "Downloads", "separated")

        # Aplica ícone (sem quebrar se não existir)
        try:
            self.master.iconbitmap(resource_path("icon.ico"))
        except Exception:
            pass

        # ---- MenuBar ----
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)

        # Menu Downloads
        menubar.add_command(label="Downloads", command=self.abrir_meus_downloads)

        # Menu Utilitários
        menu_util = tk.Menu(menubar, tearoff=0)
        menu_util.add_command(label="Download do YouTube", command=self.abrir_download_youtube)
        menu_util.add_command(label="Abrir Pasta de Saída", command=self.abrir_pasta_saida)  # Adicionado
        menubar.add_cascade(label="Utilitários", menu=menu_util)

        # ---- Conteúdo da tela inicial ----
        self.frame_principal = tk.Frame(master, padx=30, pady=20)
        self.frame_principal.pack(expand=True, fill=tk.BOTH)

        titulo = tk.Label(
            self.frame_principal,
            text="🎵 PlayAlongs",
            font=("Segoe UI", 24, "bold"),
            fg="#2c3e50"
        )
        titulo.pack(pady=(0, 25))

        # Frame para selecionar arquivo local
        frame_local = tk.Frame(self.frame_principal)
        frame_local.pack(fill=tk.X)

        label_local = tk.Label(frame_local, text="Selecione um arquivo de áudio local para separar:", font=("Segoe UI", 12))
        label_local.pack(anchor="w")

        self.btn_abrir_separador = tk.Button(
            frame_local,
            text="📂 Selecionar Arquivo Local",
            font=("Segoe UI", 12, "bold"),
            bg="#27ae60",
            fg="white",
            activebackground="#2ecc71",
            cursor="hand2",
            command=self.abrir_separador_sem_download
        )
        self.btn_abrir_separador.pack(pady=10, fill=tk.X)

    # ---------- Funções do menubar ----------
    def abrir_meus_downloads(self):
        janela_downloads = tk.Toplevel(self.master)
        janela_downloads.title("Meus Downloads")
        janela_downloads.geometry("500x300")
        janela_downloads.resizable(False, False)
        try:
            janela_downloads.iconbitmap(resource_path("icon.ico"))
        except Exception:
            pass

        frame = tk.Frame(janela_downloads, padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)

        lista_box = tk.Listbox(frame, width=60)
        lista_box.pack(pady=10, fill=tk.BOTH, expand=True)

        pasta_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
        if not os.path.exists(pasta_downloads):
            os.makedirs(pasta_downloads, exist_ok=True)

        arquivos = [f for f in os.listdir(pasta_downloads) if f.lower().endswith(".mp3")]
        if not arquivos:
            lista_box.insert(tk.END, "Nenhum arquivo encontrado.")
        else:
            for f in arquivos:
                lista_box.insert(tk.END, f)

        def selecionar_arquivo():
            selecionado = lista_box.get(tk.ACTIVE)
            if selecionado and not selecionado.startswith("Nenhum"):
                caminho = os.path.join(pasta_downloads, selecionado)
                # Abre o separador já com o arquivo selecionado
                self.master.withdraw()
                top = tk.Toplevel(self.master)
                try:
                    top.iconbitmap(resource_path("icon.ico"))
                except Exception:
                    pass
                AplicativoSeparador(top, arquivo_inicial=caminho)
                janela_downloads.destroy()

        btn_frame = tk.Frame(janela_downloads)
        btn_frame.pack(pady=10)

        btn_selecionar = tk.Button(btn_frame, text="Selecionar", width=12, command=selecionar_arquivo)
        btn_selecionar.pack(side=tk.LEFT, padx=5)

        btn_cancelar = tk.Button(btn_frame, text="Cancelar", width=12, command=janela_downloads.destroy)
        btn_cancelar.pack(side=tk.LEFT, padx=5)

    def abrir_pasta_saida(self):
        if self.pasta_saida and os.path.exists(self.pasta_saida):
            try:
                open_folder(self.pasta_saida)
            except Exception as e:
                messagebox.showwarning("Aviso", f"Erro ao abrir a pasta: {e}")
        else:
            messagebox.showwarning("Aviso", "A pasta de saída ainda não foi gerada.")

    def abrir_download_youtube(self):
        top = tk.Toplevel(self.master)
        try:
            top.iconbitmap(resource_path("icon.ico"))
        except Exception:
            pass
        TelaDownloadYoutube(top)

    def abrir_separador_sem_download(self):
        self.master.withdraw()
        top = tk.Toplevel(self.master)
        try:
            top.iconbitmap(resource_path("icon.ico"))
        except Exception:
            pass
        AplicativoSeparador(top)


# -------------------------
# Tela de Download do YouTube
# -------------------------
class TelaDownloadYoutube:
    def __init__(self, master):
        self.master = master
        self.master.title("Download do YouTube")
        self.master.geometry("600x300")
        self.master.resizable(False, False)
        try:
            self.master.iconbitmap(resource_path("icon.ico"))
        except Exception:
            pass

        frame = tk.Frame(master, padx=20, pady=20)
        frame.pack(expand=True, fill=tk.BOTH)

        label_link = tk.Label(frame, text="Cole o link da música no YouTube:", font=("Segoe UI", 12))
        label_link.pack(anchor="w")

        self.entry_link = tk.Entry(frame, font=("Segoe UI", 11), width=60)
        self.entry_link.pack(pady=5, fill=tk.X)

        # opção de formato (MP3 ou WAV)
        self.formato_var = tk.StringVar(value="MP3")
        formato_frame = tk.Frame(frame)
        formato_frame.pack(anchor="w", pady=(4, 8))
        tk.Label(formato_frame, text="Formato:").pack(side=tk.LEFT)
        tk.Radiobutton(formato_frame, text="MP3", variable=self.formato_var, value="MP3").pack(side=tk.LEFT, padx=6)
        tk.Radiobutton(formato_frame, text="WAV", variable=self.formato_var, value="WAV").pack(side=tk.LEFT, padx=6)

        self.btn_baixar = tk.Button(
            frame,
            text="▶️ Baixar",
            font=("Segoe UI", 12, "bold"),
            bg="#2980b9",
            fg="white",
            activebackground="#3498db",
            cursor="hand2",
            command=self.baixar_musica
        )
        self.btn_baixar.pack(pady=(5, 0), fill=tk.X)

        self.log_download = scrolledtext.ScrolledText(
            frame,
            height=6,
            font=("Segoe UI", 10),
            state=tk.DISABLED,
            bg="#f0f0f0"
        )
        self.log_download.pack(fill=tk.BOTH, pady=(10, 0), expand=True)

    def log_download_insert(self, texto):
        self.log_download.config(state=tk.NORMAL)
        self.log_download.insert(tk.END, texto + "\n")
        self.log_download.see(tk.END)
        self.log_download.config(state=tk.DISABLED)

    def baixar_musica(self):
        link = self.entry_link.get().strip()
        if not link:
            messagebox.showwarning("Aviso", "Por favor, cole um link do YouTube.")
            return

        if yt_dlp is None:
            messagebox.showerror("Erro", "Biblioteca yt_dlp não está instalada.")
            return

        # Pega a pasta de Downloads do usuário
        pasta_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
        os.makedirs(pasta_downloads, exist_ok=True)

        formato = self.formato_var.get().upper()

        def progress_hook(d):
            status = d.get("status")
            if status == 'downloading':
                percent = d.get('_percent_str', '').strip()
                speed = d.get('_speed_str', '').strip()
                eta = d.get('_eta_str', '').strip()
                msg = f"Baixando: {percent} | Velocidade: {speed} | ETA: {eta}"
                self.log_download.after(0, lambda m=msg: self.log_download_insert(m))
            elif status == 'finished':
                self.log_download.after(0, lambda: self.log_download_insert("Download concluído, convertendo..."))

        postprocessor = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
        # Se o usuário escolheu WAV, deixamos arquivo sem converter para mp3 (ou convertemos para wav se preferir)
        if formato == "WAV":
            # saída em wav via ffmpeg
            postprocessor = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192',
            }]

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(pasta_downloads, '%(title)s.%(ext)s'),
            'postprocessors': postprocessor,
            'quiet': True,
            'no_warnings': True,
            'progress_hooks': [progress_hook]
        }

        def baixar():
            try:
                self.log_download.after(0, lambda: self.log_download_insert("[INFO] Iniciando download..."))
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([link])
                self.log_download.after(0, lambda: self.log_download_insert("[SUCESSO] Arquivo salvo em Downloads!"))
            except Exception as e:
                self.log_download.after(0, lambda e=e: self.log_download_insert(f"[ERRO] Falha: {e}"))

        threading.Thread(target=baixar, daemon=True).start()


# -------------------------
# Aplicativo Separador
# -------------------------
class AplicativoSeparador:
    def __init__(self, master, arquivo_inicial=None):
        self.master = master
        self.master.title("Separador de Áudio (Demucs)")
        self.master.geometry("800x520")
        self.master.resizable(False, False)

        try:
            self.master.iconbitmap(resource_path("icon.ico"))
        except Exception:
            pass

        self.arquivo_inicial = arquivo_inicial
        self.pasta_saida = os.path.join(os.path.expanduser("~"), "Downloads", "separated")
        self.processando = False

        self.setup_gui()

    def setup_gui(self):
        # Frame principal
        self.frame = tk.Frame(self.master, padx=20, pady=20)
        self.frame.pack(expand=True, fill=tk.BOTH)

        # Linha de seleção de arquivo
        frame_arquivo = tk.Frame(self.frame)
        frame_arquivo.pack(pady=10, fill=tk.X)

        self.entry_arquivo = tk.Entry(frame_arquivo, width=65, font=("Arial", 11))
        self.entry_arquivo.pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)

        if self.arquivo_inicial and os.path.exists(self.arquivo_inicial):
            self.entry_arquivo.insert(0, self.arquivo_inicial)

        self.btn_escolher = tk.Button(frame_arquivo, text="Escolher Arquivo", width=15,
                                      command=self.escolher_arquivo)
        self.btn_escolher.pack(side=tk.LEFT)

        # Botões ação
        frame_botoes = tk.Frame(self.frame)
        frame_botoes.pack(fill=tk.X, pady=5)

        self.btn_separar = tk.Button(frame_botoes, text="Separar Áudio", width=20, height=2,
                                     bg="#4CAF50", fg="white", command=self.separar_audio_thread)
        self.btn_separar.pack(side=tk.LEFT)

        self.btn_abrir_pasta = tk.Button(frame_botoes, text="Abrir Pasta de Saída", width=20,
                                         command=self.abrir_pasta_saida)
        self.btn_abrir_pasta.pack(side=tk.RIGHT)
        self.btn_abrir_pasta.pack_forget()  # oculto até terminar separação

        # Log
        self.log_text = scrolledtext.ScrolledText(self.frame, width=95, height=22)
        self.log_text.pack(pady=10, fill=tk.BOTH, expand=True)

        # Menu
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)

        menubar.add_command(label="Início", command=self.voltar_tela_inicial)
        menubar.add_command(label="Downloads", command=self.abrir_meus_downloads)

        self.formato_var = tk.StringVar(value="MP3")
        menu_formato = tk.Menu(menubar, tearoff=0)
        menu_formato.add_radiobutton(label="MP3", variable=self.formato_var, value="MP3")
        menu_formato.add_radiobutton(label="WAV", variable=self.formato_var, value="WAV")
        menubar.add_cascade(label="Formato", menu=menu_formato)

        self.modelo_var = tk.StringVar(value="htdemucs")
        menu_modelo = tk.Menu(menubar, tearoff=0)
        menu_modelo.add_radiobutton(label="Preciso (htdemucs)", variable=self.modelo_var, value="htdemucs")
        menu_modelo.add_radiobutton(label="Rápido (mdx_extra_q)", variable=self.modelo_var, value="mdx_extra_q")
        menubar.add_cascade(label="Modelo", menu=menu_modelo)

        # Utilitários
        menu_util = tk.Menu(menubar, tearoff=0)
        menu_util.add_command(label="Download do YouTube", command=self.abrir_download_youtube)
        menu_util.add_command(label="Abrir Pasta de Saída", command=self.abrir_pasta_saida)  # Adicionado
        menubar.add_cascade(label="Utilitários", menu=menu_util)

    # -------- Funções --------
    def log_text_insert(self, texto):
        self.log_text.after(0, lambda: (self.log_text.config(state=tk.NORMAL),
                                        self.log_text.insert(tk.END, texto + "\n"),
                                        self.log_text.see(tk.END),
                                        self.log_text.config(state=tk.DISABLED)))

    def escolher_arquivo(self):
        arquivo = filedialog.askopenfilename(
            title="Selecione o arquivo de áudio",
            filetypes=[("Arquivos de áudio", "*.mp3 *.wav *.flac *.ogg")]
        )
        if arquivo:
            self.entry_arquivo.delete(0, tk.END)
            self.entry_arquivo.insert(0, arquivo)

    def separar_audio_thread(self):
        if self.processando:
            messagebox.showwarning("Atenção", "O processamento já está em andamento!")
            return
        threading.Thread(target=self.separar_audio, daemon=True).start()

    def separar_audio(self):
        self.processando = True
        self.btn_separar.config(state=tk.DISABLED)
        self.btn_escolher.config(state=tk.DISABLED)
        self.master.config(cursor="wait")

        arquivo_audio = self.entry_arquivo.get()
        if not arquivo_audio or not os.path.exists(arquivo_audio):
            messagebox.showerror("Erro", "Por favor, selecione um arquivo válido.")
            self.reset_interface()
            return

        try:
            import torch
            device_info = "GPU detectada" if torch.cuda.is_available() else "Usando CPU"
            self.log_text_insert(f"[INFO] {device_info}")
        except Exception:
            self.log_text_insert("[AVISO] Torch não encontrado. Certifique-se de que está empacotado no .exe.")

        modelo = self.modelo_var.get()
        formato = self.formato_var.get()
        self.log_text_insert(f"[INFO] Processando arquivo '{arquivo_audio}' com modelo '{modelo}'...")

        # Pasta de saída dentro da pasta Downloads do usuário
        self.pasta_saida = os.path.join(os.path.expanduser("~"), "Downloads", "separated")
        os.makedirs(self.pasta_saida, exist_ok=True)

        args = [arquivo_audio, "--out", self.pasta_saida, "-n", modelo]
        if formato.upper() == "MP3":
            args.append("--mp3")
        else:
            args.append("--wav")

        try:
            from demucs.separate import main as demucs_main
            writer = GuiStreamWriter(self.log_text_insert)
            with contextlib.redirect_stdout(writer), contextlib.redirect_stderr(writer):
                demucs_main(args)

            self.log_text_insert(f"[SUCESSO] Separação concluída! Arquivos em '{self.pasta_saida}'.")
            self.btn_abrir_pasta.pack(side=tk.RIGHT)

            # Pergunta ao usuário se quer abrir a pasta agora
            abrir = messagebox.askyesno("Sucesso", f"Separação concluída!\n\nOs arquivos estão em:\n{self.pasta_saida}\n\nDeseja abrir a pasta agora?")
            if abrir:
                try:
                    open_folder(self.pasta_saida)
                except Exception as e:
                    messagebox.showwarning("Aviso", f"Não foi possível abrir a pasta automaticamente: {e}")

        except Exception as e:
            self.log_text_insert(f"[ERRO] Ocorreu um erro: {e}")
            messagebox.showerror("Erro", f"Ocorreu um erro: {e}")
        finally:
            self.reset_interface()

    def reset_interface(self):
        self.processando = False
        try:
            self.btn_separar.config(state=tk.NORMAL)
            self.btn_escolher.config(state=tk.NORMAL)
            self.master.config(cursor="")
        except Exception:
            pass

    def abrir_pasta_saida(self):
        if self.pasta_saida and os.path.exists(self.pasta_saida):
            try:
                open_folder(self.pasta_saida)
            except Exception as e:
                messagebox.showwarning("Aviso", f"Erro ao abrir a pasta: {e}")
        else:
            messagebox.showwarning("Aviso", "A pasta de saída ainda não foi gerada.")

    def voltar_tela_inicial(self):
        try:
            self.master.destroy()
        except Exception:
            pass
        top = tk.Toplevel()
        try:
            top.iconbitmap(resource_path('icon.ico'))
        except Exception:
            pass
        TelaInicial(top)

    def abrir_meus_downloads(self):
        # Reaproveitado do inicial (mesma lógica)
        janela_downloads = tk.Toplevel(self.master)
        janela_downloads.title("Meus Downloads")
        janela_downloads.geometry("500x300")
        janela_downloads.resizable(False, False)
        try:
            janela_downloads.iconbitmap(resource_path("icon.ico"))
        except Exception:
            pass

        frame = tk.Frame(janela_downloads, padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)

        lista_box = tk.Listbox(frame, width=60)
        lista_box.pack(pady=10, fill=tk.BOTH, expand=True)

        pasta_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
        if not os.path.exists(pasta_downloads):
            os.makedirs(pasta_downloads, exist_ok=True)

        arquivos = [f for f in os.listdir(pasta_downloads) if f.lower().endswith(".mp3")]
        if not arquivos:
            lista_box.insert(tk.END, "Nenhum arquivo encontrado.")
        else:
            for f in arquivos:
                lista_box.insert(tk.END, f)

        def selecionar_arquivo():
            selecionado = lista_box.get(tk.ACTIVE)
            if selecionado and not selecionado.startswith("Nenhum"):
                caminho = os.path.join(pasta_downloads, selecionado)
                self.entry_arquivo.delete(0, tk.END)
                self.entry_arquivo.insert(0, caminho)
                janela_downloads.destroy()

        btn_frame = tk.Frame(janela_downloads)
        btn_frame.pack(pady=10)

        btn_selecionar = tk.Button(btn_frame, text="Selecionar", width=12, command=selecionar_arquivo)
        btn_selecionar.pack(side=tk.LEFT, padx=5)

        btn_cancelar = tk.Button(btn_frame, text="Cancelar", width=12, command=janela_downloads.destroy)
        btn_cancelar.pack(side=tk.LEFT, padx=5)

    def abrir_download_youtube(self):
        top = tk.Toplevel(self.master)
        try:
            top.iconbitmap(resource_path("icon.ico"))
        except Exception:
            pass
        TelaDownloadYoutube(top)


# -------------------------
# Main
# -------------------------
if __name__ == "__main__":
    freeze_support()
    root = tk.Tk()
    try:
        root.iconbitmap(resource_path("icon.ico"))
    except Exception:
        pass
    app = TelaInicial(root)
    root.mainloop()
