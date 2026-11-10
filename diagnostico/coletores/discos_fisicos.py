"""Tipo (SSD/HD) e saúde básica dos discos físicos.

Windows: PowerShell Get-PhysicalDisk.
Mac: system_profiler (status SMART "Verified" / "Failing").
Linux (só para testes): /sys/block/*/queue/rotational.
Cada item: {"nome", "tipo": "SSD|HD|Desconhecido", "saude": "Saudável|Atenção|Falhando|Desconhecida",
            "tamanho_gb": float|None}
"""
import json
import os
import platform
import subprocess

SO = platform.system()
GB = 1024 ** 3


def _executar(cmd, timeout=20):
    kwargs = {}
    if SO == "Windows":
        kwargs["creationflags"] = 0x08000000  # CREATE_NO_WINDOW: sem janela preta piscando
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, **kwargs)
    return r.stdout if r.returncode == 0 else ""


def _windows():
    ps = ("Get-PhysicalDisk | Select-Object FriendlyName,MediaType,BusType,HealthStatus,Size "
          "| ConvertTo-Json -Compress")
    saida = _executar(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps])
    if not saida.strip():
        return []
    dados = json.loads(saida)
    if isinstance(dados, dict):
        dados = [dados]
    tipos = {"SSD": "SSD", "HDD": "HD"}
    saudes = {"Healthy": "Saudável", "Warning": "Atenção", "Unhealthy": "Falhando"}
    itens = []
    for d in dados:
        tipo = tipos.get(str(d.get("MediaType")), "Desconhecido")
        if tipo == "Desconhecido" and str(d.get("BusType")) == "NVMe":
            tipo = "SSD"
        tam = d.get("Size")
        itens.append({
            "nome": d.get("FriendlyName") or "Disco",
            "tipo": tipo,
            "saude": saudes.get(str(d.get("HealthStatus")), "Desconhecida"),
            "tamanho_gb": round(tam / GB, 1) if tam else None,
        })
    return itens


def _saude_mac(texto):
    t = (texto or "").lower()
    if "verified" in t:
        return "Saudável"
    if "fail" in t:
        return "Falhando"
    if "not supported" in t or not t:
        return "Desconhecida"
    return "Atenção"


def _mac():
    saida = _executar(["system_profiler", "-json", "SPNVMeDataType", "SPSerialATADataType"], timeout=30)
    if not saida.strip():
        return []
    dados = json.loads(saida)
    itens = []

    def percorrer(lista, tipo_padrao):
        for no in lista or []:
            for sub in [no] + list(no.get("_items", [])):
                nome = sub.get("device_model") or sub.get("_name")
                if not nome or ("spnvme_smart_status" not in sub and "smart_status" not in sub
                                and "size_in_bytes" not in sub):
                    continue
                medio = str(sub.get("spsata_medium_type", "")).lower()
                tipo = tipo_padrao
                if medio:
                    tipo = "SSD" if "solid" in medio else ("HD" if "rotational" in medio else "Desconhecido")
                tam = sub.get("size_in_bytes")
                itens.append({
                    "nome": nome,
                    "tipo": tipo,
                    "saude": _saude_mac(sub.get("spnvme_smart_status") or sub.get("smart_status")),
                    "tamanho_gb": round(tam / GB, 1) if tam else None,
                })

    percorrer(dados.get("SPNVMeDataType"), "SSD")
    percorrer(dados.get("SPSerialATADataType"), "Desconhecido")
    return itens


def _linux():
    itens = []
    base = "/sys/block"
    if not os.path.isdir(base):
        return itens
    for nome in sorted(os.listdir(base)):
        if nome.startswith(("loop", "ram", "zram", "dm-", "sr")):
            continue
        try:
            with open(f"{base}/{nome}/queue/rotational") as f:
                rot = f.read().strip()
            with open(f"{base}/{nome}/size") as f:
                setores = int(f.read().strip())
        except OSError:
            continue
        if setores == 0:
            continue
        virtual = nome.startswith(("vd", "xvd"))
        itens.append({
            "nome": nome,
            "tipo": "Desconhecido" if virtual else ("HD" if rot == "1" else "SSD"),
            "saude": "Desconhecida",
            "tamanho_gb": round(setores * 512 / GB, 1),
        })
    return itens


def coletar():
    try:
        if SO == "Windows":
            return _windows()
        if SO == "Darwin":
            return _mac()
        return _linux()
    except Exception:
        return []
