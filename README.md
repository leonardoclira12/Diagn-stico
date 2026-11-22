# Diagnóstico

Sistema de diagnóstico para Windows e macOS que verifica o computador peça por peça
e aponta causas prováveis de lentidão.

## Decisões
- Python + psutil (multiplataforma)
- Interface simples de terminal (estilo CMD), sem frescura
- Sem IA: regras simples e transparentes
- Um commit por etapa

## O que o app faz
- **Janela em tema escuro** com menu lateral, nota geral em anel (Saudável, Atenção ou Crítico) e uma explicação curta em cada bloco
- Páginas: Resumo, Inicialização, Discos, Bateria, Rede, Sistema, Segurança, Hardware, Monitoramento, Processos, Limpeza, Ferramentas e Relatório completo
- Inventário: sistema, CPU, RAM, partições e discos físicos (tipo SSD/HD e saúde)
- Diagnóstico de lentidão por regras: CPU, RAM, swap, disco cheio, HD mecânico, saúde do disco, uptime
- Programas na inicialização (Windows: Registro e pasta Inicializar; Mac: LaunchAgents e Itens de Login)
- Bateria (notebooks): desgaste, ciclos e carga (Windows via powercfg, Mac via system_profiler)
- Rede: latência, perda de conexão e tempo de DNS (testes TCP, sem precisar de administrador)
- Monitoramento com duração à escolha (ex.: `30`, `2 min`, `1h`; de 5 s a 1 h), com **gráficos ao vivo** de CPU, RAM e disco
- Limpeza de temporários: estimativa por pasta e remoção só com confirmação (apenas arquivos com mais de 24 h, só em pastas conhecidas, sem seguir atalhos)
- **Sistema:** atualizações pendentes e reinício pendente, dispositivos com driver com erro, erros recentes (telas azuis, desligamentos inesperados, erros de disco, travamentos)
- **Tempo de boot** e o que mais atrasou a inicialização (Windows)
- **Segurança:** antivírus e firewall (Windows); FileVault, firewall, SIP e Gatekeeper (Mac)
- **Hardware:** modelo, número de série, placa-mãe, BIOS, pentes de RAM e placa de vídeo (com a idade do driver)
- **Ferramentas:** atalhos para as ferramentas do sistema e opção de reabrir como administrador (Windows)
- Relatório em `.txt`

## Roadmap
- [x] Estrutura, coletores básicos, análise por regras, menu de terminal, relatório .txt
- [x] Interface gráfica simples + executável (.exe / .app)
- [x] Programas de inicialização, tipo e saúde dos discos, monitoramento com tempo escolhido
- [x] Nota geral, abas e gráfico ao vivo
- [x] Bateria, rede e limpeza de temporários
- [x] Atualizações, drivers com erro, erros recentes, tempo de boot, segurança e hardware
- [x] Atalhos para ferramentas do sistema
- [ ] Ações que mexem no sistema: desativar programa de inicialização, encerrar processo, limpar cache de DNS (sempre com confirmação)
- [ ] Relatório em HTML/PDF e histórico de diagnósticos
- [ ] Temperaturas e throttling
- [x] Tema escuro e menu lateral
- [ ] Ícone próprio

## Como usar

**Versão com janela (.exe)**
- Windows: dê dois cliques em `build_windows.bat` (precisa de Python instalado). O executável sai em `dist\Diagnostico.exe`.
- Mac: `./build_mac.sh` gera `dist/Diagnostico.app`.
- Sem gerar o executável: `python run_gui.py`
- Os executáveis também são gerados automaticamente pelo GitHub Actions (aba Actions > Artifacts)

**Versão terminal**
- `pip install -r requirements.txt` e `python -m diagnostico`
