"""Processos que mais consomem CPU e RAM."""
import time

import psutil

# Entradas que representam CPU ociosa, não programas de verdade
IGNORAR = {"system idle process", "idle"}


def top(n=5, amostra_seg=1.0):
    nucleos = psutil.cpu_count(logical=True) or 1
    procs = [p for p in psutil.process_iter(["pid", "name", "memory_percent"])
             if p.info["pid"] != 0 and (p.info["name"] or "").lower() not in IGNORAR]
    for p in procs:
        try:
            p.cpu_percent(None)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    time.sleep(amostra_seg)

    linhas = []
    for p in procs:
        try:
            linhas.append({
                "pid": p.info["pid"],
                "nome": p.info["name"] or "?",
                "cpu_percent": round(p.cpu_percent(None) / nucleos, 1),
                "ram_percent": round(p.info["memory_percent"] or 0, 1),
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    por_cpu = sorted(linhas, key=lambda x: x["cpu_percent"], reverse=True)[:n]
    por_ram = sorted(linhas, key=lambda x: x["ram_percent"], reverse=True)[:n]
    return {"por_cpu": por_cpu, "por_ram": por_ram}
