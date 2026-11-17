"""Tema escuro com destaque laranja e componentes visuais da janela (tkinter puro)."""
import platform
import tkinter as tk
from tkinter import ttk

_SO = platform.system()
FONTE = "Segoe UI" if _SO == "Windows" else "Helvetica Neue" if _SO == "Darwin" else "DejaVu Sans"
MONO = "Consolas" if _SO == "Windows" else "Menlo" if _SO == "Darwin" else "DejaVu Sans Mono"

BG = "#141518"        # fundo da janela
MENU = "#101113"      # menu lateral
PAINEL = "#1e2024"    # cartões
PAINEL2 = "#2a2d33"   # campos e botões
BORDA = "#33363c"
TEXTO = "#e8e9eb"
SUAVE = "#8b9098"
TRILHO = "#2f3238"
DESTAQUE = "#ff5a1f"  # laranja
DESTAQUE_HOVER = "#ff7a45"
COR = {"ok": "#3fb950", "atencao": "#e3b341", "falha": "#f85149", "neutro": "#6e7681"}


def cor_por_uso(percent, limite_atencao=70, limite_falha=90):
    if percent >= limite_falha:
        return COR["falha"]
    if percent >= limite_atencao:
        return COR["atencao"]
    return COR["ok"]


def aplicar_estilo(root):
    """Deixa Combobox, barra de progresso e rolagem no tema escuro (tema 'clam' funciona igual em todo SO)."""
    s = ttk.Style(root)
    s.theme_use("clam")
    s.configure("TCombobox", fieldbackground=PAINEL2, background=PAINEL2, foreground=TEXTO,
                arrowcolor=TEXTO, bordercolor=BORDA, lightcolor=PAINEL2, darkcolor=PAINEL2,
                selectbackground=PAINEL2, selectforeground=TEXTO, padding=5)
    s.map("TCombobox", fieldbackground=[("readonly", PAINEL2), ("disabled", PAINEL)],
          foreground=[("disabled", SUAVE)], selectbackground=[("readonly", PAINEL2)],
          selectforeground=[("readonly", TEXTO)])
    root.option_add("*TCombobox*Listbox.background", PAINEL2)
    root.option_add("*TCombobox*Listbox.foreground", TEXTO)
    root.option_add("*TCombobox*Listbox.selectBackground", DESTAQUE)
    root.option_add("*TCombobox*Listbox.selectForeground", "white")
    s.configure("Horizontal.TProgressbar", troughcolor=PAINEL2, background=DESTAQUE,
                bordercolor=PAINEL2, lightcolor=DESTAQUE, darkcolor=DESTAQUE, thickness=8)
    s.configure("Vertical.TScrollbar", troughcolor=PAINEL, background=PAINEL2, bordercolor=PAINEL,
                arrowcolor=SUAVE, lightcolor=PAINEL2, darkcolor=PAINEL2)
    s.map("Vertical.TScrollbar", background=[("active", BORDA)])


class Botao(tk.Label):
    """Botão feito com Label para ter as mesmas cores em Windows, Mac e Linux."""

    def __init__(self, master, texto, comando, primario=False):
        self._cmd, self._primario, self._estado = comando, primario, "normal"
        super().__init__(master, text=texto, font=(FONTE, 10, "bold"), padx=16, pady=8, bd=0,
                         cursor="hand2", highlightthickness=1)
        self._pintar(False)
        self.bind("<Enter>", lambda _e: self._pintar(True))
        self.bind("<Leave>", lambda _e: self._pintar(False))
        self.bind("<Button-1>", self._clicar)

    def _pintar(self, hover):
        if self._estado == "disabled":
            cores = dict(bg=PAINEL, fg="#5c616a", highlightbackground=BORDA, cursor="arrow")
        elif self._primario:
            cores = dict(bg=DESTAQUE_HOVER if hover else DESTAQUE, fg="white",
                         highlightbackground=DESTAQUE, cursor="hand2")
        else:
            cores = dict(bg=BORDA if hover else PAINEL2, fg=TEXTO,
                         highlightbackground=BORDA, cursor="hand2")
        super().configure(**cores)

    def _clicar(self, _e):
        if self._estado == "normal" and self._cmd:
            self._cmd()

    def configure(self, cnf=None, **kw):
        if "state" in kw:
            self._estado = kw.pop("state")
            self._pintar(False)
        if cnf or kw:
            super().configure(cnf, **kw)

    config = configure


class Cartao(tk.Frame):
    """Painel com título, explicação curta e barra laranja embaixo (como na referência)."""

    def __init__(self, master, titulo, explicacao=None):
        super().__init__(master, bg=PAINEL, highlightthickness=1, highlightbackground=BORDA,
                         highlightcolor=BORDA)
        tk.Frame(self, bg=DESTAQUE, height=3).pack(side="bottom", fill="x")
        tk.Label(self, text=titulo.upper(), font=(FONTE, 10, "bold"), fg=TEXTO, bg=PAINEL,
                 anchor="w").pack(fill="x", padx=16, pady=(14, 2))
        if explicacao:
            exp = tk.Label(self, text=explicacao, font=(FONTE, 9), fg=SUAVE, bg=PAINEL,
                           anchor="w", justify="left")
            exp.pack(fill="x", padx=16, pady=(0, 8))
            exp.bind("<Configure>", lambda e, w=exp: w.configure(wraplength=max(e.width - 4, 120)))
        self.corpo = tk.Frame(self, bg=PAINEL)
        self.corpo.pack(fill="both", expand=True, padx=16, pady=(0, 10))


