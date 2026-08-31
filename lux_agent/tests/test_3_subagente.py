"""
TESTE 3: Subagente arqueologo via delegate_task.
Simula: Hermes detecta que precisa investigar 1 repo novo, dispara subagente,
recebe evidencia estruturada, integra no ciclo.
"""
import sys
sys.path.insert(0, '/home/vinicius/.hermes')
sys.path.insert(0, '/home/vinicius/.hermes/integrations')
sys.path.insert(0, '/home/vinicius/luxverso-archive/TraceFoundry/src')

from lux_agent import (
    investigate, save_cycle, add_evidence, add_claim, add_gap,
    discard_path, queue_next, set_decision, apply_operator, render_report,
)

print("="*70)
print("TESTE 3 — Subagente arqueologo (delegate_task)")
print("="*70)

# Cenario: investigar oportunidade nova (um repo publico novo do viniburilux)
oportunidade = "investigue o repo pncp-data-pipeline para reuso"
c = investigate(oportunidade)
print(f"\n[1] Ciclo criado: opid={c.opportunity_id}")

# R1: operador radiografar
apply_operator(c, 'radiografar')
print(f"  Operador: radiografar")

# Hermes detecta que precisa entender o repo. Dispara subagente via delegate_task.
# (Aqui simulamos o retorno do subagente; o Hermes real chamaria delegate_task)
subagente_result = {
    "structure": "pncp-data-pipeline/ (5 diretorios, 23 arquivos Python, 8 schemas JSON)",
    "main_files": ["pncp_api.py", "normalize.py", "parquet_writer.py", "manifest.py"],
    "schemas": ["contrato.json", "compra.json", "orgao.json", "release.json"],
    "public_url": "https://github.com/viniburilux/pncp-data-pipeline",
    "size_mb": 12,
    "public": True,
    "has_tests": True,
    "test_coverage_estimate": "70%",
    "can_be_integrated_as_is": True,
    "integration_effort_hours": 4,
    "limitations": ["API rate-limited", "schema version v0.2", "nao tem auth implementada"],
}

# Adicionar evidencia do subagente
e_sub = add_evidence(
    c,
    kind='subagent_report',
    source='delegate_task[arqueologo]',
    uri='https://github.com/viniburilux/pncp-data-pipeline',
    record_id='pncp-data-pipeline-investigation-v1',
    note='Subagente fez arqueologia read-only do repo publico'
)
print(f"  Evidencia do subagente: {e_sub.evidence_id}")

# Claims baseados no retorno do subagente
cl1 = add_claim(c, statement='pncp-data-pipeline tem 23 .py + 8 schemas, repo publico', status='observed', evidence_ids=(e_sub.evidence_id,))
cl2 = add_claim(c, statement='Tem tests, cobertura ~70%, integracao em ~4h', status='inferred', evidence_ids=(e_sub.evidence_id,))
cl3 = add_claim(c, statement='API rate-limited, schema v0.2, sem auth - sao limitacoes', status='observed', evidence_ids=(e_sub.evidence_id,))
cl4 = add_claim(c, statement='Pode ser integrado como dependencia externa (consumidor)', status='inferred', evidence_ids=(e_sub.evidence_id,))
print(f"  4 claims derivados do subagente")

# Operadores aplicados
apply_operator(c, 'densidade')
apply_operator(c, 'ponte_inesperada')
print(f"  3 operadores: radiografar + densidade + ponte_inesperada")

# Gap
g1 = add_gap(c, statement='Schema v0.2 estavel? Validar breaking changes', severity='critical', required_evidence=('SCHEMA_CHANGELOG',))
g2 = add_gap(c, statement='Rate limit especifico (quantas req/s?)', severity='material', required_evidence=('API_DOCS',))
print(f"  2 gaps: {g1.gap_id} (critical), {g2.gap_id} (material)")

# Path descartado: tentar fork+modificar
discard_path(c, 'forkar o repo e modificar internamente', 'Reusar como dependencia externa preserva origem, evita manter fork')
print(f"  1 path descartado")

# Decisao
set_decision(c, 'continue')
queue_next(c, 'Verificar changelog do schema v0.2', reason='Resolver gap critical', query_plan='web_extract(github.com/viniburilux/pncp-data-pipeline/blob/main/CHANGELOG.md)')
queue_next(c, 'Testar integracao minima em sandbox', reason='Validar ~4h de esforco', query_plan='pip install git+... + 1 teste de smoke')
print(f"  decision: {c.decision}, 2 proximas perguntas")

# Salvar
path = save_cycle(c)
print(f"\n[2] Cycle 0 salvo: {path}")
print(f"  evidencia: {len(c.evidence)}")
print(f"  claims: {len(c.claims)}")
print(f"  gaps: {len(c.gaps)}")
print(f"  paths_discarded: {len(c.paths_discarded)}")
print(f"  operadores: {len(c.applied_operators)}")

print("\n" + render_report(c))
print("✓ TESTE 3 PASSOU")
