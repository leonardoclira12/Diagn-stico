"""Erros recentes do sistema (últimos 7 dias).

Windows: registro de eventos (telas azuis, desligamentos inesperados, erros de disco, travamentos de programas).
Mac: relatórios de diagnóstico (kernel panics e travamentos de programas).
Cada categoria: {"n": quantidade, "ultimo": "AAAA-MM-DD HH:MM" | None}.
"""
import glob
import os
import platform
import time
from datetime import datetime

from . import _exec

SO = platform.system()
DIAS = 7

SCRIPT_WINDOWS = r"""
$d=(Get-Date).AddDays(-7)
function Resumo($e){ $l=@($e); if($l.Count -eq 0){return @{n=0}}; @{n=$l.Count; ultimo=(($l | Sort-Object TimeCreated -Descending | Select-Object -First 1).TimeCreated.ToString('yyyy-MM-dd HH:mm'))} }
$sys=@(Get-WinEvent -FilterHashtable @{LogName='System';StartTime=$d;Id=41,1001,7,11,51,153,55})
$app=@(Get-WinEvent -FilterHashtable @{LogName='Application';StartTime=$d;Id=1000,1002})
$r=@{}
$r.desligamentos=Resumo ($sys | Where-Object {$_.Id -eq 41})
$r.falhas_sistema=Resumo ($sys | Where-Object {$_.Id -eq 1001 -and $_.ProviderName -like '*WER-SystemErrorReporting*'})
$r.disco=Resumo ($sys | Where-Object {($_.ProviderName -eq 'disk' -and ($_.Id -in 7,11,51,153)) -or ($_.ProviderName -eq 'Ntfs' -and $_.Id -eq 55)})
$r.travamentos=Resumo ($app | Where-Object {($_.Id -eq 1000 -and $_.ProviderName -eq 'Application Error') -or ($_.Id -eq 1002 -and $_.ProviderName -eq 'Application Hang')})
$r.lido=$true
$r | ConvertTo-Json -Compress -Depth 4
"""

CATEGORIAS = ("desligamentos", "falhas_sistema", "disco", "travamentos")


def _categoria(x):
    if not isinstance(x, dict):
        return {"n": 0, "ultimo": None}
    return {"n": int(x.get("n") or 0), "ultimo": x.get("ultimo")}


def interpretar_windows(d):
    if not isinstance(d, dict) or not d.get("lido"):
        return None
    return {c: _categoria(d.get(c)) for c in CATEGORIAS}


def ler_mac(pastas, agora=None, dias=DIAS):
    """Conta relatórios recentes: kernel panics (falhas do sistema) e travamentos de programas."""
    agora = agora or time.time()
    corte = agora - dias * 86400
    falhas, travas = [], []
    for pasta in pastas:
        for arq in glob.glob(os.path.join(pasta, "*")):
            try:
                if not os.path.isfile(arq) or os.path.getmtime(arq) < corte:
                    continue
            except OSError:
                continue
            nome = os.path.basename(arq).lower()
            data = os.path.getmtime(arq)
            if nome.startswith("kernel") or nome.endswith(".panic"):
                falhas.append(data)
            elif nome.endswith((".crash", ".ips", ".hang", ".spin")):
                travas.append(data)

    def resumo(lista):
        if not lista:
            return {"n": 0, "ultimo": None}
        return {"n": len(lista), "ultimo": datetime.fromtimestamp(max(lista)).strftime("%Y-%m-%d %H:%M")}

    return {"falhas_sistema": resumo(falhas), "travamentos": resumo(travas)}


def coletar():
    if SO == "Windows":
        return interpretar_windows(_exec.json_ps(SCRIPT_WINDOWS, timeout=25))
    if SO == "Darwin":
        return ler_mac([os.path.expanduser("~/Library/Logs/DiagnosticReports"),
                        "/Library/Logs/DiagnosticReports"])
    return None
