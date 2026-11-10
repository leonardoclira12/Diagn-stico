"""Informações gerais do sistema operacional."""
import platform
import socket
import time

import psutil


def coletar():
    boot = psutil.boot_time()
    return {
        "host": socket.gethostname(),
        "so": platform.system(),
        "versao_so": platform.release(),
        "build": platform.version(),
        "arquitetura": platform.machine(),
        "uptime_horas": round((time.time() - boot) / 3600, 1),
    }
