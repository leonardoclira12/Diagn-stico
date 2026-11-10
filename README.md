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
3. [ ] Análise de lentidão (regras)
4. [ ] Menu de terminal
5. [ ] Exportar relatório em texto
6. [ ] Próximos: bateria, rede, SMART, programas de inicialização, temperaturas
