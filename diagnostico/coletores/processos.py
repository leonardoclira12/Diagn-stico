"""Processos que mais consomem CPU e RAM."""
import time

import psutil


def top(n=5, amostra_seg=1.0):
    procs = list(psutil.process_iter(["pid", "name", "memory_percent"]))
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
                "cpu_percent": p.cpu_percent(None),
                "ram_percent": round(p.info["memory_percent"] or 0, 1),
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    por_cpu = sorted(linhas, key=lambda x: x["cpu_percent"], reverse=True)[:n]
    por_ram = sorted(linhas, key=lambda x: x["ram_percent"], reverse=True)[:n]
    return {"por_cpu": por_cpu, "por_ram": por_ram}
