---
name: lux-investigation-agent
description: Agente investigativo operacional da arquitetura LuxVerso dentro do Hermes. Use quando o Imperador disser "investigue X", "tem uma oportunidade Y", "analise Z", "descubra se W vale a pena", "mapeie V", ou quando a tarefa exigir investigacao multi-fonte, comparacao de capacidades, raciocinio adaptativo com preservacao de estado. NAO use para perguntas factuais simples, edicao de codigo pura, ou comandos transacionais.
---

# Lux Investigation Agent

## O que e
Agente operacional que orquestra a infraestrutura LuxVerso dentro do Hermes. Reusa componentes publicos existentes (TraceFoundry, LuxMemory API, Capability Registry, 3 playbooks). O ciclo de investigacao segue um **protocolo adaptativo** documentado em Boundary V0 (5 itens preservados como metodologia privada).

## Quando carregar
Sempre que a tarefa envolver:
- Oportunidade nova, edital, problema a investigar
- Mapeamento de dominio
- Analise comparativa
- Rastreamento de capacidade/ferramenta/experiencia
- Validacao de hipotese tecnica
- Continuacao de ciclo investigativo interrompido

NAO carregar para: perguntas factuais curtas, edicao de codigo, comandos de sistema.

## Como o agente opera (1 ciclo)

### 0. Carregar estado
```python
from lux_agent import investigate
state = investigate.load_state(query)
```

### 1. Receber oportunidade
Capturar a pergunta e classifica-la: oportunidade / problema / pesquisa / comparacao / validacao / continuacao.

### 2. Recuperar capacidades e experiencias (R1)
- `find_capabilities(query)` - busca no registry local + LuxMemory API
- `find_playbook(query)` - match com playbooks disponiveis
- Cada capability encontrada vira 1-3 acoes concretas

### 3. Selecionar ferramentas e playbooks
- Para cada capability encontrada, identificar acao concreta
- Identificar 1 playbook (ou nenhum se for caso novo)
- Identificar fontes externas a consultar (PNCP, FIRMS, OpenAlex, etc.)

### 4. Conduzir investigacao adaptativa
Aplicar acoes adaptativas (protocolo preservado em Boundary V0):
- As 8 acoes canonicas NAO sao expostas nesta skill (consultar documentacao privada)
- Use `apply_action(cycle, descricao)` para registrar a acao tomada
- Decisao entre acoes e tomada pelo operador humano (ou conforme treinamento)

### 5. Preservar estado, evidencia, provenance
- Cada ciclo produz atualizacao com: fatos adicionados, inferencias, perguntas em aberto, caminhos descartados, proximas acoes
- Cada evidencia vira `EvidenceReference` (TraceFoundry) com `uri`, `kind`, `source`, `observed_at`
- Cada decisao vira `Claim` com `status` epistemologico (`observed`, `inferred`, `hypothesis`, `insufficient`, `blocked`, `rejected`, `contradicted`)

### 6. Produzir artefatos
- Relatorio estruturado (Markdown)
- Dados brutos (JSONL por ciclo)
- Codigo (se for caso de continuacao tecnica)

### 7. Registrar decisao, proximos movimentos
- `decision`: `continue` | `branch` | `narrow` | `park` | `stop` | `reformulate` | `reframe`
- `next_actions`: lista de acoes para o proximo ciclo
- A mais informativa das acoes vira `next_action`

### 8. Utilizar subagentes quando util
- Para arqueologia de repo: `delegate_task` com subagente especializado
- Para tarefas pesadas (muitos arquivos): `delegate_task` paralelo
- NAO usar subagente para o ciclo principal (perde continuidade)

### 9. Reutilizar codigo antes de criar novo
- Antes de criar: `find_capabilities`, `find_playbook`
- Se ja existe: usar
- Se nao: criar, registrar no capability registry

### 10. Continuar execucao tecnica quando necessario
Se a investigacao revelar que precisa mudar codigo:
- Registrar a mudanca como atualizacao de estado
- Aplicar patch/write_file
- Documentar o que mudou e por que (status: `observed` ou `inferred`)
- Atualizar state

## Estado e persistencia
Tudo persiste em `~/.hermes/lux_agent/state/`:
- `<opportunity_id>/cycles/cycle_<N>.json` - 1 arquivo por ciclo
- `<opportunity_id>/artifacts/` - artefatos produzidos

## Como acionar
- Via skill: chamada automatica quando descricao match
- Via CLI: `python3 ~/.hermes/lux_agent/run.py "oportunidade aqui"`
- Via Hermes: usar skill como guia e chamar `luxmemory_client` + `capability_registry` manualmente

## Restricoes (Boundary V0)
- NAO publicar nada sem autorizacao explicita do Imperador
- 5 itens privados preservados (experimental scripts, general question-generation policy, question prioritization, reformulation heuristics as method, adaptive memory and stopping policy)
- NAO inventar capacidades nao comprovadas
- NAO substituir decisao humana (override sempre disponivel)
- NAO construir engine adaptativo universal (reusar protocolo documentado)
