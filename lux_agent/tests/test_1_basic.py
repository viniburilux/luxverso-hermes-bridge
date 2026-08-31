"""
TESTE 1 (SINTETICO) - InvestigationCycle basica.
Nenhuma referencia a projetos reais. Fixtures genericas.
"""
import sys
# Usar variavel de ambiente para raiz (sem hardcode)
import os
sys.path.insert(0, os.environ.get('HERMES_HOME', '.'))
# TraceFoundry e LuxMemory sao dependencias, nao vao no repo publico
sys.path.insert(0, os.environ.get('TRACE_FOUNDRY_SRC', '../TraceFoundry/src'))
sys.path.insert(0, os.environ.get('HERMES_INTEGRATIONS', '../integrations'))

from lux_agent import (
    investigate, save_cycle, find_capabilities, find_playbook,
    apply_action, add_evidence, add_claim, add_gap,
    discard_path, queue_next, set_decision, assess, to_luxmemory_link,
    render_report,
)

print("="*70)
print("TESTE SINTETICO 1 - Investigacao basica")
print("="*70)

# Fixture generica
oportunidade = "exemplo de oportunidade generica para teste do agente"
c = investigate(oportunidade)
print(f"\n[1] Ciclo criado: opid={c.opportunity_id}, cycle_n={c.cycle_n}")

# 3 evidencias genericas
e1 = add_evidence(c, kind='web_url', source='example_source_1', uri='https://example.org/doc-1', note='evidencia generica 1')
e2 = add_evidence(c, kind='local_doc', source='local_doc', uri='/example/path/file.md', note='documento generico')
e3 = add_evidence(c, kind='web_url', source='example_source_2', uri='https://example.org/doc-2', note='evidencia generica 2')

# 4 claims genericos (3 status diferentes)
add_claim(c, 'afirmacao observada 1', 'observed', (e1.evidence_id,))
add_claim(c, 'afirmacao observada 2', 'observed', (e2.evidence_id, e3.evidence_id))
add_claim(c, 'afirmacao inferida', 'inferred', (e2.evidence_id, e3.evidence_id))
add_claim(c, 'afirmacao hipotetica', 'hypothesis', gap_ids=('gp_test_1',))

# 3 gaps
add_gap(c, 'gap critico generico', 'critical', ('REQUIRED_EVIDENCE_A',))
add_gap(c, 'gap material generico', 'material', ('REQUIRED_EVIDENCE_B',))
add_gap(c, 'gap menor generico', 'minor')

# Acoes adaptativas (descricoes genericas)
apply_action(c, 'acao adaptativa generica 1')
apply_action(c, 'acao adaptativa generica 2')

# 3 paths descartados
discard_path(c, 'caminho descartado 1', 'motivo generico')
discard_path(c, 'caminho descartado 2', 'motivo generico')
discard_path(c, 'caminho descartado 3', 'motivo generico')

# Decisao + proximas
set_decision(c, 'continue')
queue_next(c, 'acao seguinte 1', reason='motivo generico', query_plan='plano generico')
queue_next(c, 'acao seguinte 2', reason='motivo generico', query_plan='plano generico')

# Assess + bridge
ass = assess(c)
link = to_luxmemory_link(c)

# Salvar
path = save_cycle(c)
print(f"[2] Ciclo salvo: {path}")
print(f"[3] assess: {ass['conclusion']}")
print(f"[4] link_id: {link.get('link_id')}")
print(f"\n{render_report(c)}")
print("OK")
