"""Atualizações do sistema: pendentes, reinício pendente e data da última instalada.

Windows: Windows Update (COM) + registro + hotfixes, em uma única chamada de PowerShell.
Mac: softwareupdate -l.
Retorna None onde não se aplica ou não foi possível ler.
"""
import platform
import re
from datetime import date

from . import _exec

SO = platform.system()

SCRIPT_WINDOWS = r"""
$r=@{}
$r.reboot=((Test-Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired') -or (Test-Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending'))
$h=Get-CimInstance Win32_QuickFixEngineering | Where-Object {$_.InstalledOn} | Sort-Object InstalledOn -Descending | Select-Object -First 1
if($h){$r.ultima=$h.InstalledOn.ToString('yyyy-MM-dd')}
$s=New-Object -ComObject Microsoft.Update.Session
$b=$s.CreateUpdateSearcher().Search('IsInstalled=0 and IsHidden=0')
if($b){$r.pendentes=@($b.Updates | ForEach-Object {$_.Title})}
$r | ConvertTo-Json -Compress
"""


def _titulos(valor):
    if valor is None:
        return None
    if isinstance(valor, str):
        return [valor]
    return [str(v) for v in valor]


def interpretar_windows(d):
    if not isinstance(d, dict):
        return None
    ultima = d.get("ultima")
    dias = None
    if ultima:
        try:
            dias = (date.today() - date.fromisoformat(ultima)).days
        except ValueError:
            ultima = None
    return {
        "reboot_pendente": bool(d["reboot"]) if "reboot" in d else None,
        "pendentes": _titulos(d.get("pendentes")),
        "ultima_instalacao": ultima,
        "dias_desde_ultima": dias,
    }


def interpretar_mac(texto):
    if not texto.strip():
        return None
    titulos = re.findall(r"Title:\s*([^,\n]+),", texto)
    if not titulos:
        titulos = re.findall(r"^\s*\*\s+Label:\s*(.+)$", texto, re.M)
    return {"reboot_pendente": None, "pendentes": [t.strip() for t in titulos],
            "ultima_instalacao": None, "dias_desde_ultima": None}


def coletar():
    if SO == "Windows":
        return interpretar_windows(_exec.json_ps(SCRIPT_WINDOWS, timeout=25))
    if SO == "Darwin":
        return interpretar_mac(_exec.executar(["softwareupdate", "-l"], timeout=30))
    return None
