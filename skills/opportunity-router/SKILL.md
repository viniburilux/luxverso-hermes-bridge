---
name: opportunity-router
description: Triage e roteamento de oportunidades/problemas novos. Use quando o Imperador disser "tem uma [oportunidade]", "investigue [X]", "veja se [Y] vale a pena", "competição nova", "edital aberto", "cliente pediu", "mercado mudou". Carrega playbooks relevantes, busca capabilities no LuxMemory, identifica scripts reutilizáveis, e propõe estratégia inicial. Tools: terminal, read_file, web_search, memory.
license: MIT
version: 0.1.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [opportunity, triage, router, planning, intelligence, luxmemory]
    category: meta
    related_skills: [osint-investigation, subagent-driven-development, watchers]
---

# Opportunity Router

**Quando carregar:** O Imperador traz uma oportunidade, problema, edital, competição, cliente, mercado, ou pedido novo. Você precisa decidir como abordar.

**O que faz:** Classifica o problema → busca capabilities existentes no LuxMemory → identifica playbooks e skills relevantes → propõe estratégia → executa investigação inicial → produz primeiro resultado mensurável.

---

## Protocolo de Triagem (5 passos)

### 1. CLASSIFICAR
Extraia do pedido do Imperador:
- **Tipo:** competição (Kaggle) | edital público | cliente comercial | pesquisa | mercado | problema técnico
- **Domínio:** transparência | saúde | ambiente | educação | finanças | genérico
- **Prazo:** imediato (horas) | curto (dias) | médio (semanas)
- **Recursos disponíveis:** GPU | APIs abertas | datasets próprios | rede de contatos

### 2. BUSCAR no LuxMemory
**A API LuxMemory está rodando em http://127.0.0.1:8787.**

```python
import sys
sys.path.insert(0, '/app/.hermes/integrations')
from luxmemory_client import get_client
c = get_client()
# Buscar capabilities relevantes
caps = c.capabilities(query="<palavras-chave-do-problema>", limit=5)
# Buscar skills
skills = c.skills()
# Resumir projetos similares
resume = c.resume(query="<descrição-do-problema>", limit=3)
```

**Ou via curl:**
```bash
curl -s "http://127.0.0.1:8787/api/capabilities?q=<query>&limit=5"
curl -s "http://127.0.0.1:8787/api/search?q=<query>&mode=answer"
```

**Se a API não estiver rodando:** Suba com:
```bash
cd /app/luxverso-archive/LuxMemory/src
LUXMEMORY_ROOT=/app/luxverso-archive/LuxMemory \
PYTHONPATH=/app/.hermes/integrations \
python3 app_local.py
```

### 3. MATCHEAR com Playbooks
Leia os playbooks em `~/.hermes/playbooks/`:
- `investigate-new-domain.md` — qualquer "investigue X" genérico
- `repository-archaeology.md` — "mapeie esse repo"
- `data-source-discovery.md` — "encontre dados para X"
- `opportunity-triage.md` — "vale a pena investir nesse edital?"

Use o playbook mais próximo do tipo identificado no passo 1.

### 4. IDENTIFICAR Capacidades Locais
Consulte `~/.hermes/capabilities/registry.yaml` para ver se já temos:
- Scripts de coleta de dados (PNCP, FIRMS, EONET, etc)
- Pipelines (build_release, quality_layer, document_acquisition)
- Adapters (Dandi, OpenAlex, PatentsView, Zenodo)
- Metodologias (InvestigationState, ResearchMove, Claim, EvidenceGap)

### 5. EXECUTAR Investigação Inicial
- **Delegue para subagentes** se a tarefa for paralelizável
- **Carregue skills relevantes** (osint-investigation, subagent-driven-development, watchers)
- **Documente tudo** em `~/.hermes/mission_log/mission_log.jsonl`
- **Produza primeiro resultado mensurável** em ≤30 min

---

## Critérios de Decisão Go/No-Go

| Sinal | Go | No-Go |
|-------|-----|--------|
| Fonte oficial pública e aberta | ✅ | |
| Dados acessíveis sem auth | ✅ | |
| Cruzamento com base nossa | ✅ (alto valor) | |
| Tempo estimado < 2h | ✅ | |
| Auth complexa / rate limit | ⚠️ reavaliar | |
| Sem cruzamento possível | | ❌ |
| Dados privados/sensiveis | | ❌ (ético) |
| Tempo estimado > 8h | | ❌ |

## Exemplo de uso

**Imperador diz:** "Tem uma competição nova no Kaggle. Faltam 48 horas. Vale a pena entrar?"

**Você faz:**
```python
c = get_client()
caps = c.capabilities(query="kaggle competition agent")
# Exemplo: encontra CAP-OBS-HETEROGENEOUS_CORPUS_INTELLIGENCE (transferable)
resume = c.resume(query="competição ML agent", objective="entrar e produzir resultado")
# Identifica experiência passada (CGOV hoje, Kaggle-OpenAI-Agent-Security)
# Carrega playbook investigate-new-domain
# Propõe: usar TraceFoundry para registrar InvestigationState, gerar adapter se necessário
# Delega para 2 subagentes em paralelo
```

## Arquivos de Suporte

- `~/.hermes/capabilities/registry.yaml` — 21 capabilities catalogadas
- `~/.hermes/playbooks/*.md` — playbooks reutilizáveis
- `~/.hermes/integrations/luxmemory_client.py` — cliente Python
- `~/.hermes/mission_log/mission_log.jsonl` — log persistente
- `/app/luxverso-archive/LuxMemory/` — fonte de capabilities/skills
- `/app/luxverso-archive/TraceFoundry/src/oi_discovery/` — schemas formais

## Não-fazer

- NÃO subclassifique sem rodar a busca no LuxMemory
- NÃO inicie execução sem carregar pelo menos 1 playbook
- NÃO delegue sem critério claro (subagente precisa de goal + context)
- NÃO produza artefato sem registrar no mission_log

## Quando pedir decisão humana

- Trade-off ético (dados sensíveis)
- Decisão de risco (escrever em repo externo)
- Trade-off de tempo (>4h)
- Múltiplas oportunidades simultâneas

## Status de Desenvolvimento

- Versão: 0.1.0 (2026-08-31)
- API LuxMemory: ✅ operacional em :8787
- Client Python: ✅ testado
- 21 capabilities locais + 25 do LuxMemory + 9 skills indexadas
- Cobertura: 3 playbooks + 3 skills oficiais + 1 cliente integração
