"""
EXEMPLO REAL: investigacao completa (2 ciclos) — caso CGU Cross-Data 2026.

Mostra o agente em acao: cycle 0 (discovery) + cycle 1 (reformulacao) + render final.

Este e o caso que sera usado como exemplo na documentacao.
"""
import sys
sys.path.insert(0, '/home/vinicius/.hermes')
sys.path.insert(0, '/home/vinicius/.hermes/integrations')
sys.path.insert(0, '/home/vinicius/luxverso-archive/TraceFoundry/src')

from lux_agent import (
    investigate, save_cycle, load_state, render_report,
    find_capabilities, find_playbook, apply_operator,
    add_evidence, add_claim, add_gap, discard_path, queue_next, set_decision,
    assess, to_luxmemory_link,
)

print("="*70)
print("EXEMPLO REAL — Investigacao CGU Cross-Data 2026 (workflow completo)")
print("="*70)

OPORTUNIDADE = "tem um edital CGU 2026 sobre Cross-Data? Vale a pena investigar?"

# ============================================================================
# CYCLE 0: discovery inicial
# ============================================================================
print("\n" + "─"*70)
print("CYCLE 0 — DISCOVERY (P → R1 → S → P')")
print("─"*70)

c = investigate(OPORTUNIDADE)
print(f"\n[1] P: {c.question[:80]}")
print(f"    opid={c.opportunity_id}")

print(f"\n[2] R1 (recuperacao):")
caps = find_capabilities("CGU cross-data reuso", limit=5)
for x in caps[:3]:
    if x['source'] == 'local_registry':
        print(f"    [registry] {x['capability'].get('name')}: score={x['score']}")
    else:
        print(f"    [luxmemory] {x.get('match_name', '?')}: score={x['score']}")
pb = find_playbook("CGU cross-data reuso")
print(f"    [playbook] {pb.name if pb else 'nenhum'}")

print(f"\n[3] S (sinais extraidos):")
apply_operator(c, 'radiografar')
apply_operator(c, 'densidade')
print(f"    2 operadores: radiografar + densidade")

# Evidencias (3: edital web + audit local + repo GitHub)
e1 = add_evidence(c, kind='web_url', source='CGU', uri='https://www.gov.br/cgu/pt-br/concurso-2026', note='2o Concurso Reuso Dados 2026')
e2 = add_evidence(c, kind='local_doc', source='hermes', uri='/home/vinicius/.hermes/cgu_discovery_audit.md', note='Auditoria previa do Hermes')
e3 = add_evidence(c, kind='github_repo', source='viniburilux/cgu-reuso-2026', uri='https://github.com/viniburilux/cgu-reuso-2026', note='Materializacao previa: 4 iniciativas PROVEN')
print(f"    3 evidencias: {e1.kind}, {e2.kind}, {e3.kind}")

# Claims
add_claim(c, 'CGU 2026 tem 2o Concurso Reuso de Dados', 'observed', (e1.evidence_id,))
add_claim(c, '4 iniciativas cross-data materializadas (PNCP+FIRMS+CNES+IBGE)', 'observed', (e2.evidence_id, e3.evidence_id))
add_claim(c, 'Cross-Data Validator ~80% codigo pronto', 'inferred', (e2.evidence_id, e3.evidence_id))
add_claim(c, 'Submissao aproveitaria estado atual', 'hypothesis', gap_ids=('gp_001',))
print(f"    4 claims: observed, observed, inferred, hypothesis")

# Gaps
add_gap(c, 'Prazo exato do edital 2026', 'critical', ('EDITAL_URL',))
add_gap(c, 'Criterios de pontuacao detalhados', 'material', ('EDITAL_PDF',))
add_gap(c, 'GPU/Earth Engine para GhostWorks', 'minor')
print(f"    3 gaps: critical, material, minor")

