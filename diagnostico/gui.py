"""Interface gráfica simples (tkinter)."""
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from . import __version__, apresentacao, monitor, relatorio
from .coleta import coletar_tudo

COR = {"ok": "#1a7f37", "atencao": "#b36b00", "falha": "#cf222e"}
DURACOES = ["30 segundos", "1 minuto", "2 minutos", "5 minutos", "10 minutos"]


class App:
    def __init__(self, root):
        self.root = root
        self.dados = None
        self.fila = queue.Queue()
        self.parar_ev = threading.Event()
        root.title(f"Diagnóstico v{__version__}")
        root.geometry("780x600")
        root.minsize(600, 420)

        linha1 = tk.Frame(root, padx=10, pady=10)
        linha1.pack(fill="x")
        self.btn_rodar = tk.Button(linha1, text="Executar diagnóstico", font=("Segoe UI", 11, "bold"),
                                   padx=12, pady=6, command=self.executar)
        self.btn_rodar.pack(side="left")
        self.btn_salvar = tk.Button(linha1, text="Salvar relatório...", padx=12, pady=6,
                                    state="disabled", command=self.salvar)
        self.btn_salvar.pack(side="left", padx=8)

        linha2 = tk.Frame(root, padx=10)
        linha2.pack(fill="x")
        tk.Label(linha2, text="Monitorar por:").pack(side="left")
        self.combo = ttk.Combobox(linha2, values=DURACOES, width=14)
        self.combo.set("1 minuto")
        self.combo.pack(side="left", padx=6)
        self.btn_monitorar = tk.Button(linha2, text="Monitorar", padx=10, pady=3, command=self.monitorar)
        self.btn_monitorar.pack(side="left")
        self.btn_parar = tk.Button(linha2, text="Parar", padx=10, pady=3, state="disabled", command=self.parar)
        self.btn_parar.pack(side="left", padx=6)
        self.barra = ttk.Progressbar(linha2, mode="determinate", length=160)
        self.barra.pack(side="left", padx=8)

        self.status = tk.Label(root, text="Pronto.", anchor="w", padx=10)
        self.status.pack(fill="x", pady=(6, 0))

        self.texto = ScrolledText(root, font=("Consolas", 10), state="disabled", wrap="none")
        self.texto.pack(fill="both", expand=True, padx=10, pady=(4, 10))
        self.texto.tag_configure("titulo", font=("Consolas", 10, "bold"))
        for nivel, cor in COR.items():
            self.texto.tag_configure(nivel, foreground=cor, font=("Consolas", 10, "bold"))
        self._escrever([("Clique em \"Executar diagnóstico\" para uma análise rápida, ou escolha um\n"
                         "tempo e clique em \"Monitorar\" para acompanhar a máquina por alguns minutos.\n", "")])

    # ---------- utilitários ----------
    def _escrever(self, linhas):
        self.texto.configure(state="normal")
        self.texto.delete("1.0", "end")
        for txt, tag in linhas:
            self.texto.insert("end", txt, tag or ())
        self.texto.configure(state="disabled")

    def _ocupado(self, ocupado, pode_parar=False):
        estado = "disabled" if ocupado else "normal"
        self.btn_rodar.configure(state=estado)
        self.btn_monitorar.configure(state=estado)
        self.combo.configure(state="disabled" if ocupado else "normal")
        self.btn_parar.configure(state="normal" if (ocupado and pode_parar) else "disabled")
        if ocupado:
            self.btn_salvar.configure(state="disabled")

    def _rodar(self, alvo, status, pode_parar=False):
        self._ocupado(True, pode_parar)
        self.barra.configure(value=0)
        self.status.configure(text=status)
        threading.Thread(target=self._thread, args=(alvo,), daemon=True).start()
        self.root.after(100, self._checar)

    def _thread(self, alvo):
        try:
            self.fila.put(("fim", alvo()))
        except Exception as e:  # mostra o erro na tela em vez de travar
            self.fila.put(("erro", str(e)))

    def _checar(self):
        try:
            while True:
                msg = self.fila.get_nowait()
                if msg[0] == "prog":
                    self.barra.configure(maximum=msg[2], value=msg[1])
                    self.status.configure(text=f"Monitorando... {msg[1]}/{msg[2]} s")
                elif msg[0] == "status":
                    self.status.configure(text=msg[1])
                else:
                    self._concluir(msg)
                    return
        except queue.Empty:
            self.root.after(100, self._checar)

    def _concluir(self, msg):
        self._ocupado(False)
        if msg[0] == "erro":
            self.status.configure(text="Erro.")
            messagebox.showerror("Erro", msg[1])
            return
        self.dados = msg[1]
        self._escrever(apresentacao.montar_linhas(self.dados))
        self.btn_salvar.configure(state="normal")
        self.barra.configure(value=self.barra["maximum"])
        self.status.configure(text="Concluído.")

    # ---------- ações ----------
    def executar(self):
        self._rodar(coletar_tudo, "Coletando dados (alguns segundos)...")

    def monitorar(self):
        try:
            segundos = monitor.parse_duracao(self.combo.get())
        except ValueError as e:
            messagebox.showwarning("Tempo inválido", f"{e}.\nExemplos: 30 segundos, 2 minutos, 90.")
            return
        self.parar_ev = threading.Event()
        base = self.dados

        def alvo():
            dados = dict(base) if base else coletar_tudo()
            self.fila.put(("status", f"Monitorando por {monitor.formatar_duracao(segundos)}..."))
            resultado = monitor.monitorar(
                segundos, ao_progresso=lambda a, b: self.fila.put(("prog", a, b)), parar=self.parar_ev)
            if resultado:
                dados["monitor"] = resultado
            return dados

        self._rodar(alvo, "Preparando...", pode_parar=True)

    def parar(self):
        self.parar_ev.set()
        self.btn_parar.configure(state="disabled")
        self.status.configure(text="Encerrando e analisando o que foi coletado...")

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
