"""Interface gráfica simples (tkinter): um botão, o resultado e salvar relatório."""
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.scrolledtext import ScrolledText

from . import __version__, apresentacao, relatorio
from .coleta import coletar_tudo

COR = {"ok": "#1a7f37", "atencao": "#b36b00", "falha": "#cf222e"}


class App:
    def __init__(self, root):
        self.root = root
        self.dados = None
        self.fila = queue.Queue()
        root.title(f"Diagnóstico v{__version__}")
        root.geometry("760x560")
        root.minsize(560, 400)

        topo = tk.Frame(root, padx=10, pady=10)
        topo.pack(fill="x")
        self.btn_rodar = tk.Button(topo, text="Executar diagnóstico", font=("Segoe UI", 11, "bold"),
                                   padx=12, pady=6, command=self.executar)
        self.btn_rodar.pack(side="left")
        self.btn_salvar = tk.Button(topo, text="Salvar relatório...", padx=12, pady=6,
                                    state="disabled", command=self.salvar)
        self.btn_salvar.pack(side="left", padx=8)
        self.status = tk.Label(topo, text="Pronto.", anchor="w")
        self.status.pack(side="left", padx=10)

        self.texto = ScrolledText(root, font=("Consolas", 10), state="disabled", wrap="none")
        self.texto.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.texto.tag_configure("titulo", font=("Consolas", 10, "bold"))
        for nivel, cor in COR.items():
            self.texto.tag_configure(nivel, foreground=cor, font=("Consolas", 10, "bold"))
        self._escrever([("Clique em \"Executar diagnóstico\" para começar.\n", "")])

    def _escrever(self, linhas):
        self.texto.configure(state="normal")
        self.texto.delete("1.0", "end")
        for txt, tag in linhas:
            self.texto.insert("end", txt, tag or ())
        self.texto.configure(state="disabled")

    def executar(self):
        self.btn_rodar.configure(state="disabled")
        self.btn_salvar.configure(state="disabled")
        self.status.configure(text="Coletando dados (alguns segundos)...")
        threading.Thread(target=self._trabalho, daemon=True).start()
        self.root.after(100, self._checar)

    def _trabalho(self):
        try:
            self.fila.put(("ok", coletar_tudo()))
        except Exception as e:  # mostra o erro na tela em vez de travar
            self.fila.put(("erro", str(e)))

    def _checar(self):
        try:
            tipo, valor = self.fila.get_nowait()
        except queue.Empty:
            self.root.after(100, self._checar)
            return
        self.btn_rodar.configure(state="normal")
        if tipo == "erro":
            self.status.configure(text="Erro na coleta.")
            messagebox.showerror("Erro", valor)
            return
        self.dados = valor
        self._escrever(apresentacao.montar_linhas(valor))
        self.btn_salvar.configure(state="normal")
        self.status.configure(text="Concluído.")

    def salvar(self):
        if not self.dados:
            return
        caminho = filedialog.asksaveasfilename(
            defaultextension=".txt", filetypes=[("Texto", "*.txt")],
            initialfile="diagnostico.txt", title="Salvar relatório")
        if not caminho:
            return
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(relatorio.gerar_texto(self.dados))
        self.status.configure(text=f"Salvo em {caminho}")


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()
