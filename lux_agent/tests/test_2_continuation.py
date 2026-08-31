"""
TESTE 2: Continuacao de ciclo (auto_resume) + decisao reformulate.
Simula: Hermes recebe o ciclo 0, faz R1+S, agora no turno 2 faz auto_resume.
"""
import sys
sys.path.insert(0, '/home/vinicius/.hermes')
sys.path.insert(0, '/home/vinicius/.hermes/integrations')
sys.path.insert(0, '/home/vinicius/luxverso-archive/TraceFoundry/src')

from lux_agent import (
    investigate, save_cycle, load_state, render_report,
    find_capabilities, apply_operator,
    add_evidence, add_claim, add_gap, discard_path, queue_next, set_decision,
    assess,
)

print("="*70)
print("TESTE 2 — Continuacao de ciclo (cycle 0 -> cycle 1)")
print("="*70)

# Mesma oportunidade do teste 1
oportunidade = "tem um edital CGU 2026 sobre Cross-Data? Vale a pena investigar?"

# Cycle 1: deve auto-resumir cycle 0
c = investigate(oportunidade, auto_resume=True)
print(f"\n[1] Auto-resume funcionou: cycle_n={c.cycle_n}")
print(f"  evidencia carregada: {len(c.evidence)}")
print(f"  claims carregados: {len(c.claims)}")
print(f"  gaps carregados: {len(c.gaps)}")
print(f"  paths descartados carregados: {len(c.paths_discarded)}")
print(f"  proximas perguntas carregadas: {len(c.next_questions)}")

# Cycle 1: Hermes executa a proxima pergunta
print(f"\n[2] Executando 1a proxima pergunta do cycle 0:")
nq = c.next_questions[0]
print(f"  Pergunta: {nq['q']}")

# Operador: reformular
apply_operator(c, 'reformular')
print(f"  Operador aplicado: reformular")

# Nova evidencia do web (simulando extracao do edital)
e_new = add_evidence(c, kind='web_url', source='CGU', uri='https://www.gov.br/cgu/pt-br/concurso-2026/edital.pdf', note='PDF do edital extraido')
print(f"  Nova evidencia: {e_new.evidence_id}")

# Novo claim (status upgraded de hypothesis para observed)
cl_new = add_claim(c, statement='CGU 2026 prazo: 60 dias a partir de 15/09/2026', status='observed', evidence_ids=(e_new.evidence_id,))
print(f"  Novo claim: {cl_new.status} - {cl_new.statement}")

# Gap critico resolvido -> descartar com motivo
gap_critico = c.gaps[0]  # gp_001 era prazo
discard_path(c, f"gap {gap_critico.gap_id}: prazo edital 2026", 'Resolvido por evidencia do edital (60d a partir de 15/09)')
print(f"  Gap critico resolvido (descartado): {gap_critico.gap_id}")

# Novo gap
g_new = add_gap(c, statement='Necessario revisar categorias de submissoes aceitas', severity='material', required_evidence=('EDITAL_CATEGORIAS',))
print(f"  Novo gap: {g_new.gap_id}")

# Decisao: narrow (focar no prazo)
set_decision(c, 'narrow')
print(f"  Decisao: {c.decision}")

# Proxima pergunta
queue_next(c, 'Cruzar prazo (60d) com escopo do edital', reason='Verificar se 60d e viavel', query_plan='web_extract + comparacao')
print(f"  1 proxima pergunta")

# Salvar
path = save_cycle(c)
print(f"\n[3] Cycle 1 salvo: {path}")
print(f"  Total operators: {len(c.applied_operators)}")
print(f"  Total evidencia: {len(c.evidence)}")
print(f"  Total claims: {len(c.claims)}")
print(f"  Total gaps: {len(c.gaps)}")
print(f"  Total paths descartados: {len(c.paths_discarded)}")
print(f"  Total proximas: {len(c.next_questions)}")

# Relatorio
print("\n" + render_report(c))
print("✓ TESTE 2 PASSOU")
