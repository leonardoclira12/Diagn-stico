"""Reúne todos os coletores em um único dicionário de dados."""
from .coletores import cpu, disco, inicializacao, memoria, processos, sistema


def coletar_tudo():
    return {
        "sistema": sistema.coletar(),
        "cpu": cpu.coletar(1.0),
        "memoria": memoria.coletar(),
        "disco": disco.coletar(),
        "processos": processos.top(5, 1.0),
        "inicializacao": inicializacao.coletar(),
    }
