"""Verificações básicas de segurança.

Windows: antivírus registrado (Central de Segurança) e perfis do firewall.
Mac: FileVault, firewall, proteção de integridade do sistema (SIP) e Gatekeeper.
Cada verificação: {"nome", "ok": True|False, "detalhe"}.
"""
import platform

from . import _exec

SO = platform.system()

SCRIPT_WINDOWS = r"""
$av=@(Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntiVirusProduct | ForEach-Object { @{nome=[string]$_.displayName; estado=[int64]$_.productState} })
$fw=@(Get-NetFirewallProfile | ForEach-Object { @{nome=[string]$_.Name; ativo=($_.Enabled -eq 'True')} })
@{antivirus=$av; firewall=$fw; lido=$true} | ConvertTo-Json -Compress -Depth 4
"""

PERFIS = {"Domain": "domínio", "Private": "rede privada", "Public": "rede pública"}


def interpretar_windows(d):
    if not isinstance(d, dict) or not d.get("lido"):
        return None
    itens = []
    antivirus = _exec.lista(d.get("antivirus"))
    if not antivirus:
        itens.append({"nome": "Antivírus", "ok": False, "detalhe": "nenhum antivírus registrado no Windows"})
    for av in antivirus:
        estado = int(av.get("estado") or 0)
        ativo = bool(estado & 0x1000)
        atualizado = not (estado & 0x10)
        if ativo and atualizado:
            itens.append({"nome": f"Antivírus: {av.get('nome')}", "ok": True, "detalhe": "ativo e atualizado"})
        elif ativo:
            itens.append({"nome": f"Antivírus: {av.get('nome')}", "ok": False, "detalhe": "ativo, mas com definições desatualizadas"})
        else:
            itens.append({"nome": f"Antivírus: {av.get('nome')}", "ok": None, "detalhe": "desativado (normal se outro antivírus estiver ativo)"})
    # Se nenhum antivírus está ativo, isso é o problema real
    if antivirus and not any(i["ok"] is not None and i["nome"].startswith("Antivírus:") and "ativo" in i["detalhe"] for i in itens):
        itens.append({"nome": "Antivírus", "ok": False, "detalhe": "nenhum antivírus está ativo"})
    for p in _exec.lista(d.get("firewall")):
        rotulo = PERFIS.get(p.get("nome"), p.get("nome"))
        itens.append({"nome": f"Firewall ({rotulo})", "ok": bool(p.get("ativo")),
                      "detalhe": "ativado" if p.get("ativo") else "desativado"})
    return {"verificacoes": itens}


def _estado(texto, positivos, negativos):
    t = (texto or "").lower()
    if any(p in t for p in negativos):
        return False
    if any(p in t for p in positivos):
        return True
    return None


def interpretar_mac(saidas):
    """saidas: dict com o texto de cada comando (filevault, sip, firewall, gatekeeper)."""
    regras = [
        ("filevault", "Criptografia do disco (FileVault)", ["is on"], ["is off"]),
        ("sip", "Proteção do sistema (SIP)", ["enabled"], ["disabled"]),
        ("firewall", "Firewall", ["is enabled", "state = 1"], ["is disabled", "state = 0"]),
        ("gatekeeper", "Gatekeeper (apps verificados)", ["assessments enabled"], ["assessments disabled"]),
    ]
    itens = []
    for chave, nome, pos, neg in regras:
        ok = _estado(saidas.get(chave), pos, neg)
        if ok is not None:
            itens.append({"nome": nome, "ok": ok, "detalhe": "ativado" if ok else "desativado"})
    return {"verificacoes": itens} if itens else None


def coletar():
    if SO == "Windows":
        return interpretar_windows(_exec.json_ps(SCRIPT_WINDOWS, timeout=20))
    if SO == "Darwin":
        return interpretar_mac({
            "filevault": _exec.executar(["fdesetup", "status"], 10),
            "sip": _exec.executar(["csrutil", "status"], 10),
            "firewall": _exec.executar(["/usr/libexec/ApplicationFirewall/socketfilterfw", "--getglobalstate"], 10),
            "gatekeeper": _exec.executar(["spctl", "--status"], 10),
        })
    return None