# Paths descartados
discard_path(c, 'PNCP sozinho sem cross-data', 'Escopo exclue')
discard_path(c, 'API nova do zero', 'Reusar TraceFoundry+pncp-data-pipeline')
discard_path(c, 'GPU/Earth Engine local', 'Sem sudo, bloqueado')
print(f"    3 paths descartados")

# Decisao + proxima
set_decision(c, 'continue')
queue_next(c, 'Consultar edital e extrair prazos+criterios', reason='Resolver gap critico de prazo', query_plan='web_extract(URL)')
queue_next(c, 'Cruzar 4 PROVEN com criterios', reason='Mapear match para pontuacao', query_plan='comparar 4 iniciativas vs criterios do edital')
print(f"    decision: continue")
print(f"    2 proximas perguntas")

# Assess
ass = assess(c)
print(f"\n[4] assess_manifest: {ass['conclusion']} (basis={ass['basis']})")
print(f"    next_action: {ass['next_action']}")

save_cycle(c)
print(f"\n[5] Cycle 0 salvo")

# ============================================================================
# CYCLE 1: continuacao (auto-resume + reformulate)
# ============================================================================
print("\n" + "─"*70)
print("CYCLE 1 — CONTINUACAO (P' → R2 → S → P'')")
print("─"*70)

c2 = investigate(OPORTUNIDADE, auto_resume=True)
print(f"\n[1] Auto-resume: cycle_n={c2.cycle_n}")
print(f"    Estado herdado: {len(c2.evidence)} evid, {len(c2.claims)} claims, {len(c2.gaps)} gaps, {len(c2.paths_discarded)} paths")

print(f"\n[2] R2: executando 'Consultar edital' (1a proxima de cycle 0)")
apply_operator(c2, 'reformular')
print(f"    Operador: reformular")

# Nova evidencia do edital
e_new = add_evidence(c2, kind='web_url', source='CGU', uri='https://www.gov.br/cgu/pt-br/concurso-2026/edital.pdf', note='PDF edital extraido')
add_claim(c2, 'CGU 2026 prazo: 60 dias a partir de 15/09/2026', 'observed', (e_new.evidence_id,))
print(f"    Evidencia: {e_new.evidence_id[:30]}...")

# Gap critico resolvido
gap_critico = c2.gaps[0]
discard_path(c2, f'gap {gap_critico.gap_id}: prazo edital', 'Resolvido: 60d a partir de 15/09')
print(f"    Gap critico resolvido: {gap_critico.gap_id[:30]}...")

# Novo gap
add_gap(c2, 'Categorias de submissoes aceitas', 'material', ('EDITAL_CAT',))
print(f"    Novo gap material: categorias de submissao")

set_decision(c2, 'narrow')
queue_next(c2, 'Cruzar prazo 60d com escopo', reason='Verificar viabilidade', query_plan='comparar escopo vs tempo')
print(f"    decision: narrow, 1 proxima")

ass2 = assess(c2)
print(f"\n[3] assess_manifest: {ass2['conclusion']} (basis={ass2['basis']}, candidates={ass2['candidate_count']}, rejected={ass2['rejected_count']})")

save_cycle(c2)
print(f"\n[4] Cycle 1 salvo")

# ============================================================================
# BRIDGE: link para LuxMemory
# ============================================================================
print("\n" + "─"*70)
print("BRIDGE → LUXMEMORY")
print("─"*70)

link = to_luxmemory_link(c2)
print(f"\nlink_id: {link.get('link_id')}")
print(f"source_type: {link.get('source_type')}")
print(f"observations: {len(link.get('observations', []))}")
print(f"interpretation.status: {link.get('interpretation', {}).get('status')}")
print(f"interpretation.decision: {link.get('interpretation', {}).get('decision')}")
print(f"interpretation.limitations: {link.get('interpretation', {}).get('limitations')}")

# ============================================================================
# RELATORIO FINAL
# ============================================================================
print("\n" + "="*70)
print("RELATORIO FINAL (cycle 1 acumulado)")
print("="*70)
print(render_report(c2))
