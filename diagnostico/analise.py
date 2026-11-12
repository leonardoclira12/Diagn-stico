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


def analisar_discos_fisicos(discos):
    achados = []
    for d in discos:
        nome = f"{d['nome']} ({d['tipo']})"
        if d["saude"] == "Falhando":
            achados.append(_achado(FALHA, f"Disco com falha: {nome}",
                                   "O sistema reporta o disco como não saudável.",
                                   "Faça backup dos dados agora e troque o disco."))
        elif d["saude"] == "Atenção":
            achados.append(_achado(ATENCAO, f"Disco com alerta de saúde: {nome}",
                                   "O sistema reporta sinais de desgaste ou erros.",
                                   "Faça backup e acompanhe o disco de perto."))
        if d["tipo"] == "HD":
            achados.append(_achado(ATENCAO, f"HD mecânico: {d['nome']}",
                                   "Discos mecânicos são bem mais lentos que SSDs.",
                                   "Trocar por um SSD é a melhoria de velocidade mais perceptível."))
    if discos and not achados:
        achados.append(_achado(OK, "Discos físicos",
                               ", ".join(f"{d['nome']} ({d['tipo']}, {d['saude']})" for d in discos)))
    return achados


def analisar_monitor(m, discos_fisicos=()):
    achados = []
    dur = f"{m['duracao_s']} s"
    quem = m["top_cpu"][0] if m["top_cpu"] else None

    sat = m["cpu_tempo_saturada_pct"]
    if sat >= 30:
        achados.append(_achado(FALHA, "CPU saturada por boa parte do tempo",
                               f"Ficou acima de 90% em {sat}% de {dur} (média {m['cpu_media']}%, pico {m['cpu_pico']}%).",
                               "Veja os processos que mais consomem CPU abaixo."))
    elif sat >= 10 or m["cpu_pico"] >= 98:
        achados.append(_achado(ATENCAO, "Picos de CPU durante o monitoramento",
                               f"Média {m['cpu_media']}%, pico {m['cpu_pico']}%, acima de 90% em {sat}% do tempo.",
                               "Picos curtos são normais; se a lentidão coincide com eles, investigue o processo."))
    else:
        achados.append(_achado(OK, "CPU no monitoramento", f"Média {m['cpu_media']}%, pico {m['cpu_pico']}% em {dur}."))

    alta = m["ram_tempo_alta_pct"]
    if alta >= 30:
        achados.append(_achado(FALHA, "RAM no limite por boa parte do tempo",
                               f"Ficou acima de 90% em {alta}% de {dur} (média {m['ram_media']}%, pico {m['ram_pico']}%).",
                               "Feche programas pesados ou considere mais memória."))
    elif alta >= 10:
        achados.append(_achado(ATENCAO, "RAM chegou perto do limite",
                               f"Média {m['ram_media']}%, pico {m['ram_pico']}%, acima de 90% em {alta}% do tempo.",
                               "Evite abrir muitos programas ao mesmo tempo."))
    else:
        achados.append(_achado(OK, "RAM no monitoramento", f"Média {m['ram_media']}%, pico {m['ram_pico']}% em {dur}."))

    tem_hd = any(d["tipo"] == "HD" for d in discos_fisicos)
    if tem_hd and m["disco_media_mb_s"] >= 20:
        achados.append(_achado(ATENCAO, "HD mecânico muito ocupado",
                               f"Média de {m['disco_media_mb_s']} MB/s de leitura e escrita (pico {m['disco_pico_mb_s']} MB/s).",
                               "HD sob uso contínuo trava o sistema inteiro; um SSD resolve."))
    else:
        achados.append(_achado(OK, "Disco no monitoramento",
                               f"Média {m['disco_media_mb_s']} MB/s, pico {m['disco_pico_mb_s']} MB/s."))

    if quem and quem["cpu_media"] >= 25:
        achados.append(_achado(ATENCAO, f"Processo pesado: {quem['nome']}",
                               f"Usou em média {quem['cpu_media']}% da CPU durante o monitoramento.",
                               "Feche ou investigue esse programa."))
    return achados


