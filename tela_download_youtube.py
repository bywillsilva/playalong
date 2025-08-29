import os
import tkinter as tk
from tkinter import messagebox, scrolledtext
from playalongs.services.downloader import baixar_youtube
from playalongs.utils.file_utils import resource_path

class TelaDownloadYoutube:
    def __init__(self, master):
        self.master = master
        self.master.title("Download do YouTube")
        self.master.geometry("700x300")
        self.master.resizable(False, False)
        try:
            self.master.iconbitmap(resource_path("resources/icon.ico"))
        except Exception:
            pass

        frame = tk.Frame(master, padx=20, pady=20)
        frame.pack(expand=True, fill=tk.BOTH)

        tk.Label(frame, text="Cole o link da música no YouTube:", font=("Segoe UI", 12)).pack(anchor="w")
        self.entry_link = tk.Entry(frame, font=("Segoe UI", 11), width=60)
        self.entry_link.pack(pady=5, fill=tk.X)

        self.formato_var = tk.StringVar(value="MP3")
        formato_frame = tk.Frame(frame)
        formato_frame.pack(anchor="w", pady=(4, 8))
        tk.Label(formato_frame, text="Formato:").pack(side=tk.LEFT)
        tk.Radiobutton(formato_frame, text="MP3", variable=self.formato_var, value="MP3").pack(side=tk.LEFT, padx=6)
        tk.Radiobutton(formato_frame, text="WAV", variable=self.formato_var, value="WAV").pack(side=tk.LEFT, padx=6)

        tk.Button(frame, text="▶️ Baixar", font=("Segoe UI", 12, "bold"), bg="#2980b9", fg="white",
                  activebackground="#3498db", cursor="hand2", command=self.baixar_musica).pack(pady=(5, 0), fill=tk.X)

        self.log_download = scrolledtext.ScrolledText(frame, height=6, font=("Segoe UI", 10),
                                                      state=tk.DISABLED, bg="#f0f0f0")
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
        pasta_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
        baixar_youtube(link, self.formato_var.get(), pasta_downloads, self.log_download_insert)
