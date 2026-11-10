"""Exporta o diagnóstico em arquivo de texto."""
import os
from datetime import datetime

from . import analise

ROTULOS = {"ok": "OK", "atencao": "ATENCAO", "falha": "FALHA"}


def gerar_texto(dados):
    s, c, m = dados["sistema"], dados["cpu"], dados["memoria"]
    linhas = [
        "RELATORIO DE DIAGNOSTICO",
        f"Data: {datetime.now():%d/%m/%Y %H:%M:%S}",
        "=" * 60,
        f"Host: {s['host']}",
        f"Sistema: {s['so']} {s['versao_so']} ({s['arquitetura']})",
        f"Uptime: {s['uptime_horas']} h",
        f"CPU: {c['modelo']} - {c['nucleos_fisicos']}N/{c['nucleos_logicos']}T",
        f"RAM: {m['ram_total_gb']} GB (uso {m['ram_uso_percent']}%)",
        "",
        "DISCOS",
    ]
    for d in dados["disco"]:
        linhas.append(f"  {d['ponto']} [{d['fs']}] {d['total_gb']} GB, {d['livre_gb']} GB livres ({d['uso_percent']}%)")
    linhas += ["", "DIAGNOSTICO", "-" * 60]
    for a in analise.analisar(dados):
        linhas.append(f"[{ROTULOS[a['nivel']]}] {a['titulo']} - {a['detalhe']}")
        if a["sugestao"] and a["nivel"] != "ok":
            linhas.append(f"    Sugestao: {a['sugestao']}")
    linhas += ["", "TOP PROCESSOS (CPU)"]
    for p in dados["processos"]["por_cpu"]:
        linhas.append(f"  {p['nome']} - {p['cpu_percent']}% (PID {p['pid']})")
    linhas += ["TOP PROCESSOS (RAM)"]
    for p in dados["processos"]["por_ram"]:
        linhas.append(f"  {p['nome']} - {p['ram_percent']}% (PID {p['pid']})")
    return "\n".join(linhas) + "\n"


def salvar(dados, pasta="relatorios"):
    os.makedirs(pasta, exist_ok=True)
    nome = f"diagnostico_{datetime.now():%Y%m%d_%H%M%S}.txt"
    caminho = os.path.join(pasta, nome)
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(gerar_texto(dados))
    return caminho
