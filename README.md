# Diagnóstico

Sistema de diagnóstico para Windows e macOS que verifica o computador peça por peça
e aponta causas prováveis de lentidão.

## Decisões
- Python + psutil (multiplataforma)
- Interface simples de terminal (estilo CMD), sem frescura
- Sem IA: regras simples e transparentes
- Um commit por etapa

## O que o app faz
- **Nota geral** no topo da janela: Saudável, Atenção ou Crítico
- Abas: Resumo, Inicialização, Discos, Bateria, Rede, Monitoramento, Processos e Limpeza
- Inventário: sistema, CPU, RAM, partições e discos físicos (tipo SSD/HD e saúde)
- Diagnóstico de lentidão por regras: CPU, RAM, swap, disco cheio, HD mecânico, saúde do disco, uptime
- Programas na inicialização (Windows: Registro e pasta Inicializar; Mac: LaunchAgents e Itens de Login)
- Bateria (notebooks): desgaste, ciclos e carga (Windows via powercfg, Mac via system_profiler)
- Rede: latência, perda de conexão e tempo de DNS (testes TCP, sem precisar de administrador)
- Monitoramento com duração à escolha (ex.: `30`, `2 min`, `1h`; de 5 s a 1 h), com **gráficos ao vivo** de CPU, RAM e disco
- Limpeza de temporários: estimativa por pasta e remoção só com confirmação (apenas arquivos com mais de 24 h, só em pastas conhecidas, sem seguir atalhos)
- Relatório em `.txt`

## Roadmap
- [x] Estrutura, coletores básicos, análise por regras, menu de terminal, relatório .txt
- [x] Interface gráfica simples + executável (.exe / .app)
- [x] Programas de inicialização, tipo e saúde dos discos, monitoramento com tempo escolhido
- [x] Nota geral, abas e gráfico ao vivo
- [x] Bateria, rede e limpeza de temporários
- [ ] Atualizações do Windows e drivers com erro
- [ ] Ações: abrir Gerenciador de Tarefas, desativar programa de inicialização
- [ ] Relatório em HTML/PDF e histórico de diagnósticos
- [ ] Temperaturas e throttling
- [ ] Ícone próprio e tema escuro

## Como usar

**Versão com janela (.exe)**
- Windows: dê dois cliques em `build_windows.bat` (precisa de Python instalado). O executável sai em `dist\Diagnostico.exe`.
- Mac: `./build_mac.sh` gera `dist/Diagnostico.app`.
- Sem gerar o executável: `python run_gui.py`
- Os executáveis também são gerados automaticamente pelo GitHub Actions (aba Actions > Artifacts)

**Versão terminal**
- `pip install -r requirements.txt` e `python -m diagnostico`
