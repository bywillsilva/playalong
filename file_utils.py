import os
import sys
import subprocess
import webbrowser

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__)) if "__file__" in globals() else os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def open_folder(path):
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    try:
        if sys.platform.startswith("win"):
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.call(["open", path])
        else:
            subprocess.call(["xdg-open", path])
    except Exception:
        webbrowser.open(path)

def listar_arquivos_downloads(extensoes=("mp3",)):
    pasta_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    if not os.path.exists(pasta_downloads):
        os.makedirs(pasta_downloads, exist_ok=True)
    return [f for f in os.listdir(pasta_downloads) if f.lower().endswith(tuple(extensoes))]
