# Diagnóstico

Sistema de diagnóstico para Windows e macOS que verifica o computador peça por peça
e aponta causas prováveis de lentidão.

## Decisões
- Python + psutil (multiplataforma)
- Interface simples de terminal (estilo CMD), sem frescura
- Sem IA: regras simples e transparentes
- Um commit por etapa

## Roadmap
1. [x] Estrutura do projeto
2. [x] Coletores básicos: sistema, CPU, RAM, disco
3. [x] Análise de lentidão (regras)
4. [x] Menu de terminal
5. [x] Exportar relatório em texto
6. [ ] Próximos: bateria, rede, SMART, programas de inicialização, temperaturas

## Como usar

**Versão com janela (.exe)**
- Windows: dê dois cliques em `build_windows.bat` (precisa de Python instalado). O executável sai em `dist\Diagnostico.exe`.
- Mac: `./build_mac.sh` gera `dist/Diagnostico.app`.
- Sem gerar o executável: `python run_gui.py`

**Versão terminal**
- `pip install -r requirements.txt` e `python -m diagnostico`
