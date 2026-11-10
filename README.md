# Diagnóstico

Sistema de diagnóstico para Windows e macOS que verifica o computador peça por peça
e aponta causas prováveis de lentidão.

## Decisões
- Python + psutil (multiplataforma)
- Interface simples de terminal (estilo CMD), sem frescura
- Sem IA: regras simples e transparentes
- Um commit por etapa

## O que o app faz
- Inventário: sistema, CPU, RAM, partições e discos físicos (tipo SSD/HD e saúde)
- Diagnóstico de lentidão por regras: CPU, RAM, swap, disco cheio, HD mecânico, saúde do disco, uptime
- Programas na inicialização (Windows: Registro e pasta Inicializar; Mac: LaunchAgents e Itens de Login)
- Monitoramento com duração à escolha (ex.: `30`, `2 min`, `1h`; de 5 s a 1 h): picos de CPU/RAM/disco e processos que mais pesam
- Relatório em `.txt`

## Roadmap
- [x] Estrutura, coletores básicos, análise por regras, menu de terminal, relatório .txt
- [x] Interface gráfica simples + executável (.exe / .app)
- [x] Programas de inicialização
- [x] Tipo (SSD/HD) e saúde dos discos
- [x] Monitoramento com tempo escolhido
- [ ] Bateria (notebooks)
- [ ] Rede (latência e DNS)
- [ ] Temperaturas e throttling
- [ ] Ícone próprio, nota geral e abas na janela

## Como usar

**Versão com janela (.exe)**
- Windows: dê dois cliques em `build_windows.bat` (precisa de Python instalado). O executável sai em `dist\Diagnostico.exe`.
- Mac: `./build_mac.sh` gera `dist/Diagnostico.app`.
- Sem gerar o executável: `python run_gui.py`
- Os executáveis também são gerados automaticamente pelo GitHub Actions (aba Actions > Artifacts)

**Versão terminal**
- `pip install -r requirements.txt` e `python -m diagnostico`
