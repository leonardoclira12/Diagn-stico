"""Interface gráfica: tema escuro, menu lateral, nota geral e explicações curtas."""
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from . import __version__, analise, apresentacao, atalhos, monitor, relatorio, tema
from .coleta import coletar_tudo
from .coletores import limpeza
from .tema import (BG, BORDA, COR, DESTAQUE, FONTE, MENU, PAINEL, PAINEL2, SUAVE, TEXTO, Anel, Botao,
                   Cartao, Grafico, cor_por_uso, criar_texto, escrever)

PAGINAS = ["Resumo", "Inicialização", "Discos", "Bateria", "Rede", "Sistema", "Segurança", "Hardware",
           "Monitoramento", "Processos", "Limpeza", "Ferramentas", "Relatório"]
PAGINAS_TEXTO = ["Inicialização", "Discos", "Bateria", "Rede", "Sistema", "Segurança", "Hardware",
                 "Processos", "Relatório"]
# Botões de atalho mostrados dentro de cada página (só os que existem no sistema atual)
ATALHOS_PAGINA = {
    "Inicialização": ["inicializacao"], "Discos": ["armazenamento", "disco"], "Rede": ["rede"],
    "Sistema": ["atualizacoes", "dispositivos", "eventos"], "Segurança": ["seguranca"], "Processos": ["tarefas"],
}
DURACOES = ["30 segundos", "1 minuto", "2 minutos", "5 minutos", "10 minutos"]

# Explicações curtas, só para o usuário entender o que está vendo.
EXPLICACAO = {
    "nota": "Resume todos os testes. Quanto mais alta, mais saudável o computador.",
    "problemas": "Só o que está atrapalhando o desempenho, com a sugestão de como resolver.",
    "computador": "Dados básicos desta máquina.",
    "cpu": "O processador faz os cálculos. Perto de 100% por muito tempo deixa tudo lento.",
    "ram": "Memória de trabalho. Quando enche, o sistema usa o disco e fica lento.",
    "disco": "Espaço usado no disco principal. Com menos de 10% livre, o computador desacelera.",
    "Inicialização": "Programas que abrem sozinhos ao ligar e quanto tempo o sistema levou para iniciar. Quanto mais programas, mais demora.",
    "Discos": "SSD é muito mais rápido que HD. A saúde indica se o disco está falhando.",
    "Bateria": "Saúde é quanto da capacidade original ainda resta. Abaixo de 80%, a duração cai bastante.",
    "Rede": "Latência é o tempo de resposta (menor é melhor). DNS traduz o nome de um site em endereço.",
    "Sistema": "Atualizações pendentes, dispositivos com driver com defeito e erros graves recentes (telas azuis, desligamentos).",
    "Segurança": "Antivírus e firewall protegem contra vírus e invasões. Desligados ou desatualizados, o computador fica exposto.",
    "Hardware": "As peças do computador. Útil para saber o que dá para melhorar e para abrir chamados.",
    "Ferramentas": "Atalhos para as ferramentas do sistema. Eles só abrem os programas, não mudam nada.",
    "Monitoramento": "Acompanha o computador por um tempo para pegar picos que um teste rápido perde.",
    "Processos": "Programas que mais usam processador e memória neste momento.",
    "Limpeza": "Arquivos temporários ocupam espaço e podem ser apagados com segurança.",
    "Relatório": "Todos os resultados, no mesmo texto do arquivo salvo.",
}
VAZIO = {
    "Inicialização": "Execute o diagnóstico para ver os programas que abrem com o sistema.",
    "Discos": "Execute o diagnóstico para ver tipo e saúde dos discos.",
    "Bateria": "Execute o diagnóstico para ver a bateria.",
    "Sistema": "Execute o diagnóstico para ver atualizações, drivers e erros recentes.",
    "Segurança": "Execute o diagnóstico para ver antivírus e firewall.",
    "Hardware": "Execute o diagnóstico para ver as peças do computador.",
    "Rede": "Execute o diagnóstico para testar a rede.",
    "Processos": "Execute o diagnóstico para ver os processos que mais consomem.",
    "Relatório": "Execute o diagnóstico para gerar o relatório completo.",
}
TITULO_CARTAO = {
    "Inicialização": "Programas que abrem com o sistema",
    "Discos": "Discos e partições",
    "Bateria": "Estado da bateria",
    "Sistema": "Atualizações, drivers e erros recentes",
    "Segurança": "Antivírus e firewall",
    "Hardware": "Peças do computador",
    "Rede": "Teste de rede",
    "Processos": "Maiores consumidores",
    "Relatório": "Relatório completo",
}


