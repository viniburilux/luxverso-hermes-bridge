"""
TESTE 2 (SINTETICO) - Auto-resume + cycle 1.
"""
import sys
import os
sys.path.insert(0, os.environ.get('HERMES_HOME', '.'))
sys.path.insert(0, os.environ.get('TRACE_FOUNDRY_SRC', '../TraceFoundry/src'))
sys.path.insert(0, os.environ.get('HERMES_INTEGRATIONS', '../integrations'))

from lux_agent import (
    investigate, save_cycle, apply_action, add_evidence, add_claim, add_gap,
    discard_path, queue_next, set_decision, render_report,
)

OPORTUNIDADE = "exemplo de oportunidade generica para teste do agente"

print("="*70)
print("TESTE SINTETICO 2 - Auto-resume")
print("="*70)

c = investigate(OPORTUNIDADE, auto_resume=True)
print(f"\n[1] Auto-resume: cycle_n={c.cycle_n}")
print(f"  evid={len(c.evidence)} claims={len(c.claims)} gaps={len(c.gaps)}")
# Se nao ha estado (modo degradado / primeira execucao), criar
if c.cycle_n == 0 and len(c.evidence) == 0:
    print("  (modo degradado: criando ciclo 0 basico)")
    apply_action(c, 'acao adaptativa generica base')
    e_base = add_evidence(c, kind='web_url', source='example_source', uri='https://example.org/doc-base')
    add_claim(c, 'afirmacao base observada', 'observed', (e_base.evidence_id,))
    add_gap(c, 'gap material generico', 'material', ('REQUIRED_BASE',))

apply_action(c, 'acao adaptativa generica 3')

e_new = add_evidence(c, kind='web_url', source='example_source_3', uri='https://example.org/doc-3')
add_claim(c, 'nova afirmacao observada 3', 'observed', (e_new.evidence_id,))

gap_existente = c.gaps[0]
discard_path(c, f'gap {gap_existente.gap_id}', 'resolvido por evidencia')

add_gap(c, 'novo gap material generico', 'material', ('REQUIRED_NEW',))

set_decision(c, 'narrow')
queue_next(c, 'acao de cruzamento generico', reason='verificar viabilidade')

save_cycle(c)
print(f"\n[2] Cycle 1 salvo")
print(render_report(c))
print("OK")
