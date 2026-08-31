"""
TESTE 1: Investigação completa do agente — "tem um edital sobre Cross-Data + CGU 2026?"

Cenário real: 2o Concurso CGU sobre reuso de dados. O agente deve:
1. Criar ciclo
2. R1: buscar capacidades LuxMemory + registry + playbook
3. S: extrair sinais (evidências, claims, gaps, paths descartados)
4. P': decidir próximo + salvar
5. Renderizar relatório
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
print("TESTE 1 — Investigação CGU Cross-Data 2026")
print("="*70)

# 1. Criar ciclo
oportunidade = "tem um edital CGU 2026 sobre Cross-Data? Vale a pena investigar?"
c = investigate(oportunidade)
print(f"\n[1] Ciclo criado: opid={c.opportunity_id}, cycle_n={c.cycle_n}")

# 2. R1: buscar capacidades
print(f"\n[2] R1: Buscando capacidades...")
caps = find_capabilities("CGU cross-data reuso", limit=5)
print(f"  Encontradas {len(caps)} capacidades:")
for x in caps:
    if x['source'] == 'local_registry':
        print(f"    [local] {x['capability'].get('name')}: {x['capability'].get('description', '')[:80]}")
    else:
        print(f"    [luxmemory] {x.get('match_name', str(x.get('match',''))[:100])}")
playbook = find_playbook("CGU cross-data reuso")
print(f"  Playbook: {playbook.name if playbook else 'nenhum'}")

# 3. Adicionar operadores
print(f"\n[3] Operadores AOM aplicados:")
apply_operator(c, 'radiografar')
print(f"  ✓ radiografar (corpus -> superficie de decisao)")
apply_operator(c, 'densidade')
print(f"  ✓ densidade (priorizar por recorrencia)")

# 4. Adicionar evidências
print(f"\n[4] Evidências registradas:")
e1 = add_evidence(c, kind='web_url', source='CGU', uri='https://www.gov.br/cgu/pt-br/...', note='Edital 2o Concurso Reuso Dados 2026')
e2 = add_evidence(c, kind='local_doc', source='hermes/cgu_discovery_audit.md', uri='/home/vinicius/.hermes/cgu_discovery_audit.md', note='Auditoria previa do Hermes')
e3 = add_evidence(c, kind='github_repo', source='viniburilux/cgu-reuso-2026', uri='https://github.com/viniburilux/cgu-reuso-2026', note='Materializacao previa do Hermes (4 iniciativas PROVEN)')
print(f"  ✓ {e1.evidence_id}: {e1.kind} {e1.source}")
print(f"  ✓ {e2.evidence_id}: {e2.kind} {e2.source}")
print(f"  ✓ {e3.evidence_id}: {e3.kind} {e3.source}")

# 5. Adicionar claims
print(f"\n[5] Claims:")
cl1 = add_claim(c, statement='CGU 2026 tem 2o Concurso Reuso de Dados ja aberto', status='observed', evidence_ids=(e1.evidence_id,), note='Confirmado por CGU + repo previo')
cl2 = add_claim(c, statement='4 iniciativas cross-data ja foram materializadas (PNCP+FIRMS+CNES+IBGE)', status='observed', evidence_ids=(e2.evidence_id, e3.evidence_id), note='Confirmado por auditoria previa')
cl3 = add_claim(c, statement='Cross-Data Validator tem 80% do codigo pronto', status='inferred', evidence_ids=(e2.evidence_id, e3.evidence_id), note='Inferencia por sobreposicao de evidencia')
cl4 = add_claim(c, statement='Submissao aproveitaria estado atual do agente', status='hypothesis', evidence_ids=(), gap_ids=('gp_001',), note='Hipotese, precisa validacao')
print(f"  ✓ {cl1.claim_id}: {cl1.status} - {cl1.statement[:60]}")
print(f"  ✓ {cl2.claim_id}: {cl2.status} - {cl2.statement[:60]}")
print(f"  ✓ {cl3.claim_id}: {cl3.status} - {cl3.statement[:60]}")
print(f"  ✓ {cl4.claim_id}: {cl4.status} - {cl4.statement[:60]}")

# 6. Adicionar gaps
print(f"\n[6] Gaps:")
g1 = add_gap(c, statement='Prazo exato do edital 2026', severity='critical', required_evidence=('CGU_EDITAL_URL',))
g2 = add_gap(c, statement='Criterios de pontuacao detalhados', severity='material', required_evidence=('CGU_EDITAL_PDF',))
g3 = add_gap(c, statement='Disponibilidade de GPU/Earth Engine para GhostWorks', severity='minor', required_evidence=())
print(f"  ✓ {g1.gap_id}: {g1.severity} - {g1.statement}")
print(f"  ✓ {g2.gap_id}: {g2.severity} - {g2.statement}")
print(f"  ✓ {g3.gap_id}: {g3.severity} - {g3.statement}")

# 7. Caminhos descartados
print(f"\n[7] Caminhos descartados:")
discard_path(c, 'investigar solo os editais PNCP sem cross-data', 'A pergunta e sobre CROSS-data, escopo exclue PNCP sozinho')
discard_path(c, 'construir nova API do zero', 'TraceFoundry+pncp-data-pipeline ja existem, reusar')
discard_path(c, 'tentar GPU/Earth Engine local', 'Sem sudo, bloqueado por libs nativas; hipotese rejeitada por agora')
print(f"  3 paths descartados")

# 8. Decisao e proximas
print(f"\n[8] Decisao:")
set_decision(c, 'continue')
queue_next(c, 'Consultar edital CGU 2026 e extrair prazos+criterios', reason='Resolver gap critico de prazo', query_plan='web_extract(URL) -> parse -> save artifacts')
queue_next(c, 'Cruzar 4 iniciativas PROVEN com criterios do edital', reason='Mapear match para pontuacao', query_plan='read_file(cgu_discovery_audit.md) + aplicar matriz')
print(f"  decision: {c.decision}")
print(f"  2 proximas perguntas")

# 9. Salvar
path = save_cycle(c)
print(f"\n[9] Ciclo salvo em: {path}")

# 10. Assess
print(f"\n[10] assess_manifest (TraceFoundry):")
ass = assess(c)
print(f"  conclusion: {ass['conclusion']}")
print(f"  basis: {ass['basis']}")
print(f"  candidates: {ass['candidate_count']}")
print(f"  rejected: {ass['rejected_count']}")
print(f"  next_action: {ass['next_action']}")

# 11. Bridge para LuxMemory
print(f"\n[11] Bridge Hermes->LuxMemory (TraceFoundry.build_link):")
link = to_luxmemory_link(c)
print(f"  link_id: {link.get('link_id')}")
print(f"  source_type: {link.get('source_type')}")
print(f"  observations: {len(link.get('observations', []))}")

# 12. Render
print(f"\n[12] Relatorio Markdown:")
print("-"*70)
print(render_report(c))
print("-"*70)
print(f"\n✓ TESTE 1 PASSOU")