def analisar_bateria(b):
    if not b or not b.get("presente"):
        return None
    saude, ciclos, cond = b.get("saude_pct"), b.get("ciclos"), (b.get("condicao") or "").lower()
    ciclos_txt = f", {ciclos} ciclos" if ciclos else ""
    if saude is not None and saude < 60 or "poor" in cond or "service" in cond or "replace" in cond:
        return _achado(FALHA, "Bateria muito desgastada",
                       f"Capacidade atual em {saude}% da original{ciclos_txt}." if saude is not None
                       else f"Condição reportada: {b.get('condicao')}.",
                       "A autonomia cai muito e o notebook pode desligar sozinho. Considere trocar a bateria.")
    if saude is not None and saude < 80 or "fair" in cond:
        return _achado(ATENCAO, "Bateria com desgaste",
                       f"Capacidade atual em {saude}% da original{ciclos_txt}." if saude is not None
                       else f"Condição reportada: {b.get('condicao')}.",
                       "A bateria já segura menos carga. Acompanhe e planeje a troca.")
    if ciclos and ciclos >= 1000:
        return _achado(ATENCAO, "Bateria com muitos ciclos de carga",
                       f"{ciclos} ciclos de carga.", "Baterias costumam perder desempenho perto de 1000 ciclos.")
    if saude is not None:
        return _achado(OK, "Bateria", f"Capacidade em {saude}% da original{ciclos_txt}; carga atual {b['percent']}%.")
    return _achado(OK, "Bateria", f"Carga atual em {b['percent']}% (desgaste não informado pelo sistema).")


def analisar_rede(r):
    if not r:
        return []
    dns = r["dns"]
    alvos = r["alvos"]
    medidos = [a for a in alvos if a["medio_ms"] is not None]
    if not r["internet"]:
        return [_achado(FALHA, "Sem acesso à internet",
                        "Nenhum teste de conexão nem de DNS respondeu.",
                        "Verifique cabo/Wi-Fi e o roteador. Se a rede bloqueia testes externos, pode ser alarme falso.")]
    achados = []
    if medidos:
        tent = sum(a["tentativas"] for a in alvos)
        perdas = sum(a["falhas"] for a in alvos)
        pct = round(100 * perdas / tent)
        lat = round(sum(a["medio_ms"] for a in medidos) / len(medidos), 1)
        pico = max(a["max_ms"] for a in medidos)
        if pct >= 40:
            achados.append(_achado(FALHA, "Conexão muito instável",
                                   f"{pct}% das tentativas de conexão falharam (latência média {lat} ms).",
                                   "Verifique o sinal do Wi-Fi, o cabo e o roteador."))
        elif pct >= 20:
            achados.append(_achado(ATENCAO, "Perda de pacotes na conexão",
                                   f"{pct}% das tentativas falharam (latência média {lat} ms).",
                                   "Instabilidade de Wi-Fi ou do provedor. Teste de novo e, se persistir, cabo de rede."))
        elif lat >= 300:
            achados.append(_achado(FALHA, "Latência de rede muito alta",
                                   f"Média de {lat} ms (pico {pico} ms).",
                                   "A internet está lenta: Wi-Fi fraco, rede congestionada ou problema no provedor."))
        elif lat >= 120:
            achados.append(_achado(ATENCAO, "Latência de rede alta",
                                   f"Média de {lat} ms (pico {pico} ms).",
                                   "Pode deixar sites e chamadas lentos. Teste perto do roteador ou por cabo."))
        else:
            achados.append(_achado(OK, "Latência de rede", f"Média de {lat} ms, {pct}% de perda."))
    else:
        achados.append(_achado(OK, "Latência de rede",
                               "Conexões diretas de teste foram bloqueadas (rede corporativa?); DNS respondeu."))
    if dns["falhas"] and dns["medio_ms"] is None:
        achados.append(_achado(FALHA, "DNS não responde", "Nenhum nome foi resolvido.",
                               "Troque o servidor DNS (ex.: 1.1.1.1 ou 8.8.8.8) ou reinicie o roteador."))
    elif dns["falhas"]:
        achados.append(_achado(ATENCAO, "Falhas de DNS",
                               f"{dns['falhas']} de {dns['total']} nomes não foram resolvidos.",
                               "Troque o servidor DNS (ex.: 1.1.1.1 ou 8.8.8.8)."))
    elif dns["medio_ms"] >= 400:
        achados.append(_achado(ATENCAO, "DNS lento",
                               f"Resolver nomes levou em média {dns['medio_ms']} ms.",
                               "Sites demoram a abrir mesmo com internet boa. Trocar o DNS (ex.: 1.1.1.1) costuma resolver."))
    else:
        achados.append(_achado(OK, "DNS", f"Resolução em média {dns['medio_ms']} ms."))
    return achados


