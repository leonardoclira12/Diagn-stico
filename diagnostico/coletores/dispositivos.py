"""Dispositivos com problema de driver (o 'triângulo amarelo' do Gerenciador de Dispositivos).

Só Windows (Win32_PnPEntity). Em outros sistemas devolve None (não se aplica).
"""
import platform

from . import _exec

SO = platform.system()

SCRIPT_WINDOWS = r"""
$x=@(Get-CimInstance Win32_PnPEntity | Where-Object {$_.ConfigManagerErrorCode -ne 0} | Select-Object Name,PNPClass,ConfigManagerErrorCode)
@{itens=$x} | ConvertTo-Json -Compress -Depth 3
"""

# Código 22 = desativado pelo usuário; 45 = dispositivo não conectado agora. Não são defeitos.
IGNORAR = {0, 22, 45}
CODIGOS = {
    1: "não está configurado corretamente",
    10: "não consegue iniciar",
    12: "conflito de recursos",
    18: "driver precisa ser reinstalado",
    24: "ausente ou com defeito",
    28: "driver não instalado",
    31: "não está funcionando direito",
    39: "driver corrompido ou ausente",
    43: "foi parado após reportar um problema",
    52: "assinatura do driver não pôde ser verificada",
}


def interpretar_windows(d):
    if not isinstance(d, dict):
        return None
    itens = []
    for x in _exec.lista(d.get("itens")):
        cod = x.get("ConfigManagerErrorCode")
        if cod in IGNORAR:
            continue
        itens.append({
            "nome": x.get("Name") or "Dispositivo desconhecido",
            "classe": x.get("PNPClass") or "—",
            "codigo": cod,
            "descricao": CODIGOS.get(cod, "problema no driver ou no dispositivo"),
        })
    return {"itens": itens}


def coletar():
    if SO == "Windows":
        return interpretar_windows(_exec.json_ps(SCRIPT_WINDOWS, timeout=20))
    return None
