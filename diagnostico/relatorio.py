"""Exporta o diagnóstico em arquivo de texto."""
import os
from datetime import datetime

from . import apresentacao


def gerar_texto(dados):
    cabecalho = f"RELATÓRIO DE DIAGNÓSTICO - {datetime.now():%d/%m/%Y %H:%M:%S}\n{'=' * 60}\n"
    return cabecalho + apresentacao.montar_texto(dados)


def salvar(dados, pasta="relatorios"):
    os.makedirs(pasta, exist_ok=True)
    caminho = os.path.join(pasta, f"diagnostico_{datetime.now():%Y%m%d_%H%M%S}.txt")
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(gerar_texto(dados))
    return caminho
