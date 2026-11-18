"""Reúne todos os coletores em um único dicionário de dados.

Primeiro as leituras rápidas de CPU/RAM/processos (sem concorrência, para não distorcer a medição);
depois as leituras mais lentas (PowerShell, rede) em paralelo.
"""
from concurrent.futures import ThreadPoolExecutor

from .coletores import (atualizacoes, bateria, boot, cpu, disco, discos_fisicos, dispositivos, eventos, inicializacao, memoria, processos,
                        rede, sistema)

# Leituras lentas, executadas em paralelo. Valor None = "não deu para ler / não se aplica".
LEITORES = {
    "rede": rede.coletar,
    "discos_fisicos": discos_fisicos.coletar,
    "inicializacao": inicializacao.coletar,
    "bateria": bateria.coletar,
    "atualizacoes": atualizacoes.coletar,
    "dispositivos": dispositivos.coletar,
    "eventos": eventos.coletar,
    "boot": boot.coletar,
}
PADRAO = {"discos_fisicos": [], "inicializacao": [], "bateria": {"presente": False}}


def _seguro(fn):
    try:
        return fn()
    except Exception:
        return None


def coletar_tudo():
    dados = {
        "sistema": sistema.coletar(),
        "cpu": cpu.coletar(1.0),
        "memoria": memoria.coletar(),
        "disco": disco.coletar(),
        "processos": processos.top(5, 1.0),
    }
    with ThreadPoolExecutor(max_workers=4) as pool:
        futuros = {nome: pool.submit(_seguro, fn) for nome, fn in LEITORES.items()}
        for nome, f in futuros.items():
            resultado = f.result()
            dados[nome] = PADRAO.get(nome) if resultado is None else resultado
    return dados
