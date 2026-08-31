# LuxVerso × Hermes Bridge

> Ponte operacional entre o ecossistema LuxVerso (TraceFoundry, Lux-Radar, Lux-Lab, LuxMemory) e o Hermes Agent v0.19.0.
> Materializa capacidades, playbooks, skills e integrações descobertas na **Missão LuxVerso Arqueologia** (2026-08-31).

## O que tem aqui

### `capabilities/registry.yaml`
21 capabilities catalogadas com evidência em código real.
Cada uma tem: id, name, type, domain, problem_types, tools_used, scripts, repo, paths, inputs, outputs, evidencia, reused_count, last_used, status, limitations, classe.

### `playbooks/`
3 playbooks operacionais (não conceituais):
- `investigate-new-domain.md` — explore→extract→structure→enrich→hypothesize→validate→artifact (2 casos reais)
- `repository-archaeology.md` — discover→structure→schemas→evidence→classify→register (2 casos reais)
- `data-source-discovery.md` — define→known→test→validate→cross→register (1 caso real)

### `skills/opportunity-router/`
Skill do Hermes que executa 5 passos:
1. CLASSIFICAR o tipo de oportunidade
2. BUSCAR no LuxMemory (API REST)
3. MATCHEAR com playbooks
4. IDENTIFICAR capabilities locais
5. EXECUTAR investigação inicial

### `integrations/`
Cliente Python para a API LuxMemory.

### `luxverso/LuxMemory_app_local.py`
App Flask patched (com ROOT parametrizável) que serve a API REST.

### `reports/arqueologia_report.json`
Relatório de arqueologia de TraceFoundry + Lux-Radar (gerado por subagente).

### `state.json` / `MISSION_REPORT.md`
Estado e relatório completo da missão.

## Como usar

### 1. Subir a API LuxMemory
```bash
cd /home/vinicius/luxverso-archive/LuxMemory/src
LUXMEMORY_ROOT=/home/vinicius/luxverso-archive/LuxMemory \
PYTHONPATH=/home/vinicius/.hermes/integrations \
python3 app_local.py
# API: http://127.0.0.1:8787
```

### 2. Do Hermes, usar o cliente
```python
import sys
sys.path.insert(0, '/home/vinicius/.hermes/integrations')
from luxmemory_client import get_client
c = get_client()
caps = c.capabilities(query="PNCP", limit=5)
```

### 3. Skill opportunity-router
Já carrega automaticamente no próximo turno do Hermes (skill instalada em `~/.hermes/skills/opportunity-router/`).

## Métricas da Missão

- 35 repos descobertos (22 públicos + 13 privados)
- 12 repos locais analisados
- 21 capabilities catalogadas
- 25 capabilities LuxMemory integradas
- 5 skills instaladas (1 própria + 3 oficiais + 1 default)
- 3 playbooks operacionais
- 3 subagentes arqueólogos usados
- 3 testes reais validados

## Origem

Gerado pela **Missão LuxVerso Arqueologia** (2026-08-31).
Documentação completa: `MISSION_REPORT.md`.
