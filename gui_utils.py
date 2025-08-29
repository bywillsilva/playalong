import tkinter as tk
from tkinter import scrolledtext

class GuiStreamWriter:
    def __init__(self, log_callback):
        self.log_callback = log_callback
        self._buffer = ""

    def write(self, data):
        if not data: return
        self._buffer += data
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            text = line.rstrip()
            if text: self.log_callback(text)

    def flush(self):
        if self._buffer:
            text = self._buffer.rstrip()
            if text: self.log_callback(text)
            self._buffer = ""

def append_log(widget: scrolledtext.ScrolledText, texto: str):
    widget.config(state=tk.NORMAL)
    widget.insert(tk.END, texto + "\n")
    widget.see(tk.END)
    widget.config(state=tk.DISABLED)
