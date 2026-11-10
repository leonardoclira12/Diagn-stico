"""Informações e uso de CPU."""
import platform

import psutil


def coletar(amostra_seg=1.0):
    freq = psutil.cpu_freq()
    return {
        "modelo": platform.processor() or platform.machine(),
        "nucleos_fisicos": psutil.cpu_count(logical=False),
        "nucleos_logicos": psutil.cpu_count(logical=True),
        "uso_percent": psutil.cpu_percent(interval=amostra_seg),
        "freq_atual_mhz": round(freq.current) if freq else None,
        "freq_max_mhz": round(freq.max) if freq and freq.max else None,
    }
