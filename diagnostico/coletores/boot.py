"""Tempo da última inicialização do Windows e o que mais a atrasou (programas, drivers, serviços).

Fonte: registro 'Diagnostics-Performance' (eventos 100 a 103). Se o log estiver vazio ou sem permissão,
devolve None. Só Windows.
"""
import platform

from . import _exec

SO = platform.system()
TIPOS = {101: "programa", 102: "driver", 103: "serviço"}

SCRIPT_WINDOWS = r"""
$log='Microsoft-Windows-Diagnostics-Performance/Operational'
$e=@(Get-WinEvent -FilterHashtable @{LogName=$log;Id=100} -MaxEvents 5)
$ms=@()
foreach($x in $e){ $xml=[xml]$x.ToXml(); $v=($xml.Event.EventData.Data | Where-Object {$_.Name -eq 'BootTime'}).'#text'; if($v){$ms+=[int]$v} }
$of=@(Get-WinEvent -FilterHashtable @{LogName=$log;Id=101,102,103} -MaxEvents 40 | ForEach-Object {
  $xml=[xml]$_.ToXml(); $dt=@{}; foreach($d in $xml.Event.EventData.Data){$dt[$d.Name]=$d.'#text'}
  $nome=$dt['FriendlyName']; if(-not $nome){$nome=$dt['Name']}
  @{tipo=$_.Id; nome=$nome; total=[int]$dt['TotalTime']; degr=[int]$dt['DegradationTime']} })
@{ms=$ms; ofensores=$of; lido=($ms.Count -gt 0)} | ConvertTo-Json -Compress -Depth 4
"""


def interpretar_windows(d):
    if not isinstance(d, dict) or not d.get("lido"):
        return None
    medidas = [m for m in _exec.lista(d.get("ms")) if isinstance(m, (int, float)) and m > 0]
    if not medidas:
        return None
    melhores = {}
    for o in _exec.lista(d.get("ofensores")):
        nome = o.get("nome")
        if not nome:
            continue
        atual = melhores.get(nome)
        if not atual or (o.get("degr") or 0) > atual["degr"]:
            melhores[nome] = {"nome": nome, "tipo": TIPOS.get(o.get("tipo"), "item"),
                              "degr": o.get("degr") or 0, "total": o.get("total") or 0}
    ofensores = sorted((x for x in melhores.values() if x["degr"] > 0),
                       key=lambda x: x["degr"], reverse=True)[:5]
    return {
        "ultimo_s": round(medidas[0] / 1000, 1),
        "media_s": round(sum(medidas) / len(medidas) / 1000, 1),
        "medidas": len(medidas),
        "ofensores": [{"nome": x["nome"], "tipo": x["tipo"], "atraso_s": round(x["degr"] / 1000, 1)}
                      for x in ofensores],
    }


def coletar():
    if SO == "Windows":
        return interpretar_windows(_exec.json_ps(SCRIPT_WINDOWS, timeout=20))
    return None
