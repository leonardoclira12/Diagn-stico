"""Programas que iniciam junto com o sistema.

Windows: chaves Run do Registro + pastas Inicializar.
Mac: LaunchAgents/LaunchDaemons + Itens de Login.
Linux (usado só para testes): ~/.config/autostart.
Cada item: {"nome", "comando", "origem"}.
"""
import glob
import os
import platform
import plistlib
import subprocess

SO = platform.system()


def _windows():
    import winreg

    itens = []
    chaves = [
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", "Registro (usuário)", 0),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run", "Registro (todos)", winreg.KEY_WOW64_64KEY),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run", "Registro (todos, 32 bits)", winreg.KEY_WOW64_32KEY),
    ]
    for raiz, caminho, origem, flag in chaves:
        try:
            with winreg.OpenKey(raiz, caminho, 0, winreg.KEY_READ | flag) as k:
                i = 0
                while True:
                    try:
                        nome, valor, _ = winreg.EnumValue(k, i)
                    except OSError:
                        break
                    itens.append({"nome": nome, "comando": str(valor), "origem": origem})
                    i += 1
        except OSError:
            continue

    pastas = [
        (os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"), "Pasta Inicializar (usuário)"),
        (os.path.expandvars(r"%PROGRAMDATA%\Microsoft\Windows\Start Menu\Programs\StartUp"), "Pasta Inicializar (todos)"),
    ]
    for pasta, origem in pastas:
        for arq in glob.glob(os.path.join(pasta, "*")):
            if os.path.basename(arq).lower() == "desktop.ini":
                continue
            itens.append({"nome": os.path.splitext(os.path.basename(arq))[0], "comando": arq, "origem": origem})
    return itens


def _mac():
    itens = []
    pastas = [
        (os.path.expanduser("~/Library/LaunchAgents"), "LaunchAgent (usuário)"),
        ("/Library/LaunchAgents", "LaunchAgent (todos)"),
        ("/Library/LaunchDaemons", "LaunchDaemon (sistema)"),
    ]
    for pasta, origem in pastas:
        for arq in glob.glob(os.path.join(pasta, "*.plist")):
            try:
                with open(arq, "rb") as f:
                    info = plistlib.load(f)
            except Exception:
                continue
            if info.get("Disabled") is True:
                continue
            cmd = " ".join(info.get("ProgramArguments") or [info.get("Program", "")]).strip()
            itens.append({"nome": info.get("Label", os.path.basename(arq)), "comando": cmd, "origem": origem})

    try:  # Itens de Login (pode pedir permissão de Automação na primeira vez)
        r = subprocess.run(
            ["osascript", "-e", 'tell application "System Events" to get the name of every login item'],
            capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            for nome in [n.strip() for n in r.stdout.split(",") if n.strip()]:
                itens.append({"nome": nome, "comando": "", "origem": "Item de Login"})
    except Exception:
        pass
    return itens


def _linux():
    itens = []
    for arq in glob.glob(os.path.expanduser("~/.config/autostart/*.desktop")):
        nome, cmd = os.path.basename(arq), ""
        try:
            with open(arq, encoding="utf-8", errors="ignore") as f:
                for linha in f:
                    if linha.startswith("Name=") and nome == os.path.basename(arq):
                        nome = linha.split("=", 1)[1].strip()
                    elif linha.startswith("Exec="):
                        cmd = linha.split("=", 1)[1].strip()
        except OSError:
            continue
        itens.append({"nome": nome, "comando": cmd, "origem": "Autostart"})
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
