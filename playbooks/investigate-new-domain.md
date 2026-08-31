# Playbook: Investigar Domínio Novo

**Evidência:** Aplicado em 2 oportunidades reais:
1. **Superbet** (2026-08): exp1-7 em `~/.hermes/lab/` — sucesso completo, gerou 7 scripts + 1.5MB de dados estruturados
2. **Concurso 2026** (2026-XX-XX): 4 etapas (CONTRATOS → FIRMS → CNES → IBJE) — 4 iniciativas PROVEN

**Método:** Sequência de 7 fases, cada fase produz artefato observável.

---

## Quando usar

Vini disser qualquer coisa como:
- "investigue [X]"
- "tem uma oportunidade em [Y]"
- "olha esse mercado/produto/API"
- "veja se [Z] dá pra atacar"
- "queria entender como funciona [W]"

## Sequência operacional

### FASE 1 — EXPLORE (Observar)
**Objetivo:** Mapear superfície do domínio, identificar URLs, páginas-chave, APIs visíveis.

**Ações concretas:**
1. Listar 3-5 URLs principais do domínio (homepage, página de produto, busca, dashboard)
2. Navegar cada uma (browser ou web_extract)
3. Capturar:
   - Estrutura HTML básica
   - Links principais
   - Padrões de URL (/api/, /v1/, /graphql, etc)
   - Indícios de auth/login
4. Salvar HTML/text cru em `observations/obs_<n>_<fonte>.txt`

**Output:** Lista de URLs + snapshots brutos.

### FASE 2 — EXTRACT (Coletar dados)
**Objetivo:** Extrair dados brutos de fontes acessíveis.

**Ações concretas:**
1. Identificar endpoints de API (mesmo que interno)
2. Capturar responses de `https://api.*`, `https://*.api.*`, `graphql`
3. Se necessário, usar network capture no browser
4. Salvar cada response em arquivo JSON: `data/raw_<fonte>_<n>.json`
5. **SEMPRE** salvar:
   - URL completa
   - Status HTTP
   - Method
   - Content-Type
   - Timestamp
   - SHA-256 do payload

**Output:** Diretório `data/` com JSONs brutos + metadados.

### FASE 3 — STRUCTURE (Normalizar)
**Objetivo:** Padronizar dados em formato único (records).

**Ações concretas:**
1. Definir schema único: cada record = `{id, name, ts, source, fields...}`
2. Converter cada JSON bruto em records
3. Deduplicar por id
4. Salvar como `structured/<dataset>_flat.json` ou `.parquet`
5. Validar com checksums

**Output:** Dataset tabular limpo.

### FASE 4 — ENRICH (Cruzar)
**Objetivo:** Cruzar com bases externas (IBGE, FIRMS, Querido Diário, etc).

**Ações concretas:**
1. Identificar chaves de junção (municipality, date, CNPJ, IBGE code)
2. Para cada record, fazer lookup em fontes conhecidas
3. Salvar enriched: `enriched/<dataset>_enriched.json`
4. Marcar campos com `provenance: source_uri` + `observed_at`

**Output:** Dataset com informação cruzada.

### FASE 5 — HYPOTHESIZE (Gerar perguntas)
**Objetivo:** Formular hipóteses testáveis sobre o domínio.

**Ações concretas:**
1. Listar 3-5 perguntas de valor público
2. Para cada pergunta, definir:
   - Hipótese nula
   - Forma de testar (query específica, threshold, filtro)
   - Métrica de sucesso
3. Salvar em `hypotheses/h<n>_<nome>.json`:
   ```json
   {
     "id": "h1",
     "question": "Há editais emergenciais em municípios com queimadas ativas?",
     "hypothesis": "Sim, > 5 em 30 dias",
     "test_query": "cross-data CONTRATOS x FIRMS",
     "evidence_threshold": 5,
     "status": "open"
   }
   ```

**Output:** Lista de hipóteses com critério de aceite.

