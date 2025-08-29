import os
import contextlib
from playalongs.utils.gui_utils import GuiStreamWriter

def separar_audio(arquivo_audio, pasta_saida, modelo, formato, log_callback):
    os.makedirs(pasta_saida, exist_ok=True)
    args = [arquivo_audio, "--out", pasta_saida, "-n", modelo]
    if formato.upper() == "MP3":
        args.append("--mp3")
    else:
        args.append("--wav")

    try:
        from demucs.separate import main as demucs_main
        writer = GuiStreamWriter(log_callback)
        with contextlib.redirect_stdout(writer), contextlib.redirect_stderr(writer):
            demucs_main(args)
        log_callback(f"[SUCESSO] Separação concluída! Arquivos em '{pasta_saida}'.")
    except Exception as e:
        log_callback(f"[ERRO] Ocorreu um erro: {e}")
        raise e
