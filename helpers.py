import os
import subprocess
import sys
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

class GuiStreamWriter:
    def __init__(self, log_callback):
        self.log_callback = log_callback
        self._buffer = ""

    def write(self, data):
        if not data:
            return
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