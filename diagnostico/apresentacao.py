"""Monta o texto do diagnóstico como lista de (texto, tag).

A mesma saída é usada pelo terminal, pela janela e pelo relatório .txt.
Tags: "titulo", "ok", "atencao", "falha" ou "" (texto normal).
"""
from . import analise
from .coletores.limpeza import formatar_tamanho

ROTULOS = {"ok": "[ OK ]", "atencao": "[ !! ]", "falha": "[FALHA]"}


def secao_inventario(d):
    s, c, m = d["sistema"], d["cpu"], d["memoria"]
    out = [
        ("INVENTÁRIO\n", "titulo"),
        (f" Host ....... {s['host']}\n", ""),
        (f" Sistema .... {s['so']} {s['versao_so']} ({s['arquitetura']})\n", ""),
        (f" Uptime ..... {s['uptime_horas']} h\n", ""),
        (f" CPU ........ {c['modelo']} ({c['nucleos_fisicos']}N/{c['nucleos_logicos']}T)\n", ""),
        (f" RAM ........ {m['ram_total_gb']} GB (swap {m['swap_total_gb']} GB)\n", ""),
    ]
    for f in d.get("discos_fisicos", []):
        tam = f" {f['tamanho_gb']} GB," if f["tamanho_gb"] else ""
        out.append((f" Disco ...... {f['nome']} [{f['tipo']}]{tam} saúde: {f['saude']}\n", ""))
    for p in d["disco"]:
        out.append((f" Partição ... {p['ponto']} [{p['fs']}] {p['total_gb']} GB, {p['livre_gb']} GB livres\n", ""))
    return out


def descrever_nota(nota):
    partes = []
    if nota["falhas"]:
        partes.append(f"{nota['falhas']} falha(s)")
    if nota["atencoes"]:
        partes.append(f"{nota['atencoes']} alerta(s)")
    partes.append(f"{nota['oks']} ok")
    return ", ".join(partes)


def secao_diagnostico(d):
    achados = analise.analisar(d)
    nota = analise.resumo_nota(achados)
    out = [("\nDIAGNÓSTICO DE LENTIDÃO\n", "titulo"),
           (f" NOTA GERAL: {nota['titulo']}  ({descrever_nota(nota)})\n\n", nota["nivel"])]
    for a in achados:
        out.append((f" {ROTULOS[a['nivel']]} {a['titulo']}\n", a["nivel"]))
        out.append((f"          {a['detalhe']}\n", ""))
        if a["sugestao"] and a["nivel"] != "ok":
            out.append((f"          -> {a['sugestao']}\n", ""))
    return out


def secao_discos(d):
    out = [("DISCOS FÍSICOS\n", "titulo")]
    fisicos = d.get("discos_fisicos", [])
    if not fisicos:
        out.append(("   Não foi possível identificar os discos físicos neste sistema.\n", ""))
    for f in fisicos:
        tam = f" {f['tamanho_gb']} GB," if f["tamanho_gb"] else ""
        out.append((f"   {f['nome']} [{f['tipo']}]{tam} saúde: {f['saude']}\n", ""))
    out.append(("\nPARTIÇÕES\n", "titulo"))
    for p in d["disco"]:
        out.append((f"   {p['ponto']} [{p['fs']}] {p['total_gb']} GB, {p['livre_gb']} GB livres ({p['uso_percent']}% usado)\n", ""))
    return out


def secao_inicializacao(d):
    itens = d.get("inicializacao")
    if itens is None:
        return []
    out = [(f"\nPROGRAMAS NA INICIALIZAÇÃO ({len(itens)})\n", "titulo")]
    if not itens:
        out.append(("   Nenhum item encontrado.\n", ""))
    for it in sorted(itens, key=lambda x: x["nome"].lower()):
        out.append((f"   {it['nome'][:34]:<34} {it['origem']}\n", ""))
    return out


def secao_bateria(d):
    b = d.get("bateria")
    if b is None:
        return []
    out = [("\nBATERIA\n", "titulo")]
    if not b.get("presente"):
        out.append(("   Nenhuma bateria detectada (computador de mesa).\n", ""))
        return out
    out.append((f" Carga atual ..... {b['percent']}% ({'na tomada' if b['na_tomada'] else 'na bateria'})\n", ""))
    if b.get("saude_pct") is not None:
        out.append((f" Saúde ........... {b['saude_pct']}% da capacidade original\n", ""))
    if b.get("capacidade_projeto_mwh") and b.get("capacidade_atual_mwh"):
        out.append((f" Capacidade ...... {b['capacidade_atual_mwh']} de {b['capacidade_projeto_mwh']} mWh\n", ""))
    if b.get("ciclos"):
        out.append((f" Ciclos de carga . {b['ciclos']}\n", ""))
    if b.get("condicao"):
        out.append((f" Condição ........ {b['condicao']}\n", ""))
    return out