### FASE 6 — VALIDATE (Testar)
**Objetivo:** Executar queries que validam/invalidam hipóteses.

**Ações concretas:**
1. Para cada hipótese, rodar o teste
2. Salvar resultado em `hypotheses/h<n>_result.json`:
   ```json
   {
     "hypothesis_id": "h1",
     "result": "supported | contradicted | insufficient",
     "evidence_count": 7,
     "evidence_ids": ["e1", "e2", ...],
     "confidence": 0.85
   }
   ```
3. Marcar hipótese como `resolved` se houver evidência suficiente

**Output:** Hipóteses validadas/invalidadas.

### FASE 7 — ARTIFACT (Materializar)
**Objetivo:** Transformar achado em artefato público (reúso, demo, submission).

**Ações concretas:**
1. Se hipótese suportada, escolher formato:
   - **Dataset** (CSV/Parquet/GeoJSON) + schema + dicionário
   - **Demo** (HTML estático) com visualização
   - **Análise** (relatório com achados quantificados)
   - **Submissão** (texto + URL + dados)
2. Criar README explicando: fontes, transformação, limitações, reprodutibilidade
3. Versionar (tag ou release)
4. Salvar no destino apropriado (Drive, GitHub, etc)
5. **Logar a operação no `~/.hermes/mission_log/mission_log.jsonl`**

**Output:** Artefato público pronto pra reúso.

---

## Critérios de decisão Go/No-Go após Fase 1

| Sinal | Go/No-Go |
|-------|----------|
| Fonte oficial pública e aberta | ✅ Go |
| Dados acessíveis sem auth | ✅ Go |
| Cruzamento com 1+ base nossa | ✅ Go (alto valor) |
| Tempo estimado < 2h | ✅ Go |
| Custo computacional aceitável | ✅ Go |
| Auth complexa / rate limit | ⚠️ Reavaliar |
| Dados privados/sensiveis | ❌ No-Go (ético) |
| Sem cruzamento possível | ❌ No-Go (sem diferencial) |

## Lições aprendidas (de casos reais)

1. **Catu BA** (Concurso 2026): 1 edital Dispensa + 1 foco FIRMS a 3.99km — achado com 1 cruzamento geográfico
2. **Marinha 28/08** (Concurso 2026): 6 dispensas no mesmo dia — achado com agrupamento temporal
3. **CE 62%** (Concurso 2026): anomalia estadual — achado com agregação por UF

Todos vieram do MESMO playbook (Fases 1-7).

## Não-fazer (anti-patterns)

- **NÃO leia 1000 linhas de cada arquivo sem foco** — arqueologia direcionada
- **NÃO invente dados** — se não tem fonte, registre como `insufficient_evidence`
- **NÃO pule Fases 1-3** — coleta mal-feita = análise inútil
- **NÃO fique em loop** — se Fase 6 não converge em 30min, registrar e ir pra próxima hipótese
- **NÃO faça tudo em uma sessão** — se a sessão acabar, persistir tudo (mission_log, scratch/)

## Quando pedir ajuda do Imperador

- Decisão ética (dados sensíveis)
- Decisão de risco (write em Drive/repo externo)
- Decisão de tempo (>4h estimado)
- Decisão de prioridade (múltiplas oportunidades simultâneas)
- Bloqueio técnico (auth complexa, infra não disponível)

## Scripts reutilizáveis (em ~/.hermes/scripts/)

- `extract_with_provenance.py` — FASE 2+4 (extrai + cruza + provenance)
- `hypothesis_tracker.py` — FASE 5+6 (gerencia hipóteses)
- `release_builder.py` — FASE 7 (gera dataset + demo)
- `decision_matrix.py` — Go/No-Go (avalia sinais)

(ainda não existem - são gaps conhecidos)

---

**Status:** proven
**Confidence:** 0.85
**Last used:** 2026-XX-XX (CGOV)
**Reused count:** 2
