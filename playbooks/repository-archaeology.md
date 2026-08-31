# Playbook: Repository Archaeology

**Evidência:** Aplicado 2 vezes com sucesso:
1. **Concurso 2026** (2026-XX-XX): reconstrução de 22 repos LuxVerso → `HERMES_LUXVERSO_ARCHITECTURE.md` (482 linhas)
2. **Missão Luxverso-Discovery** (2026-XX-XX): descoberta de 35 repos + estrutura + capabilities → `arqueologia_report.json` (18KB)

**Quando usar:** Vini disser "mapeie esse repo", "entenda essa arquitetura", "veja se tem coisa útil no projeto X".

---

## Sequência

### FASE 1 — DESCOBRIR
1. Verificar se já existe clone local: `find ~ -name '.git' -type d 2>/dev/null | head`
2. Se não existir, clonar: `git clone <url> /tmp/arqueo-<nome> --depth 1`
3. Listar estrutura: `tree -L 3 /tmp/arqueo-<nome>` ou `ls -la`

### FASE 2 — ESTRUTURAR
1. Listar top-level: arquivos de config (README, LICENSE, pyproject.toml, package.json)
2. Identificar entrypoints: `setup.py`, `pyproject.toml [project.scripts]`, `package.json "bin"`
3. Listar diretórios relevantes: `src/`, `lib/`, `tests/`, `docs/`, `scripts/`, `examples/`

### FASE 3 — SCHEMAS E CONTRATOS
1. Procurar `*.json` em `schemas/`, `data/`, `examples/`
2. Para cada schema, ler primeiro 50 linhas: título, required fields, descrição
3. Listar **todos os .py em src/** (não tests/) e identificar classes/funções principais

### FASE 4 — EVIDÊNCIAS
1. Buscar por `assert` em tests/ — indica uso correto
2. Buscar por `if __name__ == "__main__"` — scripts executáveis
3. Buscar por `TODO`, `FIXME`, `XXX` — debt técnico
4. Buscar por `API_KEY`, `secret` — dependências externas

### FASE 5 — CLASSIFICAR
Para cada artefato encontrado, classificar:
- **A. REUTILIZAR DIRETAMENTE** — pode ser importado sem modificação
- **B. ADAPTAR** — requer mudanças pequenas
- **C. TRANSFORMAR EM SKILL** — vale virar skill do Hermes
- **D. TRANSFORMAR EM TOOL** — vale virar tool/script
- **E. TRANSFORMAR EM PLAYBOOK** — vale virar playbook (método)
- **F. INDEXAR COMO CAPABILITY** — vale adicionar ao registry
- **G. REFERÊNCIA** — útil saber que existe
- **H. NÃO REUTILIZÁVEL** — não tem valor pra nós

### FASE 6 — REGISTRAR
1. Salvar achados em `~/.hermes/mission_log/` com categoria `arqueologia`
2. Atualizar `~/.hermes/capabilities/registry.yaml` com novas capabilities
3. Criar/atualizar skills ou playbooks derivados

---

## Comandos úteis

```bash
# Estrutura
tree -L 3 --dirsfirst
ls -la
find . -name '*.py' -not -path '*/tests/*' | head -20

# Documentos
find . -name 'README*' -o -name '*.md' -not -path '*/node_modules/*' | head -10

# Schemas
find . -name '*.json' -path '*/schema*' | head -10
find . -name '*.schema.json' | head

# Entry points
grep -E "scripts|entry_points" pyproject.toml

# Classes/funções principais
grep -rE "^class |^def " --include='*.py' . | grep -v test | head -30

# Secrets/keys
grep -rE "API_KEY|SECRET|TOKEN" --include='*.py' . | head

# Integrações conhecidas
grep -rE "hermes|integration|bridge" --include='*.py' --include='*.md' . | head -20
```

---

## Outputs típicos

- `mission_log/arqueologia_<repo>_<date>.json` com chaves: structure, schemas, modules, central_files, integration_refs, key_findings
- Updates em `capabilities/registry.yaml`
- Skills/playbooks novos se descoberta for significativa

---

## Lições aprendidas

1. **NÃO leia 1000 linhas de cada arquivo** — arqueologia direcionada por evidência
2. **Schemas JSON valem ouro** — são contratos formais reutilizáveis
3. **Tests revelam uso correto** — leia os primeiros 50 linhas de cada test
4. **Bridge files revelam integrações planejadas** — `bridge.py`, `integration.py`, `_connect.py` etc
5. **README raiz vs README em subpastas** — o raiz é visão geral, os subpastas são específicos

---

**Status:** proven
**Confidence:** 0.90
**Last used:** 2026-XX-XX (Missão Luxverso Arqueologia)
**Reused count:** 2
