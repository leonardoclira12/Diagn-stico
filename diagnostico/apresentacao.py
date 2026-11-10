"""Monta o texto do diagnóstico como lista de (texto, tag).

A mesma saída é usada pelo terminal, pela janela e pelo relatório .txt.
Tags: "titulo", "ok", "atencao", "falha" ou "" (texto normal).
"""
from . import analise

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


def secao_diagnostico(d):
    out = [("\nDIAGNÓSTICO DE LENTIDÃO\n", "titulo")]
    achados = analise.analisar(d)
    for a in achados:
        out.append((f" {ROTULOS[a['nivel']]} {a['titulo']}\n", a["nivel"]))
        out.append((f"          {a['detalhe']}\n", ""))
        if a["sugestao"] and a["nivel"] != "ok":
            out.append((f"          -> {a['sugestao']}\n", ""))
    problemas = sum(1 for a in achados if a["nivel"] != "ok")
    resumo = f"{problemas} ponto(s) de atenção." if problemas else "Nenhum problema encontrado."
    out.append((f"\n Resultado: {resumo}\n", "titulo"))
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
    return secao_inventario(d) + secao_diagnostico(d) + secao_inicializacao(d) + secao_monitor(d) + secao_processos(d)


def montar_texto(d):
    return "".join(t for t, _ in montar_linhas(d))
