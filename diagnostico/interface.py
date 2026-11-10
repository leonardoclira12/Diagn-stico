"""Interface de terminal simples (estilo CMD)."""
import os
import sys

from . import __version__, apresentacao, relatorio
from .coleta import coletar_tudo

LARGURA = 60
CORES = {"ok": "\033[92m", "atencao": "\033[93m", "falha": "\033[91m", "titulo": "\033[1m", "fim": "\033[0m"}


def _habilitar_cores():
    if os.name == "nt":
        os.system("")  # ativa sequências ANSI no CMD/PowerShell do Windows
    return sys.stdout.isatty()


USAR_CORES = _habilitar_cores()


def imprimir(linhas):
    for texto, tag in linhas:
        if USAR_CORES and tag in CORES:
            texto = f"{CORES[tag]}{texto}{CORES['fim']}"
        print(texto, end="")


def cabecalho(texto):
    print("\n" + "=" * LARGURA)
    print(f" {texto}")
    print("=" * LARGURA)


def menu():
    dados = None
    while True:
        cabecalho(f"DIAGNÓSTICO v{__version__}")
        print(" 1) Diagnóstico completo")
        print(" 2) Salvar último relatório em arquivo .txt")
        print(" 0) Sair")
        op = input("\n Opção: ").strip()
        if op == "0":
            break
        if op == "1":
            print("Coletando dados (alguns segundos)...")
            dados = coletar_tudo()
            print()
            imprimir(apresentacao.montar_linhas(dados))
        elif op == "2":
            if dados is None:
                print(" Rode o diagnóstico primeiro (opção 1).")
            else:
                print(f"\n Relatório salvo em: {relatorio.salvar(dados)}")
        else:
            print(" Opção inválida.")
            continue
        input("\n Enter para voltar ao menu...")
