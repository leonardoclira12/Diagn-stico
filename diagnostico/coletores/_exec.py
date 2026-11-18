"""Execução segura de comandos externos e PowerShell: sem janela, com tempo limite, saída em UTF-8."""
import json
import platform
import subprocess

SO = platform.system()
_FLAGS = 0x08000000 if SO == "Windows" else 0  # CREATE_NO_WINDOW
_PREFIXO = ("$OutputEncoding=[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false);"
            "$ErrorActionPreference='SilentlyContinue';")


def executar(cmd, timeout=30):
    """Roda um comando e devolve o texto da saída ('' se falhar ou estourar o tempo)."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=timeout, creationflags=_FLAGS)
    except (subprocess.TimeoutExpired, OSError):
        return ""
    return r.stdout or ""


def powershell(script, timeout=30):
    return executar(["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                     "-Command", _PREFIXO + script], timeout)


def interpretar_json(texto):
    """Extrai JSON de uma saída que pode ter lixo antes (avisos, BOM). None se não houver."""
    texto = (texto or "").strip()
    posicoes = [p for p in (texto.find("{"), texto.find("[")) if p != -1]
    if not posicoes:
        return None
    try:
        return json.loads(texto[min(posicoes):])
    except ValueError:
        return None


def json_ps(script, timeout=30):
    return interpretar_json(powershell(script, timeout))


def lista(valor):
    """O PowerShell devolve objeto único em vez de lista quando há 1 item; normaliza para lista."""
    if valor is None:
        return []
    return valor if isinstance(valor, list) else [valor]