def secao_rede(d):
    r = d.get("rede")
    if not r:
        return []
    out = [("\nREDE\n", "titulo"),
           (f" Internet ....... {'acessível' if r['internet'] else 'sem resposta'}\n", "")]
    for a in r["alvos"]:
        if a["medio_ms"] is None:
            out.append((f" {a['nome']:<14}... sem resposta ({a['falhas']}/{a['tentativas']} falhas)\n", ""))
        else:
            out.append((f" {a['nome']:<14}... média {a['medio_ms']} ms, pico {a['max_ms']} ms, "
                        f"{a['falhas']}/{a['tentativas']} falhas\n", ""))
    dns = r["dns"]
    if dns["medio_ms"] is None:
        out.append((" DNS ........... sem resposta\n", ""))
    else:
        out.append((f" DNS ........... média {dns['medio_ms']} ms, pico {dns['max_ms']} ms"
                    f" ({dns['falhas']} falha(s))\n", ""))
    for ad in r["adaptadores"]:
        vel = f" ({ad['velocidade_mbps']} Mb/s)" if ad["velocidade_mbps"] else ""
        out.append((f" Adaptador ..... {ad['nome']}{vel}\n", ""))
    return out


def secao_limpeza(d):
    itens = d.get("limpeza")
    if not itens:
        return []
    out = [("\nARQUIVOS TEMPORÁRIOS (estimativa)\n", "titulo")]
    for i in itens:
        if not i["acessivel"]:
            out.append((f"   {i['nome']:<30} pasta não encontrada ou sem acesso\n", ""))
        else:
            mais = "+" if i["incompleto"] else ""
            out.append((f"   {i['nome']:<30} {formatar_tamanho(i['bytes'])}{mais} ({i['arquivos']} arquivos)\n", ""))
    out.append((f"   Total removível: {formatar_tamanho(sum(i['bytes'] for i in itens))}\n", "titulo"))
    return out


def secao_monitor(d):
    m = d.get("monitor")
    if not m:
        return []
    out = [(f"\nMONITORAMENTO ({m['duracao_s']} s)\n", "titulo"),
           (f" CPU ....... média {m['cpu_media']}%  pico {m['cpu_pico']}%\n", ""),
           (f" RAM ....... média {m['ram_media']}%  pico {m['ram_pico']}%\n", ""),
           (f" Disco ..... média {m['disco_media_mb_s']} MB/s  pico {m['disco_pico_mb_s']} MB/s\n", ""),
           ("\n Processos que mais usaram CPU (média):\n", "")]
    for p in m["top_cpu"]:
        out.append((f"   {p['nome'][:28]:<28} {p['cpu_media']:>5}%\n", ""))
    out.append(("\n Processos com maior pico de RAM:\n", ""))
    for p in m["top_ram"]:
        out.append((f"   {p['nome'][:28]:<28} {p['ram_max']:>5}%\n", ""))
    return out


def secao_processos(d):
    out = [("\nTOP PROCESSOS (CPU)\n", "titulo")]
    for p in d["processos"]["por_cpu"]:
        out.append((f"   {p['nome'][:28]:<28} {p['cpu_percent']:>5}%\n", ""))
    out.append(("\nTOP PROCESSOS (RAM)\n", "titulo"))
    for p in d["processos"]["por_ram"]:
        out.append((f"   {p['nome'][:28]:<28} {p['ram_percent']:>5}%\n", ""))
    return out


def montar_linhas(d):
    return secao_inventario(d) + secao_diagnostico(d) + secao_inicializacao(d) + secao_bateria(d) + secao_rede(d) + secao_limpeza(d) + secao_monitor(d) + secao_processos(d)


def montar_texto(d):
    return "".join(t for t, _ in montar_linhas(d))


def abas(d):
    """Texto de cada aba da janela."""
    return {
        "Resumo": secao_inventario(d) + secao_diagnostico(d),
        "Inicialização": secao_inicializacao(d),
        "Discos": secao_discos(d),
        "Bateria": secao_bateria(d),
        "Rede": secao_rede(d),
        "Monitoramento": secao_monitor(d),
        "Processos": secao_processos(d),
    }
