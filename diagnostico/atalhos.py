"""Atalhos para ferramentas do sistema. Só abrem programas e telas; não alteram nada."""
import os
import platform
import subprocess
import sys

SO = platform.system()

# id: {sistema: (rótulo, dica, comando)}
_TABELA = {
    "tarefas": {
        "Windows": ("Gerenciador de Tarefas", "Veja e encerre os programas que estão pesando.", "taskmgr.exe"),
        "Darwin": ("Monitor de Atividade", "Veja e encerre os programas que estão pesando.", ["open", "-a", "Activity Monitor"]),
    },
    "inicializacao": {
        "Windows": ("Programas de inicialização", "Ative ou desative o que abre junto com o Windows.", "ms-settings:startupapps"),
        "Darwin": ("Itens de início de sessão", "Ative ou desative o que abre ao ligar o Mac.",
                   ["open", "x-apple.systempreferences:com.apple.LoginItems-Settings.extension"]),
    },
    "atualizacoes": {
        "Windows": ("Windows Update", "Instale as atualizações pendentes.", "ms-settings:windowsupdate"),
        "Darwin": ("Atualização de Software", "Instale as atualizações pendentes.",
                   ["open", "x-apple.systempreferences:com.apple.Software-Update-Settings.extension"]),
    },
    "dispositivos": {
        "Windows": ("Gerenciador de Dispositivos", "Atualize ou reinstale drivers com problema.", "devmgmt.msc"),
    },
    "eventos": {
        "Windows": ("Visualizador de Eventos", "Veja o registro detalhado de erros do sistema.", "eventvwr.msc"),
        "Darwin": ("Console", "Veja o registro detalhado de erros do sistema.", ["open", "-a", "Console"]),
    },
    "armazenamento": {
        "Windows": ("Armazenamento", "Veja o que ocupa espaço e libere o disco.", "ms-settings:storagesense"),
        "Darwin": ("Armazenamento do Mac", "Veja o que ocupa espaço e libere o disco.",
                   ["open", "x-apple.systempreferences:com.apple.settings.Storage"]),
    },
    "rede": {
        "Windows": ("Configurações de rede", "Wi-Fi, cabo e DNS.", "ms-settings:network"),
        "Darwin": ("Configurações de rede", "Wi-Fi, cabo e DNS.",
                   ["open", "x-apple.systempreferences:com.apple.Network-Settings.extension"]),
    },
    "seguranca": {
        "Windows": ("Segurança do Windows", "Antivírus, firewall e proteções.", "windowsdefender:"),
        "Darwin": ("Privacidade e Segurança", "Firewall, FileVault e permissões.",
                   ["open", "x-apple.systempreferences:com.apple.settings.PrivacySecurity.extension"]),
    },
    "disco": {
        "Windows": ("Desfragmentar e Otimizar Unidades", "Otimização e verificação dos discos.", "dfrgui.exe"),
        "Darwin": ("Utilitário de Disco", "Verifique e repare o disco.", ["open", "-a", "Disk Utility"]),
    },
}


def disponiveis():
    """Atalhos que existem no sistema atual: [{'id', 'rotulo', 'dica'}]."""
    return [{"id": i, "rotulo": v[SO][0], "dica": v[SO][1]} for i, v in _TABELA.items() if SO in v]


def abrir(id_):
    """Abre o atalho. Devolve True se conseguiu iniciar."""
    item = _TABELA.get(id_, {}).get(SO)
    if not item:
        return False
    comando = item[2]
    try:
        if SO == "Windows":
            os.startfile(comando)  # noqa: S606 - comandos fixos da tabela acima
            return True
        return subprocess.run(comando, capture_output=True, timeout=10).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def e_administrador():
    if SO == "Windows":
        try:
            import ctypes
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:
            return False
    return hasattr(os, "geteuid") and os.geteuid() == 0


def reabrir_como_administrador():
    """Windows: pede permissão (UAC) e inicia uma nova instância elevada. True se o pedido foi aceito."""
    if SO != "Windows":
        return False
    try:
        import ctypes
        if getattr(sys, "frozen", False):
            params = ""
        else:
            params = f'"{os.path.abspath(sys.argv[0])}"'
        return ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1) > 32
    except Exception:
        return False
