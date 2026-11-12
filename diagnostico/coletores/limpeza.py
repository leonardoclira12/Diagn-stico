"""Limpeza de arquivos temporários: estimativa e remoção.

Regras de segurança:
- só atua nas pastas listadas em categorias() (nada fora delas);
- só remove arquivos com mais de IDADE_MIN_H horas (não mexe no que está em uso agora);
- nunca segue links simbólicos (nem apaga o destino deles);
- a remoção só acontece quando a interface chama limpar(), depois de o usuário confirmar.
"""
import os
import platform
import time

SO = platform.system()
IDADE_MIN_H = 24
GB = 1024 ** 3
MB = 1024 ** 2


def categorias():
    """Lista de {"id", "nome", "pasta", "idade_min_h", "explicacao"} para o sistema atual."""
    home = os.path.expanduser("~")
    cats = []
    if SO == "Windows":
        local = os.environ.get("LOCALAPPDATA", "")
        temp = os.environ.get("TEMP") or os.environ.get("TMP") or ""
        win = os.environ.get("WINDIR", r"C:\Windows")
        cats = [
            ("temp_usuario", "Temporários do usuário", temp, "Sobras de instaladores e programas."),
            ("temp_windows", "Temporários do Windows", os.path.join(win, "Temp"),
             "Pode exigir executar como administrador para apagar."),
            ("cache_chrome", "Cache do Google Chrome", os.path.join(local, "Google", "Chrome", "User Data", "Default", "Cache"),
             "Sites podem carregar um pouco mais devagar na primeira visita."),
            ("cache_edge", "Cache do Microsoft Edge", os.path.join(local, "Microsoft", "Edge", "User Data", "Default", "Cache"),
             "Sites podem carregar um pouco mais devagar na primeira visita."),
        ]
    elif SO == "Darwin":
        cats = [
            ("cache_apps", "Cache de aplicativos", os.path.join(home, "Library", "Caches"),
             "Os apps recriam o cache; a primeira abertura pode ser mais lenta."),
            ("logs_usuario", "Logs do usuário", os.path.join(home, "Library", "Logs"), "Registros antigos de apps."),
            ("lixeira", "Lixeira", os.path.join(home, ".Trash"), "Itens já descartados (pode exigir acesso total ao disco)."),
        ]
    else:  # Linux: apenas para testes de desenvolvimento
        cats = [("cache_teste", "Cache de teste", os.path.join(home, ".cache", "diagnostico-teste"), "Pasta de testes.")]
    return [
        {"id": i, "nome": n, "pasta": p, "idade_min_h": 0 if i == "lixeira" else IDADE_MIN_H, "explicacao": e}
        for i, n, p, e in cats if p
    ]


def _pasta_segura(pasta):
    """Recusa raízes, a pasta pessoal e caminhos muito curtos."""
    real = os.path.realpath(pasta)
    partes = [x for x in real.replace("\\", "/").split("/") if x]
    return (os.path.isdir(real) and os.path.dirname(real) != real
            and real != os.path.realpath(os.path.expanduser("~")) and len(partes) >= 3)


def _arquivos(raiz, corte):
    """Gera (caminho, tamanho) dos arquivos comuns com data de modificação <= corte."""
    pilha = [raiz]
    while pilha:
        pasta = pilha.pop()
        try:
            with os.scandir(pasta) as it:
                for e in it:
                    try:
                        if e.is_symlink():
                            continue
                        if e.is_dir(follow_symlinks=False):
                            pilha.append(e.path)
                        elif e.is_file(follow_symlinks=False):
                            st = e.stat(follow_symlinks=False)
                            if st.st_mtime <= corte:
                                yield e.path, st.st_size
                    except OSError:
                        continue
        except OSError:
            continue


def estimar(limite_s=20):
    """Calcula quanto cada categoria ocuparia se limpa (não apaga nada)."""
    fim = time.time() + limite_s
    resultado = []
    for c in categorias():
        item = {**c, "bytes": 0, "arquivos": 0, "acessivel": _pasta_segura(c["pasta"]), "incompleto": False}
        if item["acessivel"]:
            corte = time.time() - c["idade_min_h"] * 3600
            for _, tam in _arquivos(os.path.realpath(c["pasta"]), corte):
                item["bytes"] += tam
                item["arquivos"] += 1
                if time.time() > fim:
                    item["incompleto"] = True
                    break
        resultado.append(item)
    return resultado


def limpar(ids, ao_progresso=None):
    """Apaga os arquivos elegíveis das categorias escolhidas. Retorna totais."""
    validos = {c["id"]: c for c in categorias()}
    liberado = removidos = falhas = 0
    for id_ in ids:
        c = validos.get(id_)
        if not c or not _pasta_segura(c["pasta"]):
            continue
        raiz = os.path.realpath(c["pasta"])
        corte = time.time() - c["idade_min_h"] * 3600
        for caminho, tam in list(_arquivos(raiz, corte)):
            try:
                os.remove(caminho)
                liberado += tam
                removidos += 1
            except OSError:
                falhas += 1
            if ao_progresso and removidos % 50 == 0:
                ao_progresso(removidos)
        for atual, subs, _ in os.walk(raiz, topdown=False):  # remove pastas vazias, nunca a raiz
            if atual != raiz and not os.path.islink(atual):
                try:
                    os.rmdir(atual)
                except OSError:
                    pass
    return {"liberado_bytes": liberado, "removidos": removidos, "falhas": falhas}


def formatar_tamanho(b):
    if b >= GB:
        return f"{b / GB:.2f} GB"
    if b >= MB:
        return f"{b / MB:.1f} MB"
    return f"{b / 1024:.0f} KB"
