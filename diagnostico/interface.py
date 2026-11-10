"""Interface de terminal simples (estilo CMD)."""
import os
import sys

from . import __version__, analise
from .coletores import cpu, disco, memoria, processos, sistema

LARGURA = 60
CORES = {"ok": "\033[92m", "atencao": "\033[93m", "falha": "\033[91m", "fim": "\033[0m"}
ROTULOS = {"ok": "[ OK ]", "atencao": "[ !! ]", "falha": "[FALHA]"}


def _habilitar_cores():
    if os.name == "nt":
        os.system("")  # ativa sequências ANSI no CMD/PowerShell do Windows
    return sys.stdout.isatty()


USAR_CORES = _habilitar_cores()


def colorir(texto, nivel):
    if not USAR_CORES:
        return texto
    return f"{CORES[nivel]}{texto}{CORES['fim']}"


def linha(char="="):
    print(char * LARGURA)


def titulo(texto):
    print()
    linha()
    print(f" {texto}")
    linha()


def limpar():
    os.system("cls" if os.name == "nt" else "clear")


def coletar_tudo():
    print("Coletando dados (alguns segundos)...")
    return {
        "sistema": sistema.coletar(),
        "cpu": cpu.coletar(1.0),
        "memoria": memoria.coletar(),
        "disco": disco.coletar(),
        "processos": processos.top(5, 1.0),
    }


def mostrar_inventario(d):
    s, c, m = d["sistema"], d["cpu"], d["memoria"]
    titulo("INVENTÁRIO")
    print(f" Host ........ {s['host']}")
    print(f" Sistema ..... {s['so']} {s['versao_so']} ({s['arquitetura']})")
    print(f" Uptime ...... {s['uptime_horas']} h")
    print(f" CPU ......... {c['modelo']}")
    print(f"               {c['nucleos_fisicos']} núcleos físicos / {c['nucleos_logicos']} lógicos")
    print(f" RAM ......... {m['ram_total_gb']} GB (swap {m['swap_total_gb']} GB)")
    for p in d["disco"]:
        print(f" Disco ....... {p['ponto']} [{p['fs']}] {p['total_gb']} GB, {p['livre_gb']} GB livres")


def mostrar_processos(d):
    titulo("TOP PROCESSOS")
    print(" Por CPU:")
    for p in d["processos"]["por_cpu"]:
        print(f"   {p['nome'][:28]:<28} {p['cpu_percent']:>5}%  (PID {p['pid']})")
    print(" Por RAM:")
    for p in d["processos"]["por_ram"]:
        print(f"   {p['nome'][:28]:<28} {p['ram_percent']:>5}%  (PID {p['pid']})")


def mostrar_diagnostico(d):
    titulo("DIAGNÓSTICO DE LENTIDÃO")
    achados = analise.analisar(d)
    for a in achados:
        print(colorir(f" {ROTULOS[a['nivel']]} {a['titulo']}", a["nivel"]))
        print(f"          {a['detalhe']}")
        if a["sugestao"] and a["nivel"] != "ok":
            print(f"          -> {a['sugestao']}")
    problemas = [a for a in achados if a["nivel"] != "ok"]
    print()
    if problemas:
        print(f" Resultado: {len(problemas)} ponto(s) de atenção.")
    else:
        print(" Resultado: nenhum problema encontrado.")
    return achados


def menu():
    dados = None
    while True:
        titulo(f"DIAGNÓSTICO v{__version__}")
        print(" 1) Diagnóstico completo")
        print(" 2) Inventário do sistema")
        print(" 3) Top processos")
        print(" 0) Sair")
        op = input("\n Opção: ").strip()
        if op == "0":
            break
        if op not in ("1", "2", "3"):
            print(" Opção inválida.")
            continue
        dados = coletar_tudo()
        if op == "1":
            mostrar_diagnostico(dados)
        elif op == "2":
            mostrar_inventario(dados)
        elif op == "3":
            mostrar_processos(dados)
        input("\n Enter para voltar ao menu...")
