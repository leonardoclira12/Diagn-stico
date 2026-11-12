"""Rede: latência e perda (conexão TCP), tempo de DNS e adaptadores ativos.

Usa conexões TCP em vez de ping, para funcionar igual em Windows e Mac sem permissão de administrador.
"""
import socket
import threading
import time

import psutil

ALVOS = [("Cloudflare", "1.1.1.1", 443), ("Google", "8.8.8.8", 443)]
DOMINIOS_DNS = ["www.google.com", "www.microsoft.com", "www.wikipedia.org"]
TENTATIVAS = 5
TIMEOUT_TCP = 1.2
TIMEOUT_DNS = 4.0


def _testar_tcp(nome, host, porta, saida, indice):
    tempos, falhas = [], 0
    for _ in range(TENTATIVAS):
        t = time.perf_counter()
        try:
            with socket.create_connection((host, porta), timeout=TIMEOUT_TCP):
                pass
            tempos.append((time.perf_counter() - t) * 1000)
        except OSError:
            falhas += 1
        time.sleep(0.05)
    saida[indice] = {
        "nome": nome, "host": host, "tentativas": TENTATIVAS, "falhas": falhas,
        "medio_ms": round(sum(tempos) / len(tempos), 1) if tempos else None,
        "max_ms": round(max(tempos), 1) if tempos else None,
    }


def _testar_dns(dominio, saida, indice):
    t = time.perf_counter()
    resultado = {"ms": None}

    def resolver():
        try:
            socket.getaddrinfo(dominio, 443)
            resultado["ms"] = (time.perf_counter() - t) * 1000
        except OSError:
            pass

    th = threading.Thread(target=resolver, daemon=True)
    th.start()
    th.join(TIMEOUT_DNS)
    saida[indice] = resultado["ms"]


def _adaptadores():
    itens = []
    try:
        for nome, st in psutil.net_if_stats().items():
            if st.isup and not nome.lower().startswith(("lo", "loopback")):
                itens.append({"nome": nome, "velocidade_mbps": st.speed or None})
    except Exception:
        pass
    return itens


def coletar():
    alvos = [None] * len(ALVOS)
    dns = [None] * len(DOMINIOS_DNS)
    threads = [threading.Thread(target=_testar_tcp, args=(*a, alvos, i), daemon=True)
               for i, a in enumerate(ALVOS)]
    threads += [threading.Thread(target=_testar_dns, args=(d, dns, i), daemon=True)
                for i, d in enumerate(DOMINIOS_DNS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    ok_dns = [x for x in dns if x is not None]
    tcp_ok = any(a["medio_ms"] is not None for a in alvos)
    return {
        "internet": tcp_ok or bool(ok_dns),
        "alvos": alvos,
        "dns": {
            "medio_ms": round(sum(ok_dns) / len(ok_dns), 1) if ok_dns else None,
            "max_ms": round(max(ok_dns), 1) if ok_dns else None,
            "falhas": len(dns) - len(ok_dns),
            "total": len(dns),
        },
        "adaptadores": _adaptadores(),
    }
