"""Inventário de hardware: modelo, placa-mãe, BIOS, número de série, pentes de RAM e placa de vídeo.

Windows: CIM/WMI via PowerShell. Mac: system_profiler. Linux (testes): /sys/.../dmi.
"""
import json
import os
import platform
from datetime import date

from . import _exec

SO = platform.system()

SCRIPT_WINDOWS = r"""
function D($x){ if($x){ $x.ToString('yyyy-MM-dd') } }
$cs=Get-CimInstance Win32_ComputerSystem; $bios=Get-CimInstance Win32_BIOS; $bb=Get-CimInstance Win32_BaseBoard
$mem=@(Get-CimInstance Win32_PhysicalMemory | ForEach-Object { @{gb=[math]::Round($_.Capacity/1GB,1); mhz=[int]$_.ConfiguredClockSpeed; tipo=[int]$_.SMBIOSMemoryType} })
$slots=(Get-CimInstance Win32_PhysicalMemoryArray | Measure-Object -Property MemoryDevices -Sum).Sum
$gpu=@(Get-CimInstance Win32_VideoController | ForEach-Object { @{nome=[string]$_.Name; driver=[string]$_.DriverVersion; data=(D $_.DriverDate)} })
@{fabricante=[string]$cs.Manufacturer; modelo=[string]$cs.Model; serie=[string]$bios.SerialNumber; bios=[string]$bios.SMBIOSBIOSVersion; bios_data=(D $bios.ReleaseDate); placa=(([string]$bb.Manufacturer+' '+[string]$bb.Product).Trim()); ram=$mem; slots=[int]$slots; gpus=$gpu; lido=$true} | ConvertTo-Json -Compress -Depth 5
"""

TIPOS_RAM = {20: "DDR", 21: "DDR2", 24: "DDR3", 26: "DDR4", 27: "LPDDR", 28: "LPDDR2", 29: "LPDDR3",
             30: "LPDDR4", 34: "DDR5", 35: "LPDDR5"}
GPU_VIRTUAL = ("virtual", "vmware", "hyper-v", "remote", "parsec", "basic render", "citrix", "vnc")


def _anos(data_iso):
    try:
        return round((date.today() - date.fromisoformat(data_iso)).days / 365, 1)
    except (TypeError, ValueError):
        return None


def interpretar_windows(d):
    if not isinstance(d, dict) or not d.get("lido"):
        return None
    gpus = [{"nome": g.get("nome"), "driver": g.get("driver"), "data": g.get("data"),
             "anos": _anos(g.get("data"))} for g in _exec.lista(d.get("gpus")) if g.get("nome")]
    ram = [{"gb": m.get("gb"), "mhz": m.get("mhz") or None, "tipo": TIPOS_RAM.get(m.get("tipo"))}
           for m in _exec.lista(d.get("ram"))]
    return {
        "fabricante": d.get("fabricante") or None, "modelo": d.get("modelo") or None,
        "serie": d.get("serie") or None, "bios": d.get("bios") or None, "bios_data": d.get("bios_data"),
        "placa": d.get("placa") or None, "ram_modulos": ram, "slots": d.get("slots") or None,
        "ram_texto": None, "gpus": gpus,
    }


def interpretar_mac(json_texto):
    dados = _exec.interpretar_json(json_texto)
    if not isinstance(dados, dict):
        return None
    hw = (dados.get("SPHardwareDataType") or [{}])[0]
    if not hw:
        return None
    gpus = [{"nome": g.get("sppci_model") or g.get("_name"), "driver": None, "data": None, "anos": None}
            for g in dados.get("SPDisplaysDataType", []) if g.get("sppci_model") or g.get("_name")]
    chip = hw.get("chip_type") or hw.get("cpu_type")
    return {
        "fabricante": "Apple", "modelo": f"{hw.get('machine_name', 'Mac')} ({hw.get('machine_model', '?')})",
        "serie": hw.get("serial_number"), "bios": hw.get("boot_rom_version"), "bios_data": None,
        "placa": chip, "ram_modulos": [], "slots": None, "ram_texto": hw.get("physical_memory"), "gpus": gpus,
    }


def _linux():
    base = "/sys/devices/virtual/dmi/id"

    def ler(nome):
        try:
            with open(os.path.join(base, nome)) as f:
                return f.read().strip() or None
        except OSError:
            return None

    info = {"fabricante": ler("sys_vendor"), "modelo": ler("product_name"), "serie": ler("product_serial"),
            "bios": ler("bios_version"), "bios_data": None,
            "placa": " ".join(x for x in (ler("board_vendor"), ler("board_name")) if x) or None,
            "ram_modulos": [], "slots": None, "ram_texto": None, "gpus": []}
    return info if any(info[k] for k in ("fabricante", "modelo", "bios", "placa")) else None


def coletar():
    if SO == "Windows":
        return interpretar_windows(_exec.json_ps(SCRIPT_WINDOWS, timeout=20))
    if SO == "Darwin":
        return interpretar_mac(_exec.executar(["system_profiler", "-json", "SPHardwareDataType", "SPDisplaysDataType"], 30))
    return _linux()
