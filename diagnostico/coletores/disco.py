"""Uso de espaço nos discos."""
import psutil

GB = 1024 ** 3
IGNORAR_FS = {"squashfs", "tmpfs", "devfs", "autofs", "overlay", "iso9660"}


def coletar():
    particoes = []
    for p in psutil.disk_partitions(all=False):
        try:
            uso = psutil.disk_usage(p.mountpoint)
        except (PermissionError, OSError):
            continue
        if p.fstype in IGNORAR_FS or uso.total < GB:
            continue
        particoes.append({
            "ponto": p.mountpoint,
            "fs": p.fstype,
            "total_gb": round(uso.total / GB, 1),
            "livre_gb": round(uso.free / GB, 1),
            "uso_percent": uso.percent,
        })
    return particoes
