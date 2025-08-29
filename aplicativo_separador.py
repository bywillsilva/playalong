import os
import subprocess
import threading
import time
import contextlib
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

from .helpers import resource_path, open_folder
from .helpers import GuiStreamWriter
from .tela_download_youtube import TelaDownloadYoutube

class AplicativoSeparador:
    def __init__(self, master, arquivo_inicial=None):
        self.master = master
        self.master.title("Separador de Áudio (Demucs)")
        self.master.geometry("700x300")
        self.master.resizable(False, False)
        try:
            self.master.iconbitmap(resource_path("icon.ico"))
        except Exception:
            pass

        self.arquivo_inicial = arquivo_inicial
        self.pasta_saida = os.path.join(os.path.expanduser("~"), "Downloads", "separated")
        self.processando = False
        self._log_buffer = []
        self._log_win = None
        self._log_widget = None
        self.tempo_inicio = None

        self.setup_gui()

    def setup_gui(self):
        frame = tk.Frame(self.master, padx=20, pady=20)
        frame.pack(expand=True, fill=tk.BOTH)

        # Entrada de arquivo
        frame_arquivo = tk.Frame(frame)
        frame_arquivo.pack(pady=10, fill=tk.X)

        self.entry_arquivo = tk.Entry(frame_arquivo, width=65, font=("Arial", 11))
        self.entry_arquivo.pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)
        if self.arquivo_inicial and os.path.exists(self.arquivo_inicial):
            self.entry_arquivo.insert(0, self.arquivo_inicial)

        self.btn_escolher = tk.Button(frame_arquivo, text="Escolher Arquivo", width=15, command=self.escolher_arquivo)
        self.btn_escolher.pack(side=tk.LEFT)

        # Botões ação
        frame_botoes = tk.Frame(frame)
        frame_botoes.pack(fill=tk.X, pady=5)
        self.btn_separar = tk.Button(frame_botoes, text="Separar Áudio", width=20, height=2,
                                     bg="#4CAF50", fg="white", command=self.separar_audio_thread)
        self.btn_separar.pack(side=tk.LEFT)
        self.btn_abrir_pasta = tk.Button(frame_botoes, text="Mixar traks", width=20, command=self.abrir_audacity)
        self.btn_abrir_pasta.pack_forget()

        self.progress = ttk.Progressbar(frame, mode="indeterminate", length=400)
        self.progress.pack(fill=tk.X, pady=20, side=tk.BOTTOM)
        self.tempo_label = tk.Label(frame, text="", font=("Arial", 11), fg="blue")
        self.tempo_label.pack(side=tk.BOTTOM)

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

        MODELOS_DEMUCS = [
            ("Demucs HT (preciso, mais lento)", "htdemucs"),
            ("Demucs HT Fine-tuned (preciso, mais lento)", "htdemucs_ft"),
            ("MDX (bom equilíbrio entre qualidade e velocidade)", "mdx"),
            ("MDX Extra (alta qualidade, mais lento)", "mdx_extra"),
            ("MDX Quantizado (rápido, menor qualidade)", "mdx_q"),
            ("MDX Extra Quantizado (rápido, menor qualidade)", "mdx_extra_q"),
        ]

        self.modelo_var = tk.StringVar(value="htdemucs")
        menu_modelo = tk.Menu(menubar, tearoff=0)
        for label, value in MODELOS_DEMUCS:
            menu_modelo.add_radiobutton(label=label, variable=self.modelo_var, value=value)
        menubar.add_cascade(label="Modelo", menu=menu_modelo)

        menu_util = tk.Menu(menubar, tearoff=0)
        menu_util.add_command(label="Download do YouTube", command=self.abrir_download_youtube)
        menu_util.add_command(label="Abrir Pasta de Saída", command=self.abrir_pasta_saida)
        menu_util.add_command(label="Audacity", command=self.abrir_audacity)
        menubar.add_cascade(label="Utilitários", menu=menu_util)

        menubar.add_command(label="Log", command=self.abrir_log)

    # -------- Funções --------
    def abrir_audacity(self):
        try:
            audacity_exe = r"C:\Program Files\Audacity\audacity.exe"

            if not os.path.exists(audacity_exe):
                messagebox.showerror(
                    "Erro",
                    f"Não encontrei o Audacity em:\n{audacity_exe}\n\n"
                    "Verifique se está instalado no local correto."
                )
                return

            subprocess.Popen([audacity_exe])

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao abrir o Audacity:\n{e}")

    def _append_log(self, texto: str):
        """Acumula no buffer e atualiza a janela de log se estiver aberta."""
        if not texto:
            return
        self._log_buffer.append(texto)
        # Se a janela de log estiver aberta, atualiza incrementalmente
        if self._log_widget and self._log_widget.winfo_exists():
            self._log_widget.config(state=tk.NORMAL)
            self._log_widget.insert(tk.END, texto + "\n")
            self._log_widget.see(tk.END)
            self._log_widget.config(state=tk.DISABLED)

    def log_text_insert(self, texto):
        # Compatível com o writer existente (redirecionamento do demucs)
        # Garante thread-safety usando .after para executar no mainloop
        self.master.after(0, lambda t=texto: self._append_log(t))

    def atualizar_tempo(self):
        """Atualiza o cronômetro enquanto processa."""
        if self.processando:
            segundos = int(time.time() - self.tempo_inicio)
            self.tempo_label.config(text=f"Tempo decorrido: {segundos}s")
            self.master.after(1000, self.atualizar_tempo)  # chama de novo em 1s

    
    def abrir_log(self):
        """Abre (ou traz para frente) a janela com o log acumulado."""
        if self._log_win and self._log_win.winfo_exists():
            self._log_win.deiconify()
            self._log_win.lift()
            return

        self._log_win = tk.Toplevel(self.master)
        self._log_win.title("Log do Processo")
        self._log_win.geometry("780x420")
        try:
            self._log_win.iconbitmap(resource_path("icon.ico"))
        except Exception:
            pass

        txt = scrolledtext.ScrolledText(self._log_win, width=95, height=25, state=tk.NORMAL)
        txt.pack(fill=tk.BOTH, expand=True)
        # Preenche com o buffer já acumulado
        if self._log_buffer:
            txt.insert(tk.END, "\n".join(self._log_buffer) + "\n")
        txt.config(state=tk.DISABLED)
        self._log_widget = txt

        def on_close():
            # Não apagamos o buffer; só esquecemos a janela
            self._log_widget = None
            self._log_win.destroy()
            self._log_win = None

        self._log_win.protocol("WM_DELETE_WINDOW", on_close)

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
        self.progress.start(10)  # inicia animação
        self.tempo_inicio = time.time()
        self.atualizar_tempo()


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
            abrir = messagebox.askyesno(
                "Sucesso",
                f"Separação concluída!\n\nOs arquivos estão em:\n{self.pasta_saida}\n\nDeseja abrir a pasta agora?"
            )
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

        # --- NOVO: parar barra de progresso e mostrar status ---
        try:
            self.progress.stop()
            self.tempo_label.config(text="Finalizado!")
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
        from .tela_inicial import TelaInicial
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