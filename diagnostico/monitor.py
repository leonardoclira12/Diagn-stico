"""Monitoramento por um tempo escolhido: pega picos e processos que pesam de verdade."""
import re
import time

import psutil

MB = 1024 ** 2
LIMITE_CPU = 90   # % acima do qual a CPU conta como "saturada"
LIMITE_RAM = 90


def parse_duracao(texto):
    """'90', '90s', '2 min', '2 minutos', '1h' -> segundos. Levanta ValueError se inválido."""
    m = re.fullmatch(r"\s*(\d+(?:[.,]\d+)?)\s*([a-zA-Zçã]*)\s*", str(texto))
    if not m:
        raise ValueError("Tempo inválido")
    valor = float(m.group(1).replace(",", "."))
    unidade = m.group(2).lower()
    if unidade in ("", "s", "seg", "segundo", "segundos"):
        fator = 1
    elif unidade in ("m", "min", "mins", "minuto", "minutos"):
        fator = 60
    elif unidade in ("h", "hora", "horas"):
        fator = 3600
    else:
        raise ValueError("Unidade inválida (use segundos, min ou h)")
    segundos = int(valor * fator)
    if segundos < 5:
        raise ValueError("O tempo mínimo é 5 segundos")
    if segundos > 3600:
        raise ValueError("O tempo máximo é 1 hora")
    return segundos


def formatar_duracao(segundos):
    if segundos >= 60 and segundos % 60 == 0:
        return f"{segundos // 60} min"
    if segundos >= 60:
        return f"{segundos // 60} min {segundos % 60} s"
    return f"{segundos} s"


def monitorar(segundos, ao_progresso=None, parar=None):
    """Amostra 1x por segundo. `ao_progresso(decorrido, total)` é chamado a cada amostra;
    `parar` é um threading.Event que encerra mais cedo (os dados coletados até ali são usados)."""
    nucleos = psutil.cpu_count(logical=True) or 1
    psutil.cpu_percent(None)
    procs = {}
    for p in psutil.process_iter(["name"]):
        if p.pid == 0 or (p.info["name"] or "").lower() in ("system idle process", "idle"):
            continue  # CPU ociosa, não é um programa
        try:
            p.cpu_percent(None)
            procs[p.pid] = {"p": p, "nome": p.info["name"] or "?", "cpu_soma": 0.0, "n": 0, "ram_max": 0.0}
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    cpu_amostras, ram_amostras, disco_amostras = [], [], []
    io_anterior = psutil.disk_io_counters()
    inicio = time.time()
    proxima = inicio + 1
    while True:
        decorrido = time.time() - inicio
        if decorrido >= segundos or (parar is not None and parar.is_set()):
            break
        time.sleep(max(0, proxima - time.time()))
        proxima += 1

        cpu_amostras.append(psutil.cpu_percent(None))
        ram_amostras.append(psutil.virtual_memory().percent)
        io = psutil.disk_io_counters()
        if io and io_anterior:
            disco_amostras.append(((io.read_bytes + io.write_bytes)
                                   - (io_anterior.read_bytes + io_anterior.write_bytes)) / MB)
        io_anterior = io

        for pid, info in list(procs.items()):
            try:
                info["cpu_soma"] += info["p"].cpu_percent(None)
                info["n"] += 1
                info["ram_max"] = max(info["ram_max"], info["p"].memory_percent())
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass  # processo encerrou: mantém o que já foi somado
        if ao_progresso:
            ao_progresso(min(int(time.time() - inicio), segundos), segundos)

    n = len(cpu_amostras)
    if n == 0:
        return None

    def media(v):
        return round(sum(v) / len(v), 1) if v else 0.0

    top_cpu = sorted(
        ({"nome": i["nome"], "cpu_media": round(i["cpu_soma"] / i["n"] / nucleos, 1) if i["n"] else 0.0}
         for i in procs.values()), key=lambda x: x["cpu_media"], reverse=True)[:5]
    top_ram = sorted(
        ({"nome": i["nome"], "ram_max": round(i["ram_max"], 1)} for i in procs.values()),
        key=lambda x: x["ram_max"], reverse=True)[:5]

    return {
        "duracao_s": n,
        "cpu_media": media(cpu_amostras),
        "cpu_pico": max(cpu_amostras),
        "cpu_tempo_saturada_pct": round(100 * sum(1 for x in cpu_amostras if x >= LIMITE_CPU) / n),
        "ram_media": media(ram_amostras),
        "ram_pico": max(ram_amostras),
        "ram_tempo_alta_pct": round(100 * sum(1 for x in ram_amostras if x >= LIMITE_RAM) / n),
        "disco_media_mb_s": media(disco_amostras),
        "disco_pico_mb_s": round(max(disco_amostras), 1) if disco_amostras else 0.0,
        "top_cpu": top_cpu,
        "top_ram": top_ram,
    }