class App:
    def __init__(self, root):
        self.root = root
        self.dados = None
        self.fila = queue.Queue()
        self.parar_ev = threading.Event()
        self.ao_fim = None
        self.aba_final = "Resumo"
        self.pagina_atual = None
        self.itens_limpeza = None
        self.vars_limpeza = {}
        self.textos, self.paginas, self.menu_itens = {}, {}, {}

        root.title(f"Diagnóstico v{__version__}")
        root.geometry("1120x740")
        root.minsize(980, 640)
        root.configure(bg=BG)
        tema.aplicar_estilo(root)
        root.columnconfigure(1, weight=1)
        root.rowconfigure(0, weight=1)

        self._criar_menu()
        self.principal = tk.Frame(root, bg=BG)
        self.principal.grid(row=0, column=1, sticky="nsew")
        self.principal.columnconfigure(0, weight=1)
        self.principal.rowconfigure(2, weight=1)
        self._criar_cabecalho()
        tk.Frame(self.principal, bg=BORDA, height=1).grid(row=1, column=0, sticky="ew", padx=24)
        self.area = tk.Frame(self.principal, bg=BG)
        self.area.grid(row=2, column=0, sticky="nsew", padx=24, pady=(16, 0))
        self.area.columnconfigure(0, weight=1)
        self.area.rowconfigure(0, weight=1)
        self._criar_rodape()

        self._criar_resumo()
        for nome in PAGINAS_TEXTO:
            self._criar_pagina_texto(nome)
        self._criar_monitoramento()
        self._criar_limpeza()
        self._criar_ferramentas()
        self.mostrar_pagina("Resumo")

    # ================= estrutura =================
    def _criar_menu(self):
        menu = tk.Frame(self.root, bg=MENU, width=206)
        menu.grid(row=0, column=0, sticky="ns")
        menu.pack_propagate(False)
        tk.Label(menu, text="DIAGNÓSTICO", fg=DESTAQUE, bg=MENU, font=(FONTE, 14, "bold"),
                 anchor="w").pack(fill="x", padx=22, pady=(24, 0))
        tk.Label(menu, text="do seu computador", fg=SUAVE, bg=MENU, font=(FONTE, 9),
                 anchor="w").pack(fill="x", padx=22, pady=(0, 24))
        for nome in PAGINAS:
            linha = tk.Frame(menu, bg=MENU, cursor="hand2")
            linha.pack(fill="x")
            barra = tk.Frame(linha, bg=MENU, width=3)
            barra.pack(side="left", fill="y")
            rot = tk.Label(linha, text=nome, bg=MENU, fg=SUAVE, font=(FONTE, 10), anchor="w",
                           padx=19, pady=9, cursor="hand2")
            rot.pack(side="left", fill="x", expand=True)
            for w in (linha, rot, barra):
                w.bind("<Button-1>", lambda _e, n=nome: self.mostrar_pagina(n))
            rot.bind("<Enter>", lambda _e, n=nome: self._hover(n, True))
            rot.bind("<Leave>", lambda _e, n=nome: self._hover(n, False))
            self.menu_itens[nome] = (linha, barra, rot)
        tk.Label(menu, text=f"v{__version__}", fg=SUAVE, bg=MENU, font=(FONTE, 8),
                 anchor="w").pack(side="bottom", fill="x", padx=22, pady=16)

    def _hover(self, nome, dentro):
        if nome != self.pagina_atual:
            self.menu_itens[nome][2].configure(fg=TEXTO if dentro else SUAVE)

    def _criar_cabecalho(self):
        cab = tk.Frame(self.principal, bg=BG)
        cab.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 16))
        esq = tk.Frame(cab, bg=BG)
        esq.pack(side="left")
        self.btn_rodar = Botao(esq, "EXECUTAR DIAGNÓSTICO", self.executar, primario=True)
        self.btn_rodar.pack(side="left")
        self.btn_salvar = Botao(esq, "Salvar relatório", self.salvar)
        self.btn_salvar.pack(side="left", padx=10)
        self.btn_salvar.configure(state="disabled")
        self.titulo = tk.Label(cab, text="RESUMO", fg=TEXTO, bg=BG, font=(FONTE, 22, "bold"))
        self.titulo.pack(side="right")

    def _criar_rodape(self):
        rod = tk.Frame(self.principal, bg=BG)
        rod.grid(row=3, column=0, sticky="ew", padx=24, pady=(8, 14))
        self.status = tk.Label(rod, text="Pronto.", fg=SUAVE, bg=BG, font=(FONTE, 9), anchor="w")
        self.status.pack(side="left")
        self.barra = ttk.Progressbar(rod, mode="determinate", length=240)
        self.barra.pack(side="right")

    def _nova_pagina(self, nome):
        f = tk.Frame(self.area, bg=BG)
        f.grid(row=0, column=0, sticky="nsew")
        f.grid_remove()
        self.paginas[nome] = f
        return f

    def mostrar_pagina(self, nome):
        for n, f in self.paginas.items():
            f.grid_remove()
        self.paginas[nome].grid()
        for n, (linha, barra, rot) in self.menu_itens.items():
            ativo = n == nome
            linha.configure(bg="#1a1c20" if ativo else MENU)
            rot.configure(bg="#1a1c20" if ativo else MENU, fg="white" if ativo else SUAVE,
                          font=(FONTE, 10, "bold" if ativo else "normal"))
            barra.configure(bg=DESTAQUE if ativo else MENU)
        self.pagina_atual = nome
        self.titulo.configure(text=nome.upper())

    # ================= páginas =================
    def _medidor(self, pai, linha, coluna, titulo, explicacao, padx):
        c = Cartao(pai, titulo, explicacao)
        c.grid(row=linha, column=coluna, sticky="nsew", padx=padx, pady=(8, 0))
        anel = Anel(c.corpo, 112)
        anel.pack(side="left", padx=(0, 16))
        det = tk.Label(c.corpo, text="Execute o diagnóstico.", fg=SUAVE, bg=PAINEL, font=(FONTE, 9),
                       anchor="w", justify="left")
        det.pack(side="left", fill="x", expand=True)
        det.bind("<Configure>", lambda e, w=det: w.configure(wraplength=max(e.width - 4, 100)))
        return anel, det

    def _criar_resumo(self):
        p = self._nova_pagina("Resumo")
        for c in range(3):
            p.columnconfigure(c, weight=1, uniform="r")
        p.rowconfigure(0, weight=1, uniform="l")
        p.rowconfigure(1, weight=1, uniform="l")

        c = Cartao(p, "Nota geral", EXPLICACAO["nota"])
        c.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.anel_nota = Anel(c.corpo, 124)
        self.anel_nota.pack(side="left", padx=(0, 16))
        lado = tk.Frame(c.corpo, bg=PAINEL)
        lado.pack(side="left", fill="both", expand=True)
        self.lbl_nota = tk.Label(lado, text="SEM ANÁLISE", fg=COR["neutro"], bg=PAINEL,
                                 font=(FONTE, 15, "bold"), anchor="w")
        self.lbl_nota.pack(fill="x", pady=(20, 2))
        self.lbl_nota_sub = tk.Label(lado, text="Clique em EXECUTAR DIAGNÓSTICO.", fg=SUAVE, bg=PAINEL,
                                     font=(FONTE, 9), anchor="w", justify="left", wraplength=170)
        self.lbl_nota_sub.pack(fill="x")
        self.lbl_nota_sub.bind("<Configure>", lambda e, w=self.lbl_nota_sub: w.configure(wraplength=max(e.width - 4, 100)))

        c = Cartao(p, "O que está pesando", EXPLICACAO["problemas"])
        c.grid(row=0, column=1, sticky="nsew", padx=8)
        self.txt_problemas = criar_texto(c.corpo)
        self.txt_problemas.quadro.pack(fill="both", expand=True)
        escrever(self.txt_problemas, [("Aqui aparecem os problemas encontrados.\n", "suave")])

        c = Cartao(p, "Este computador", EXPLICACAO["computador"])
        c.grid(row=0, column=2, sticky="nsew", padx=(8, 0))
        self.txt_pc = criar_texto(c.corpo)
        self.txt_pc.quadro.pack(fill="both", expand=True)
        escrever(self.txt_pc, [("—\n", "suave")])

        self.anel_cpu, self.det_cpu = self._medidor(p, 1, 0, "Processador (CPU)", EXPLICACAO["cpu"], (0, 8))
        self.anel_ram, self.det_ram = self._medidor(p, 1, 1, "Memória (RAM)", EXPLICACAO["ram"], 8)
        self.anel_disco, self.det_disco = self._medidor(p, 1, 2, "Espaço em disco", EXPLICACAO["disco"], (8, 0))

    def _criar_pagina_texto(self, nome):
        p = self._nova_pagina(nome)
        p.columnconfigure(0, weight=1)
        p.rowconfigure(0, weight=1)
        c = Cartao(p, TITULO_CARTAO.get(nome, nome), EXPLICACAO[nome])
        c.grid(row=0, column=0, sticky="nsew")
        disp = {a["id"]: a for a in atalhos.disponiveis()}
        ids = [i for i in ATALHOS_PAGINA.get(nome, []) if i in disp]
        if ids:
            linha = tk.Frame(c.corpo, bg=PAINEL)
            linha.pack(fill="x", pady=(0, 8))
            for i in ids:
                Botao(linha, f"Abrir: {disp[i]['rotulo']}", lambda i=i: self._abrir_atalho(i)).pack(side="left", padx=(0, 8))
        t = criar_texto(c.corpo)
        t.quadro.pack(fill="both", expand=True)
        self.textos[nome] = t
        escrever(t, [(VAZIO[nome] + "\n", "suave")])

    def _criar_monitoramento(self):
        p = self._nova_pagina("Monitoramento")
        p.columnconfigure(0, weight=1)
        p.rowconfigure(2, weight=1)
        c = Cartao(p, "Monitoramento", EXPLICACAO["Monitoramento"])
        c.grid(row=0, column=0, sticky="ew")
        linha = tk.Frame(c.corpo, bg=PAINEL)
        linha.pack(fill="x", pady=(2, 0))
        tk.Label(linha, text="Monitorar por:", fg=TEXTO, bg=PAINEL, font=(FONTE, 10)).pack(side="left")
        self.combo = ttk.Combobox(linha, values=DURACOES, width=14, font=(FONTE, 10))
        self.combo.set("1 minuto")
        self.combo.pack(side="left", padx=10)
        self.btn_monitorar = Botao(linha, "MONITORAR", self.monitorar, primario=True)
        self.btn_monitorar.pack(side="left")
        self.btn_parar = Botao(linha, "Parar", self.parar)
        self.btn_parar.pack(side="left", padx=8)
        self.btn_parar.configure(state="disabled")

        graf = tk.Frame(p, bg=BG)
        graf.grid(row=1, column=0, sticky="ew", pady=8)
        for i in range(3):
            graf.columnconfigure(i, weight=1, uniform="g")
        self.g_cpu = Grafico(graf, "CPU", "%", maximo=100, cor=DESTAQUE)
        self.g_ram = Grafico(graf, "Memória (RAM)", "%", maximo=100, cor="#58a6ff")
        self.g_disco = Grafico(graf, "Disco", " MB/s", cor=COR["ok"])
        for i, g in enumerate((self.g_cpu, self.g_ram, self.g_disco)):
            g.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 6, 0 if i == 2 else 6))

        r = Cartao(p, "Resultado")
        r.grid(row=2, column=0, sticky="nsew")
        self.textos["Monitoramento"] = criar_texto(r.corpo)
        self.textos["Monitoramento"].quadro.pack(fill="both", expand=True)
        escrever(self.textos["Monitoramento"],
                 [("Escolha um tempo e clique em MONITORAR para acompanhar a máquina.\n", "suave")])

    def _criar_limpeza(self):
        p = self._nova_pagina("Limpeza")
        p.columnconfigure(0, weight=1)
        p.rowconfigure(0, weight=1)
        c = Cartao(p, "Limpeza de temporários", EXPLICACAO["Limpeza"])
        c.grid(row=0, column=0, sticky="nsew")
        topo = tk.Frame(c.corpo, bg=PAINEL)
        topo.pack(fill="x", pady=(2, 8))
        self.btn_calc = Botao(topo, "CALCULAR ESPAÇO", self.calcular_limpeza, primario=True)
        self.btn_calc.pack(side="left")
        self.btn_limpar = Botao(topo, "Limpar selecionados", self.limpar_selecionados)
        self.btn_limpar.pack(side="left", padx=10)
        self.btn_limpar.configure(state="disabled")
        self.total_limpeza = tk.Label(topo, text="", fg=TEXTO, bg=PAINEL, font=(FONTE, 10, "bold"))
        self.total_limpeza.pack(side="left", padx=8)
        tk.Label(c.corpo, justify="left", anchor="w", fg=SUAVE, bg=PAINEL, font=(FONTE, 9),
                 text="Só são removidos arquivos com mais de 24 horas, dentro das pastas listadas abaixo.\n"
                      "Nada é apagado sem a sua confirmação. Arquivos em uso são ignorados.").pack(fill="x", pady=(0, 12))
        self.lista_limpeza = tk.Frame(c.corpo, bg=PAINEL)
        self.lista_limpeza.pack(fill="both", expand=True)
        self._lista_vazia("Clique em CALCULAR ESPAÇO para ver quanto dá para liberar.")

    def _criar_ferramentas(self):
        p = self._nova_pagina("Ferramentas")
        p.columnconfigure(0, weight=1)
        p.rowconfigure(0, weight=1)
        c = Cartao(p, "Atalhos do sistema", EXPLICACAO["Ferramentas"])
        c.grid(row=0, column=0, sticky="nsew")
        lista = atalhos.disponiveis()
        if not lista:
            tk.Label(c.corpo, text="Os atalhos estão disponíveis no Windows e no Mac.", fg=SUAVE, bg=PAINEL,
                     font=(FONTE, 10), anchor="w").pack(fill="x")
        grade = tk.Frame(c.corpo, bg=PAINEL)
        grade.pack(fill="x")
        grade.columnconfigure(0, minsize=270)
        grade.columnconfigure(1, weight=1)
        for n, a in enumerate(lista):
            Botao(grade, a["rotulo"], lambda i=a["id"]: self._abrir_atalho(i)).grid(
                row=n, column=0, sticky="ew", pady=4, padx=(0, 16))
            tk.Label(grade, text=a["dica"], fg=SUAVE, bg=PAINEL, font=(FONTE, 9), anchor="w").grid(
                row=n, column=1, sticky="w")
        if atalhos.SO == "Windows":
            tk.Frame(c.corpo, bg=BORDA, height=1).pack(fill="x", pady=16)
            adm = atalhos.e_administrador()
            tk.Label(c.corpo, text="Executando como administrador: " + ("sim" if adm else "não"),
                     fg=COR["ok"] if adm else TEXTO, bg=PAINEL, font=(FONTE, 10, "bold"), anchor="w").pack(fill="x")
            tk.Label(c.corpo, fg=SUAVE, bg=PAINEL, font=(FONTE, 9), anchor="w", justify="left",
                     text="Alguns dados (registro de eventos, tempo de inicialização) só aparecem com permissão de administrador."
                     ).pack(fill="x", pady=(2, 8))
            b = Botao(c.corpo, "REABRIR COMO ADMINISTRADOR", self._reabrir_admin, primario=not adm)
            b.pack(anchor="w")
            if adm:
                b.configure(state="disabled")

    def _abrir_atalho(self, id_):
        if not atalhos.abrir(id_):
            messagebox.showwarning("Não foi possível abrir", "Não consegui abrir essa ferramenta neste computador.")

    def _reabrir_admin(self):
        if not messagebox.askyesno("Reabrir como administrador",
                                   "O Windows vai pedir a sua permissão e o app será reaberto.\nContinuar?"):
            return
        if atalhos.reabrir_como_administrador():
            self.root.destroy()
        else:
            messagebox.showwarning("Permissão não concedida", "O app continua aberto sem permissão de administrador.")

    # ================= limpeza =================
    def _lista_vazia(self, texto):
        for w in self.lista_limpeza.winfo_children():
            w.destroy()
        tk.Label(self.lista_limpeza, text=texto, anchor="w", fg=SUAVE, bg=PAINEL, font=(FONTE, 10)).pack(fill="x")

    def _mostrar_limpeza(self, itens):
        self.itens_limpeza = itens
        if self.dados is not None:
            self.dados = dict(self.dados, limpeza=itens)
            self._atualizar()
        for w in self.lista_limpeza.winfo_children():
            w.destroy()
        self.vars_limpeza = {}
        for i in itens:
            linha = tk.Frame(self.lista_limpeza, bg=PAINEL)
            linha.pack(fill="x", pady=4)
            utilizavel = i["acessivel"] and i["bytes"] > 0
            var = tk.BooleanVar(value=utilizavel)
            var.trace_add("write", lambda *_: self._atualizar_total_limpeza())
            self.vars_limpeza[i["id"]] = var
            if i["acessivel"]:
                mais = "+" if i["incompleto"] else ""
                rotulo = f"{i['nome']} — {limpeza.formatar_tamanho(i['bytes'])}{mais} ({i['arquivos']} arquivos)"
            else:
                rotulo = f"{i['nome']} — pasta não encontrada ou sem acesso"
            tk.Checkbutton(linha, text=rotulo, variable=var, anchor="w", bg=PAINEL, fg=TEXTO,
                           selectcolor=PAINEL2, activebackground=PAINEL, activeforeground=TEXTO,
                           disabledforeground=SUAVE, highlightthickness=0, bd=0, font=(FONTE, 10, "bold"),
                           state="normal" if utilizavel else "disabled").pack(fill="x")
            tk.Label(linha, text=f"{i['explicacao']}  Pasta: {i['pasta']}", anchor="w", fg=SUAVE, bg=PAINEL,
                     font=(FONTE, 8)).pack(fill="x", padx=26)
        self._atualizar_total_limpeza()

    def _selecionados(self):
        return [i for i in (self.itens_limpeza or [])
                if self.vars_limpeza.get(i["id"]) and self.vars_limpeza[i["id"]].get()]

    def _atualizar_total_limpeza(self):
        sel = self._selecionados()
        total = sum(i["bytes"] for i in sel)
        self.total_limpeza.configure(text=f"Selecionado: {limpeza.formatar_tamanho(total)}" if sel else "Nada selecionado")
        self.btn_limpar.configure(state="normal" if sel else "disabled")

    # ================= atualização da tela =================
    def _atualizar(self):
        d = self.dados
        achados = analise.analisar(d)
        nota = analise.resumo_nota(achados)
        cor = COR[nota["nivel"]]
        self.anel_nota.definir(nota["pontuacao"], str(nota["pontuacao"]), "de 100", cor)
        self.lbl_nota.configure(text=nota["titulo"], fg=cor)
        self.lbl_nota_sub.configure(text=apresentacao.descrever_nota(nota))

        linhas = []
        for a in achados:
            if a["nivel"] == "ok":
                continue
            linhas += [(f"● {a['titulo']}\n", a["nivel"]), (f"{a['detalhe']}\n", "")]
            if a["sugestao"]:
                linhas.append((f"→ {a['sugestao']}\n", "suave"))
            linhas.append(("\n", ""))
        escrever(self.txt_problemas, linhas or [("Nenhum problema encontrado.\n", "ok")])

        s, c, m = d["sistema"], d["cpu"], d["memoria"]
        escrever(self.txt_pc, [
            (f"{s['host']}\n", "titulo"),
            (f"{s['so']} {s['versao_so']} ({s['arquitetura']})\n", ""),
            ("Processador\n", "suave"),
            (f"{c['modelo']}\n{c['nucleos_fisicos']} núcleos / {c['nucleos_logicos']} threads\n", ""),
            ("Memória · tempo ligado\n", "suave"),
            (f"{m['ram_total_gb']} GB · {s['uptime_horas']} h\n", ""),
        ])

        cpu = c["uso_percent"]
        self.anel_cpu.definir(cpu, f"{cpu:.0f}%", "em uso", cor_por_uso(cpu))
        freq = f"\n{c['freq_atual_mhz']} MHz" if c.get("freq_atual_mhz") else ""
        self.det_cpu.configure(fg=TEXTO, text=f"{c['modelo']}\n{c['nucleos_fisicos']} núcleos / {c['nucleos_logicos']} threads{freq}")
        ram = m["ram_uso_percent"]
        self.anel_ram.definir(ram, f"{ram:.0f}%", "em uso", cor_por_uso(ram, 80, 90))
        self.det_ram.configure(fg=TEXTO, text=f"{m['ram_usada_gb']} de {m['ram_total_gb']} GB usados\n{m['ram_livre_gb']} GB livres")
        if d["disco"]:
            pt = d["disco"][0]
            self.anel_disco.definir(pt["uso_percent"], f"{pt['uso_percent']:.0f}%", "usado", cor_por_uso(pt["uso_percent"], 85, 95))
            self.det_disco.configure(fg=TEXTO, text=f"{pt['ponto']}\n{pt['livre_gb']} GB livres de {pt['total_gb']} GB")

        conteudo = apresentacao.abas(d)
        conteudo["Relatório"] = apresentacao.montar_linhas(d)
        for nome, t in self.textos.items():
            if nome == "Monitoramento":
                linhas_m = conteudo.get(nome)
                if linhas_m:
                    escrever(t, linhas_m)
            else:
                escrever(t, conteudo.get(nome) or [(VAZIO[nome] + "\n", "suave")])

    def _ocupado(self, ocupado, pode_parar=False):
        estado = "disabled" if ocupado else "normal"
        for b in (self.btn_rodar, self.btn_monitorar, self.btn_calc):
            b.configure(state=estado)
        self.combo.configure(state="disabled" if ocupado else "normal")
        self.btn_parar.configure(state="normal" if (ocupado and pode_parar) else "disabled")
        self.btn_salvar.configure(state="disabled" if (ocupado or not self.dados) else "normal")
        if ocupado:
            self.btn_limpar.configure(state="disabled")
        elif self.itens_limpeza:
            self._atualizar_total_limpeza()

    # ================= execução em segundo plano =================
    def _rodar(self, alvo, status, pode_parar=False, aba_final="Resumo", ao_fim=None):
        self.ao_fim = ao_fim
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
        if self.ao_fim:
            self.status.configure(text="Concluído.")
            self.ao_fim(msg[1])
            return
        self.dados = msg[1]
        self._atualizar()
        self.mostrar_pagina(self.aba_final)
        self.btn_salvar.configure(state="normal")
        self.barra.configure(value=self.barra["maximum"])
        self.status.configure(text="Concluído.")

    # ================= ações =================
    def executar(self):
        itens = self.itens_limpeza

        def alvo():
            d = coletar_tudo()
            if itens:
                d["limpeza"] = itens
            return d

        self._rodar(alvo, "Coletando dados e testando a rede (alguns segundos)...")

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
        self.mostrar_pagina("Monitoramento")

        def alvo():
            dados = dict(base) if base else coletar_tudo()
            self.fila.put(("status", f"Monitorando por {monitor.formatar_duracao(segundos)}..."))
            resultado = monitor.monitorar(
                segundos, ao_progresso=lambda a, b: self.fila.put(("prog", a, b)), parar=self.parar_ev,
                ao_amostra=lambda c, r, dk: self.fila.put(("amostra", c, r, dk)))
            if resultado:
                dados["monitor"] = resultado
            return dados

        self._rodar(alvo, "Preparando...", pode_parar=True, aba_final="Monitoramento")

    def parar(self):
        self.parar_ev.set()
        self.btn_parar.configure(state="disabled")
        self.status.configure(text="Encerrando e analisando o que foi coletado...")

    def calcular_limpeza(self):
        self.mostrar_pagina("Limpeza")
        self._rodar(limpeza.estimar, "Calculando arquivos temporários...", ao_fim=self._mostrar_limpeza)

    def limpar_selecionados(self):
        sel = self._selecionados()
        if not sel:
            return
        total = limpeza.formatar_tamanho(sum(i["bytes"] for i in sel))
        nomes = "\n".join(f" • {i['nome']}" for i in sel)
        if not messagebox.askyesno(
                "Confirmar limpeza",
                f"Apagar cerca de {total} de arquivos temporários?\n\n{nomes}\n\n"
                "Só arquivos com mais de 24 horas serão removidos. Isso não pode ser desfeito."):
            return
        ids = [i["id"] for i in sel]
        self._rodar(lambda: limpeza.limpar(ids), "Limpando...", ao_fim=self._fim_limpeza)

    def _fim_limpeza(self, r):
        messagebox.showinfo(
            "Limpeza concluída",
            f"Liberado: {limpeza.formatar_tamanho(r['liberado_bytes'])} ({r['removidos']} arquivos).\n"
            f"{r['falhas']} arquivo(s) em uso ou sem permissão foram ignorados.")
        self.calcular_limpeza()

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
