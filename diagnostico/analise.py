"""Regras simples para apontar causas prováveis de lentidão.

Cada achado: {"nivel": "ok|atencao|falha", "titulo": str, "detalhe": str, "sugestao": str}
"""

OK, ATENCAO, FALHA = "ok", "atencao", "falha"


def _achado(nivel, titulo, detalhe, sugestao=""):
    return {"nivel": nivel, "titulo": titulo, "detalhe": detalhe, "sugestao": sugestao}


def analisar_cpu(cpu, procs):
    uso = cpu["uso_percent"]
    if uso >= 90:
        pesado = procs["por_cpu"][0] if procs["por_cpu"] else None
        quem = f" Maior consumidor: {pesado['nome']} ({pesado['cpu_percent']}%)." if pesado else ""
        return _achado(FALHA, "CPU saturada", f"Uso em {uso}%.{quem}",
                       "Feche ou investigue o processo que mais consome.")
    if uso >= 70:
        return _achado(ATENCAO, "CPU com uso alto", f"Uso em {uso}%.",
                       "Verifique os processos em segundo plano.")
    return _achado(OK, "CPU", f"Uso em {uso}%.")


def analisar_memoria(mem, procs):
    uso = mem["ram_uso_percent"]
    livre = mem["ram_livre_gb"]
    if uso >= 90 or livre < 1:
        pesado = procs["por_ram"][0] if procs["por_ram"] else None
        quem = f" Maior consumidor: {pesado['nome']} ({pesado['ram_percent']}%)." if pesado else ""
        return _achado(FALHA, "Pouca memória RAM livre",
                       f"Uso em {uso}%, {livre} GB livres.{quem}",
                       "Feche programas pesados ou considere aumentar a RAM.")
    if uso >= 80:
        return _achado(ATENCAO, "RAM com uso alto", f"Uso em {uso}%, {livre} GB livres.",
                       "Evite abrir muitos programas ao mesmo tempo.")
    return _achado(OK, "Memória RAM", f"Uso em {uso}%, {livre} GB livres.")


def analisar_swap(mem):
    if mem["swap_total_gb"] > 0 and mem["swap_uso_percent"] >= 50 and mem["ram_uso_percent"] >= 80:
        return _achado(ATENCAO, "Uso intenso de swap/paginação",
                       f"Swap em {mem['swap_uso_percent']}% com RAM em {mem['ram_uso_percent']}%.",
                       "O sistema está usando o disco como memória: isso causa lentidão.")
    return None


def analisar_discos(discos):
    achados = []
    for d in discos:
        uso, livre = d["uso_percent"], d["livre_gb"]
        nome = f"Disco {d['ponto']}"
        if uso >= 95 or livre < 5:
            achados.append(_achado(FALHA, f"{nome} quase cheio",
                                   f"{uso}% usado, {livre} GB livres.",
                                   "Libere espaço: disco cheio deixa o sistema lento."))
        elif uso >= 85:
            achados.append(_achado(ATENCAO, f"{nome} com pouco espaço",
                                   f"{uso}% usado, {livre} GB livres.",
                                   "Considere limpar arquivos grandes ou temporários."))
        else:
            achados.append(_achado(OK, nome, f"{uso}% usado, {livre} GB livres."))
    return achados


def analisar_uptime(sistema):
    h = sistema["uptime_horas"]
    if h >= 24 * 14:
        return _achado(ATENCAO, "Sistema ligado há muito tempo",
                       f"Uptime de {h} horas (~{round(h / 24)} dias).",
                       "Reinicie o computador para liberar memória e aplicar atualizações.")
    return None


def analisar(dados):
    achados = [
        analisar_cpu(dados["cpu"], dados["processos"]),
        analisar_memoria(dados["memoria"], dados["processos"]),
    ]
    achados += analisar_discos(dados["disco"])
    for extra in (analisar_swap(dados["memoria"]), analisar_uptime(dados["sistema"])):
        if extra:
            achados.append(extra)
    ordem = {FALHA: 0, ATENCAO: 1, OK: 2}
    return sorted(achados, key=lambda a: ordem[a["nivel"]])
