import os
import tkinter as tk
from tkinter import messagebox, ttk
from playalongs.gui.tela_download_youtube import TelaDownloadYoutube
from playalongs.gui.aplicativo_separador import AplicativoSeparador
from playalongs.utils.file_utils import resource_path, open_folder, listar_arquivos_downloads

class TelaInicial:
    def __init__(self, master):
        self.master = master
        self.master.title("PlayAlongs")
        self.master.geometry("700x300")
        self.master.resizable(False, False)
        self.pasta_saida = os.path.join(os.path.expanduser("~"), "Downloads", "separated")
        try:
            self.master.iconbitmap(resource_path("resources/icon.ico"))
        except Exception:
            pass

        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)

        menu_util = tk.Menu(menubar, tearoff=0)
        menu_util.add_command(label="Abrir Pasta de Saída", command=self.abrir_pasta_saida)
        menu_util.add_command(label="Audacity", command=self.abrir_audacity)
        menubar.add_cascade(label="Utilitários", menu=menu_util)

        self.frame_principal = tk.Frame(master, padx=30, pady=20)
        self.frame_principal.pack(expand=True, fill=tk.BOTH)

        titulo = tk.Label(self.frame_principal, text="🎵 PlayAlongs",
                          font=("Segoe UI", 24, "bold"), fg="#2c3e50")
        titulo.pack(pady=(0, 25))

        frame_local = tk.Frame(self.frame_principal)
        frame_local.pack(fill=tk.X)

        label_local = tk.Label(frame_local, text="Selecione um arquivo de áudio local para separar:",
                               font=("Segoe UI", 12))
        label_local.pack(anchor="w")

        self.btn_abrir_separador = tk.Button(frame_local, text="📂 Selecionar Arquivo Local",
                                             font=("Segoe UI", 12, "bold"), bg="#27ae60", fg="white",
                                             activebackground="#2ecc71", cursor="hand2",
                                             command=self.abrir_separador_sem_download)
        self.btn_abrir_separador.pack(pady=10, fill=tk.X)

        self.btn_download_youtube = tk.Button(frame_local, text="Baixar do YouTube",
                                              font=("Segoe UI", 12, "bold"), bg="#e74c3c", fg="white",
                                              activebackground="#c0392b", cursor="hand2",
                                              command=self.abrir_download_youtube)
        self.btn_download_youtube.pack(pady=10, fill=tk.X)

    def abrir_audacity(self):
        try:
            audacity_exe = r"C:\Program Files\Audacity\audacity.exe"
            if not os.path.exists(audacity_exe):
                messagebox.showerror("Erro",
                                     f"Não encontrei o Audacity em:\n{audacity_exe}")
                return
            import subprocess
            subprocess.Popen([audacity_exe])
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao abrir o Audacity:\n{e}")

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
            top.iconbitmap(resource_path("resources/icon.ico"))
        except Exception:
            pass
        TelaDownloadYoutube(top)

    def abrir_separador_sem_download(self):
        self.master.withdraw()
        top = tk.Toplevel(self.master)
        try:
            top.iconbitmap(resource_path("resources/icon.ico"))
        except Exception:
            pass
        AplicativoSeparador(top)