class Anel(tk.Canvas):
    """Medidor circular (0 a 100) com valor no centro."""

    def __init__(self, master, tamanho=130, espessura=11):
        super().__init__(master, width=tamanho, height=tamanho, bg=PAINEL, highlightthickness=0)
        self.tamanho, self.espessura = tamanho, espessura
        self.valor, self.centro, self.sub, self.cor = None, "—", "", COR["neutro"]
        self.desenhar()

    def definir(self, valor, centro, sub="", cor=DESTAQUE):
        self.valor, self.centro, self.sub, self.cor = valor, centro, sub, cor
        self.desenhar()

    def desenhar(self):
        self.delete("all")
        t, e = self.tamanho, self.espessura
        m = e / 2 + 3
        caixa = (m, m, t - m, t - m)
        self.create_oval(*caixa, outline=TRILHO, width=e)
        if self.valor is not None and self.valor > 0:
            self.create_arc(*caixa, start=90, extent=-min(self.valor, 100) / 100 * 359.9,
                            style="arc", outline=self.cor, width=e)
        self.create_text(t / 2, t / 2 - (7 if self.sub else 0), text=self.centro, fill=TEXTO,
                         font=(FONTE, int(t / 5.2), "bold"))
        if self.sub:
            self.create_text(t / 2, t / 2 + t / 6, text=self.sub, fill=SUAVE, font=(FONTE, 8))


class Grafico(tk.Canvas):
    """Gráfico de linha simples, desenhado conforme os valores chegam."""

    def __init__(self, master, titulo, unidade="%", maximo=None, cor=DESTAQUE, altura=150):
        super().__init__(master, height=altura, bg=PAINEL, highlightthickness=1,
                         highlightbackground=BORDA)
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
        esq, dir_, topo, base = 42, 12, 30, h - 14
        maximo = self.maximo_fixo or max(10.0, max(self.valores, default=0) * 1.25)
        atual = f"{self.valores[-1]:.0f}{self.unidade}" if self.valores else "—"
        self.create_text(12, 14, anchor="w", text=self.titulo.upper(), font=(FONTE, 9, "bold"), fill=TEXTO)
        self.create_text(w - 12, 14, anchor="e", text=atual, font=(FONTE, 10, "bold"), fill=self.cor)
        for frac in (0, 0.5, 1):
            y = base - frac * (base - topo)
            self.create_line(esq, y, w - dir_, y, fill=TRILHO, dash=(2, 4) if frac else ())
            self.create_text(esq - 5, y, anchor="e", text=f"{maximo * frac:.0f}",
                             font=(FONTE, 7), fill=SUAVE)
        n = len(self.valores)
        if n == 0:
            return
        passos = max((self.total or n) - 1, 1)
        pontos = []
        for i, v in enumerate(self.valores):
            pontos += [esq + (w - esq - dir_) * min(i / passos, 1),
                       base - (base - topo) * min(v / maximo, 1)]
        if n == 1:
            x, y = pontos
            self.create_oval(x - 3, y - 3, x + 3, y + 3, fill=self.cor, outline=self.cor)
        else:
            self.create_line(*pontos, fill=self.cor, width=2)


def criar_texto(master, altura=None):
    """Área de texto somente leitura, no tema escuro, com rolagem e as cores de status."""
    quadro = tk.Frame(master, bg=PAINEL)
    barra = ttk.Scrollbar(quadro, orient="vertical")
    txt = tk.Text(quadro, bg=PAINEL, fg="#d3d6db", font=(MONO, 10), bd=0, highlightthickness=0,
                  wrap="word", state="disabled", cursor="arrow", padx=2, pady=2,
                  selectbackground="#3a3f47", yscrollcommand=barra.set, spacing1=1)
    if altura:
        txt.configure(height=altura)
    barra.configure(command=txt.yview)
    barra.pack(side="right", fill="y")
    txt.pack(side="left", fill="both", expand=True)
    txt.tag_configure("titulo", font=(MONO, 10, "bold"), foreground=DESTAQUE)
    txt.tag_configure("suave", foreground=SUAVE)
    for nivel in ("ok", "atencao", "falha"):
        txt.tag_configure(nivel, foreground=COR[nivel], font=(MONO, 10, "bold"))
    txt.quadro = quadro
    return txt


def escrever(txt, linhas):
    txt.configure(state="normal")
    txt.delete("1.0", "end")
    for t, tag in linhas:
        txt.insert("end", t, tag or ())
    txt.configure(state="disabled")
