"""Reúne todos os coletores em um único dicionário de dados."""
from .coletores import bateria, cpu, disco, discos_fisicos, inicializacao, memoria, processos, rede, sistema


def coletar_tudo():
    return {
        "sistema": sistema.coletar(),
        "cpu": cpu.coletar(1.0),
        "memoria": memoria.coletar(),
        "disco": disco.coletar(),
        "processos": processos.top(5, 1.0),
        "discos_fisicos": discos_fisicos.coletar(),
        "inicializacao": inicializacao.coletar(),
        "bateria": bateria.coletar(),
        "rede": rede.coletar(),
    }
