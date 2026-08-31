"""
TESTE 3 (SINTETICO) - Subagente (delegate_task) arqueologo.
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

print("="*70)
print("TESTE SINTETICO 3 - Subagente arqueologo")
print("="*70)

c = investigate("exemplo: investigue repo generico para reuso")
print(f"\n[1] Ciclo criado: opid={c.opportunity_id}")

# Simula retorno de subagente (sem referenciar repo real)
subagente = {
    "structure": "5 diretorios, 20 arquivos Python, 7 schemas JSON",
    "has_tests": True,
    "public": True,
    "integration_effort_hours": 4,
    "limitations": ["limitacao generica 1", "limitacao generica 2"],
}

e_sub = add_evidence(c, kind='subagent_report', source='delegate_task[arqueologo]', record_id='repo-generico-v1', note='subagente sintetico')
add_claim(c, 'repo generico tem 20 .py + 7 schemas', 'observed', (e_sub.evidence_id,))
add_claim(c, 'cobertura ~70%, integracao ~4h', 'inferred', (e_sub.evidence_id,))
add_claim(c, 'limitacoes: [limitacao 1, limitacao 2]', 'observed', (e_sub.evidence_id,))

apply_action(c, 'acao generica 1')
apply_action(c, 'acao generica 2')
apply_action(c, 'acao generica 3')

add_gap(c, 'schema v0.1 estavel?', 'critical', ('CHANGELOG',))
add_gap(c, 'rate limit especifico', 'material')

discard_path(c, 'forkar o repo', 'reusar como dependencia preserva origem')

set_decision(c, 'continue')
queue_next(c, 'verificar changelog', reason='resolver gap critico')
queue_next(c, 'teste de integracao em sandbox', reason='validar esforco')

save_cycle(c)
print(f"[2] Cycle salvo")
print(render_report(c))
print("OK")
