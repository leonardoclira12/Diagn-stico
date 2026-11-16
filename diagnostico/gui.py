"""Interface gráfica simples (tkinter): nota geral, abas e monitoramento."""
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from . import __version__, analise, apresentacao, monitor, relatorio
from .coleta import coletar_tudo

COR = {"ok": "#1a7f37", "atencao": "#b36b00", "falha": "#cf222e", "neutro": "#6e7781"}
DURACOES = ["30 segundos", "1 minuto", "2 minutos", "5 minutos", "10 minutos"]
ABAS_TEXTO = ["Resumo", "Inicialização", "Discos", "Bateria", "Rede", "Monitoramento", "Processos"]
VAZIO = {
    "Resumo": "Clique em \"Executar diagnóstico\" para começar.",
    "Inicialização": "Execute o diagnóstico para ver os programas que abrem com o sistema.",
    "Discos": "Execute o diagnóstico para ver tipo e saúde dos discos.",
    "Bateria": "Execute o diagnóstico para ver a bateria.",
    "Rede": "Execute o diagnóstico para testar a rede.",
    "Monitoramento": "Escolha um tempo e clique em \"Monitorar\" para acompanhar a máquina.",
    "Processos": "Execute o diagnóstico para ver os processos que mais consomem.",
}


class Grafico(tk.Canvas):
    """Gráfico de linha simples, desenhado conforme os valores chegam."""

    def __init__(self, master, titulo, unidade="%", maximo=None, cor="#0969da", altura=130):
        super().__init__(master, height=altura, bg="white", highlightthickness=1,
                         highlightbackground="#d0d7de")
        self.titulo, self.unidade, self.maximo_fixo, self.cor = titulo, unidade, maximo, cor
        self.valores, self.total = [], None
        self.bind("<Configure>", lambda _e: self.desenhar())
        self.after(50, self.desenhar)

    def reiniciar(self, total=None):
        self.valores, self.total = [], total
        self.desenhar()

    def adicionar(self, valor):
        self.valores.append(valor)
        self.desenhar()

    def desenhar(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 80 or h < 60:
            return
        esq, dir_, topo, base = 42, 10, 26, h - 12
        maximo = self.maximo_fixo or max(10.0, max(self.valores, default=0) * 1.25)
        atual = f"{self.valores[-1]:.0f}{self.unidade}" if self.valores else "—"
        self.create_text(8, 11, anchor="w", text=self.titulo, font=("Segoe UI", 9, "bold"))
        self.create_text(w - 8, 11, anchor="e", text=atual, font=("Segoe UI", 9, "bold"), fill=self.cor)
        for frac in (0, 0.5, 1):
            y = base - frac * (base - topo)
            self.create_line(esq, y, w - dir_, y, fill="#eaeef2")
            self.create_text(esq - 4, y, anchor="e", text=f"{maximo * frac:.0f}",
                             font=("Segoe UI", 7), fill="#6e7781")
        n = len(self.valores)
        if n == 0:
            return
        passos = max((self.total or n) - 1, 1)
        pontos = []
        for i, v in enumerate(self.valores):
            x = esq + (w - esq - dir_) * min(i / passos, 1)
            y = base - (base - topo) * min(v / maximo, 1)
            pontos += [x, y]
        if n == 1:
            self.create_oval(pontos[0] - 2, pontos[1] - 2, pontos[0] + 2, pontos[1] + 2, fill=self.cor, outline=self.cor)
        else:
            self.create_line(*pontos, fill=self.cor, width=2)


class App:
    def __init__(self, root):
        self.root = root
        self.dados = None
        self.fila = queue.Queue()
        self.parar_ev = threading.Event()
        root.title(f"Diagnóstico v{__version__}")
        root.geometry("940x700")
        root.minsize(760, 520)

        # --- cabeçalho: nota geral + botões ---
        cab = tk.Frame(root, padx=12, pady=10)
        cab.pack(fill="x")
        self.selo = tk.Label(cab, text="SEM ANÁLISE", fg="white", bg=COR["neutro"],
                             font=("Segoe UI", 15, "bold"), padx=18, pady=10, width=12)
        self.selo.pack(side="left")
        info = tk.Frame(cab, padx=12)
        info.pack(side="left", fill="x", expand=True)
        tk.Label(info, text="Nota geral", font=("Segoe UI", 9), anchor="w").pack(fill="x")
        self.sub = tk.Label(info, text="Execute o diagnóstico para avaliar este computador.",
                            font=("Segoe UI", 10), anchor="w")
        self.sub.pack(fill="x")
        self.btn_salvar = tk.Button(cab, text="Salvar relatório...", padx=12, pady=6,
                                    state="disabled", command=self.salvar)
        self.btn_salvar.pack(side="right")
        self.btn_rodar = tk.Button(cab, text="Executar diagnóstico", font=("Segoe UI", 11, "bold"),
                                   padx=14, pady=6, command=self.executar)
        self.btn_rodar.pack(side="right", padx=8)

        # --- controles do monitoramento ---
        linha2 = tk.Frame(root, padx=12)
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
        self.status = tk.Label(linha2, text="Pronto.", anchor="w")
        self.status.pack(side="left", padx=8)

        # --- abas ---
        self.abas = ttk.Notebook(root)
        self.abas.pack(fill="both", expand=True, padx=12, pady=(8, 12))
        self.textos = {}
        self.paginas = {}
        for nome in ABAS_TEXTO:
            self.paginas[nome] = self._nova_aba_texto(nome)
        for nome in ABAS_TEXTO:
            self._escrever(nome, [(VAZIO[nome] + "\n", "")])

    # ---------- construção ----------
    def _nova_aba_texto(self, nome):
        quadro = tk.Frame(self.abas)
        self.abas.add(quadro, text=f" {nome} ")
        if nome == "Monitoramento":
            graficos = tk.Frame(quadro)
            graficos.pack(fill="x", padx=4, pady=4)
            for c in range(3):
                graficos.columnconfigure(c, weight=1, uniform="g")
            self.g_cpu = Grafico(graficos, "CPU", "%", maximo=100, cor="#0969da")
            self.g_ram = Grafico(graficos, "RAM", "%", maximo=100, cor="#8250df")
            self.g_disco = Grafico(graficos, "Disco (leitura+escrita)", " MB/s", cor="#1a7f37")
            for c, g in enumerate((self.g_cpu, self.g_ram, self.g_disco)):
                g.grid(row=0, column=c, sticky="ew", padx=3)
        txt = ScrolledText(quadro, font=("Consolas", 10), state="disabled", wrap="none")
        txt.pack(fill="both", expand=True)
        txt.tag_configure("titulo", font=("Consolas", 10, "bold"))
        for nivel in ("ok", "atencao", "falha"):
            txt.tag_configure(nivel, foreground=COR[nivel], font=("Consolas", 10, "bold"))
        self.textos[nome] = txt
        return quadro

    def _escrever(self, aba, linhas):
        txt = self.textos[aba]
        txt.configure(state="normal")
        txt.delete("1.0", "end")
        for t, tag in linhas:
            txt.insert("end", t, tag or ())
        txt.configure(state="disabled")

    def _atualizar_abas(self):
        conteudo = apresentacao.abas(self.dados)
        for nome in ABAS_TEXTO:
            linhas = conteudo.get(nome) or [(VAZIO[nome] + "\n", "")]
            self._escrever(nome, linhas)
        nota = analise.resumo_nota(analise.analisar(self.dados))
        self.selo.configure(text=nota["titulo"], bg=COR[nota["nivel"]])
        self.sub.configure(text=apresentacao.descrever_nota(nota))

    def _ocupado(self, ocupado, pode_parar=False):
        estado = "disabled" if ocupado else "normal"
        self.btn_rodar.configure(state=estado)
        self.btn_monitorar.configure(state=estado)
        self.combo.configure(state="disabled" if ocupado else "normal")
        self.btn_parar.configure(state="normal" if (ocupado and pode_parar) else "disabled")
        if ocupado:
            self.btn_salvar.configure(state="disabled")

    # ---------- execução em segundo plano ----------
    def _rodar(self, alvo, status, pode_parar=False, aba_final="Resumo"):
        self._ocupado(True, pode_parar)
        self.barra.configure(value=0)
        self.status.configure(text=status)
        self.aba_final = aba_final
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
                elif msg[0] == "amostra":
                    self.g_cpu.adicionar(msg[1])
                    self.g_ram.adicionar(msg[2])
                    self.g_disco.adicionar(msg[3])
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
        self._atualizar_abas()
        self.abas.select(self.paginas[self.aba_final])
        self.btn_salvar.configure(state="normal")
        self.barra.configure(value=self.barra["maximum"])
        self.status.configure(text="Concluído.")

    # ---------- ações ----------
    def executar(self):
        self._rodar(coletar_tudo, "Coletando dados e testando a rede (alguns segundos)...")

    def monitorar(self):
        try:
            segundos = monitor.parse_duracao(self.combo.get())
        except ValueError as e:
            messagebox.showwarning("Tempo inválido", f"{e}.\nExemplos: 30 segundos, 2 minutos, 90.")
            return
        self.parar_ev = threading.Event()
        base = self.dados
        for g in (self.g_cpu, self.g_ram, self.g_disco):
            g.reiniciar(segundos)
        self.abas.select(self.paginas["Monitoramento"])

        def alvo():
            dados = dict(base) if base else coletar_tudo()
            self.fila.put(("status", f"Monitorando por {monitor.formatar_duracao(segundos)}..."))
            resultado = monitor.monitorar(
                segundos, ao_progresso=lambda a, b: self.fila.put(("prog", a, b)), parar=self.parar_ev,
                ao_amostra=lambda c, r, d: self.fila.put(("amostra", c, r, d)))
            if resultado:
                dados["monitor"] = resultado
            return dados

        self._rodar(alvo, "Preparando...", pode_parar=True, aba_final="Monitoramento")

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
