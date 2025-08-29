import tkinter as tk
from multiprocessing import freeze_support
from playalongs.utils.file_utils import resource_path
from playalongs.gui.tela_inicial import TelaInicial

if __name__ == "__main__":
    freeze_support()
    root = tk.Tk()
    try:
        root.iconbitmap(resource_path("resources/icon.ico"))
    except Exception:
        pass
    app = TelaInicial(root)
    root.mainloop()