def analisar_limpeza(itens):
    if not itens:
        return None
    total = sum(i["bytes"] for i in itens)
    gb = total / (1024 ** 3)
    texto = f"{gb:.2f} GB" if gb >= 1 else f"{total / (1024 ** 2):.0f} MB"
    if gb >= 5:
        return _achado(ATENCAO, "Muitos arquivos temporários", f"{texto} em arquivos temporários que podem ser removidos.",
                       "Use a limpeza (aba Limpeza) para liberar espaço.")
    return _achado(OK, "Arquivos temporários", f"{texto} que podem ser removidos.")


def analisar_inicializacao(itens):
    n = len(itens)
    if n >= 20:
        return _achado(FALHA, "Muitos programas na inicialização",
                       f"{n} programas iniciam junto com o sistema.",
                       "Desative os que você não usa todo dia: o boot e o uso inicial ficam bem mais lentos.")
    if n >= 10:
        return _achado(ATENCAO, "Vários programas na inicialização",
                       f"{n} programas iniciam junto com o sistema.",
                       "Revise a lista e desative o que não precisa abrir sozinho.")
    return _achado(OK, "Programas na inicialização", f"{n} programa(s) iniciam com o sistema.")


def analisar(dados):
    achados = [
        analisar_cpu(dados["cpu"], dados["processos"]),
        analisar_memoria(dados["memoria"], dados["processos"]),
    ]
    achados += analisar_discos(dados["disco"])
    achados += analisar_discos_fisicos(dados.get("discos_fisicos", []))
    extra_bat = analisar_bateria(dados.get("bateria"))
    if extra_bat:
        achados.append(extra_bat)
    achados += analisar_rede(dados.get("rede"))
    extra_limp = analisar_limpeza(dados.get("limpeza"))
    if extra_limp:
        achados.append(extra_limp)
    if dados.get("monitor"):
        achados += analisar_monitor(dados["monitor"], dados.get("discos_fisicos", []))
    if "inicializacao" in dados:
        achados.append(analisar_inicializacao(dados["inicializacao"]))
    for extra in (analisar_swap(dados["memoria"]), analisar_uptime(dados["sistema"])):
        if extra:
            achados.append(extra)
    ordem = {FALHA: 0, ATENCAO: 1, OK: 2}
    return sorted(achados, key=lambda a: ordem[a["nivel"]])


def resumo_nota(achados):
    """Nota geral: CRÍTICO se há falha, ATENÇÃO se há alerta, senão SAUDÁVEL."""
    falhas = sum(1 for a in achados if a["nivel"] == FALHA)
    atencoes = sum(1 for a in achados if a["nivel"] == ATENCAO)
    oks = sum(1 for a in achados if a["nivel"] == OK)
    if falhas:
        nivel, titulo = FALHA, "CRÍTICO"
    elif atencoes:
        nivel, titulo = ATENCAO, "ATENÇÃO"
    else:
        nivel, titulo = OK, "SAUDÁVEL"
    return {"nivel": nivel, "titulo": titulo, "falhas": falhas, "atencoes": atencoes, "oks": oks}
