import os
import threading
from tkinter import messagebox

try:
    import yt_dlp
except ImportError:
    yt_dlp = None

def baixar_youtube(link, formato, pasta_downloads, log_callback):
    if yt_dlp is None:
        messagebox.showerror("Erro", "Biblioteca yt_dlp não instalada.")
        return

    os.makedirs(pasta_downloads, exist_ok=True)
    postprocessor = [{'key': 'FFmpegExtractAudio', 'preferredcodec': formato.lower(), 'preferredquality': '192'}]

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(pasta_downloads, '%(title)s.%(ext)s'),
        'postprocessors': postprocessor,
        'quiet': True,
        'no_warnings': True,
        'progress_hooks': [lambda d: progress_hook(d, log_callback)]
    }

    def baixar():
        try:
            log_callback("[INFO] Iniciando download...")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([link])
            log_callback("[SUCESSO] Arquivo salvo em Downloads!")
        except Exception as e:
            log_callback(f"[ERRO] Falha: {e}")

    threading.Thread(target=baixar, daemon=True).start()

def progress_hook(d, log_callback):
    status = d.get("status")
    if status == 'downloading':
        percent = d.get('_percent_str', '').strip()
        speed = d.get('_speed_str', '').strip()
        eta = d.get('_eta_str', '').strip()
        log_callback(f"Baixando: {percent} | Velocidade: {speed} | ETA: {eta}")
    elif status == 'finished':
        log_callback("Download concluído, convertendo...")
