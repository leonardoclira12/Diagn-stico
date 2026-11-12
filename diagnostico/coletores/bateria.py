"""Bateria (notebooks): carga, desgaste e ciclos.

Windows: powercfg /batteryreport (XML). Mac: system_profiler SPPowerDataType.
Linux (só testes): /sys/class/power_supply.
Retorna {"presente": False} em computadores de mesa.
"""
import glob
import json
import os
import platform
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET

import psutil

SO = platform.system()


def _executar(cmd, timeout=30):
    kwargs = {}
    if SO == "Windows":
        kwargs["creationflags"] = 0x08000000  # sem janela preta piscando
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, **kwargs)
    return r.stdout if r.returncode == 0 else ""


def _int(valor):
    try:
        return int(re.sub(r"[^\d]", "", str(valor)))
    except ValueError:
        return None


def interpretar_relatorio_windows(xml_texto):
    """Extrai capacidade de projeto, capacidade atual e ciclos do XML do powercfg."""
    raiz = ET.fromstring(xml_texto)
    campos = {}
    for el in raiz.iter():
        tag = el.tag.split("}")[-1]
        if tag in ("DesignCapacity", "FullChargeCapacity", "CycleCount") and tag not in campos:
            campos[tag] = _int(el.text)
    ciclos = campos.get("CycleCount") or None  # 0 = o fabricante não informa
    return {
        "capacidade_projeto_mwh": campos.get("DesignCapacity"),
        "capacidade_atual_mwh": campos.get("FullChargeCapacity"),
        "ciclos": ciclos,
    }


def _windows():
    with tempfile.TemporaryDirectory() as pasta:
        arq = os.path.join(pasta, "bateria.xml")
        _executar(["powercfg", "/batteryreport", "/output", arq, "/xml", "/duration", "1"])
        if not os.path.exists(arq):
            return {}
        with open(arq, encoding="utf-8", errors="ignore") as f:
            return interpretar_relatorio_windows(f.read())


def interpretar_perfil_mac(json_texto):
    dados = json.loads(json_texto)
    for item in dados.get("SPPowerDataType", []):
        info = item.get("sppower_battery_health_info")
        if not info:
            continue
        cap = info.get("sppower_battery_health_maximum_capacity")
        return {
            "saude_pct": _int(cap) if cap else None,
            "ciclos": info.get("sppower_battery_cycle_count"),
            "condicao": info.get("sppower_battery_health"),
        }
    return {}


def _mac():
    saida = _executar(["system_profiler", "-json", "SPPowerDataType"])
    return interpretar_perfil_mac(saida) if saida.strip() else {}


def _linux():
    for base in glob.glob("/sys/class/power_supply/BAT*"):
        def ler(nome):
            try:
                with open(os.path.join(base, nome)) as f:
                    return int(f.read().strip())
            except (OSError, ValueError):
                return None
        cheia = ler("energy_full") or ler("charge_full")
        projeto = ler("energy_full_design") or ler("charge_full_design")
        info = {"ciclos": ler("cycle_count") or None}
        if cheia and projeto:
            info["saude_pct"] = round(100 * cheia / projeto)
        return info
    return {}


def coletar():
    try:
        b = psutil.sensors_battery()
    except Exception:
        b = None
    if b is None:
        return {"presente": False}
    info = {
        "presente": True,
        "percent": round(b.percent),
        "na_tomada": bool(b.power_plugged),
        "saude_pct": None,
        "ciclos": None,
        "condicao": None,
        "capacidade_projeto_mwh": None,
        "capacidade_atual_mwh": None,
    }
    try:
        extra = _windows() if SO == "Windows" else _mac() if SO == "Darwin" else _linux()
    except Exception:
        extra = {}
    info.update({k: v for k, v in extra.items() if v is not None})
    proj, atual = info["capacidade_projeto_mwh"], info["capacidade_atual_mwh"]
    if info["saude_pct"] is None and proj and atual:
        info["saude_pct"] = round(100 * atual / proj)
    return info
