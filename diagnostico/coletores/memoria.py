"""Uso de RAM e swap."""
import psutil

GB = 1024 ** 3


def coletar():
    ram = psutil.virtual_memory()
    swap = psutil.swap_memory()
    return {
        "ram_total_gb": round(ram.total / GB, 1),
        "ram_usada_gb": round(ram.used / GB, 1),
        "ram_livre_gb": round(ram.available / GB, 1),
        "ram_uso_percent": ram.percent,
        "swap_total_gb": round(swap.total / GB, 1),
        "swap_uso_percent": swap.percent,
    }
