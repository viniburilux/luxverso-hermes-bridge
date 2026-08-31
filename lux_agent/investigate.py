"""
lux_agent.investigate
=====================
Agente investigativo operacional LuxVerso (menor versao funcional).

Reusa:
- TraceFoundry oi_discovery (InvestigationState, Claim, EvidenceReference, EvidenceGap, ResearchMove, assess_manifest, build_link)
- LuxMemory API (:8787) via luxmemory_client
- Capability Registry local (capabilities/registry.yaml)
- 3 playbooks (investigate-new-domain, repository-archaeology, data-source-discovery)
- AOM documentado (8 operadores, 16 operacoes, P->R->S->P')

NÃO faz:
- Engine adaptativo geral (AOM é reusado, não recriado)
- Publicação sem autorização
- Substituição de decisão humana
- Download de dados científicos (metadata-only)
"""
from __future__ import annotations

import json
import os
import sys
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Reuso 1: TraceFoundry como biblioteca
sys.path.insert(0, '/home/vinicius/luxverso-archive/TraceFoundry/src')
from oi_discovery.investigation import (
    InvestigationState, Claim, EvidenceReference, EvidenceGap, ResearchMove,
    EPISTEMIC_STATUSES, INVESTIGATION_STATUSES, MOVE_STATUSES,
)
from oi_discovery.evaluation import assess_manifest
from oi_discovery.bridge import build_link, stable_hash

# Reuso 2: Cliente LuxMemory (Missão 1)
sys.path.insert(0, '/home/vinicius/.hermes/integrations')
from luxmemory_client import LuxMemoryClient

# Reuso 3: Capability Registry local
import yaml

AGENT_ROOT = Path('/home/vinicius/.hermes/lux_agent')
STATE_DIR = AGENT_ROOT / 'state'
CYCLES_DIR = AGENT_ROOT / 'cycles'
ARTIFACTS_DIR = AGENT_ROOT / 'artifacts'
REGISTRY_PATH = Path('/home/vinicius/.hermes/capabilities/registry.yaml')
PLAYBOOKS_DIR = Path('/home/vinicius/.hermes/playbooks')


# ============================================================================
# 1. Schema canônico: reuso parcial do TraceFoundry + extensão
# ============================================================================

class InvestigationCycle:
    """
    Um ciclo do AOM no Hermes.
    Reusa: InvestigationState (TraceFoundry), Claim, EvidenceReference
    Estende: state_update (campos do ASIE state_update_v*.json)
    """

    def __init__(self, opportunity_id: str, question: str):
        self.opportunity_id = opportunity_id
        self.question = question
        self.cycle_n = 0
        self.created_at = datetime.now(timezone.utc).isoformat()
        # Estado reusado do TraceFoundry
        self.evidence: list[EvidenceReference] = []
        self.claims: list[Claim] = []
        self.gaps: list[EvidenceGap] = []
        # Extensão AOM (campos do ASIE state_update_v*.json)
        self.facts_added: list[str] = []
        self.inferences: list[str] = []
        self.hypotheses_remaining: list[str] = []
        self.paths_discarded: list[dict] = []  # {'path': str, 'reason': str}
        self.next_questions: list[dict] = []  # {'q': str, 'reason': str, 'query_plan': str}
        self.decision: Optional[str] = None  # 'continue' | 'branch' | 'narrow' | 'park' | 'stop' | 'reformulate'
        self.representation_change: Optional[str] = None
        self.applied_operators: list[str] = []  # 8 operadores do AOM
        self.applied_operations: list[str] = []  # 16 operações do AOM

    def to_dict(self) -> dict:
        return {
            'opportunity_id': self.opportunity_id,
            'question': self.question,
            'cycle_n': self.cycle_n,
            'created_at': self.created_at,
            'updated_at': datetime.now(timezone.utc).isoformat(),
            # TraceFoundry
            'evidence': [e.to_dict() for e in self.evidence],
            'claims': [c.to_dict() for c in self.claims],
            'gaps': [g.to_dict() for g in self.gaps],
            # AOM extension
            'facts_added': self.facts_added,
            'inferences': self.inferences,
            'hypotheses_remaining': self.hypotheses_remaining,
            'paths_discarded': self.paths_discarded,
            'next_questions': self.next_questions,
            'decision': self.decision,
            'representation_change': self.representation_change,
            'applied_operators': self.applied_operators,
            'applied_operations': self.applied_operations,
        }


# ============================================================================
# 2. Persistência simples (não dependemos de LuxMemory DB)
# ============================================================================

def _opportunity_dir(opportunity_id: str) -> Path:
    """Cria diretorio por oportunidade."""
    d = AGENT_ROOT / opportunity_id
    d.mkdir(exist_ok=True)
    (d / 'cycles').mkdir(exist_ok=True)
    (d / 'artifacts').mkdir(exist_ok=True)
    return d


def save_cycle(cycle: InvestigationCycle) -> Path:
    """Persiste 1 ciclo como JSONL append-friendly."""
    odir = _opportunity_dir(cycle.opportunity_id)
    p = odir / 'cycles' / f'cycle_{cycle.cycle_n:03d}.json'
    p.write_text(json.dumps(cycle.to_dict(), indent=2, ensure_ascii=False))
    return p


def load_state(opportunity_id: str) -> Optional[InvestigationCycle]:
    """Recupera último estado de uma oportunidade."""
    odir = AGENT_ROOT / opportunity_id
    if not odir.exists():
        return None
    cycles = sorted(odir.glob('cycles/cycle_*.json'))
    if not cycles:
        return None
    latest = json.loads(cycles[-1].read_text())
    c = InvestigationCycle(latest['opportunity_id'], latest['question'])
    c.cycle_n = latest['cycle_n']
    c.facts_added = latest.get('facts_added', [])
    c.inferences = latest.get('inferences', [])
    c.hypotheses_remaining = latest.get('hypotheses_remaining', [])
    c.paths_discarded = latest.get('paths_discarded', [])
    c.next_questions = latest.get('next_questions', [])
    c.decision = latest.get('decision')
    c.representation_change = latest.get('representation_change')
    c.applied_operators = latest.get('applied_operators', [])
    c.applied_operations = latest.get('applied_operations', [])
    # Rehidratar EvidenceReference, Claim, EvidenceGap
    for e in latest.get('evidence', []):
        c.evidence.append(EvidenceReference(**{k: e[k] for k in ['evidence_id', 'kind', 'source', 'uri', 'record_id', 'observed_at', 'metadata_only', 'provenance_note'] if k in e}))
    for cl in latest.get('claims', []):
        c.claims.append(Claim(**{k: cl[k] for k in ['claim_id', 'statement', 'status', 'evidence_ids', 'gap_ids', 'note'] if k in cl}))
    for g in latest.get('gaps', []):
        c.gaps.append(EvidenceGap(**{k: g[k] for k in ['gap_id', 'statement', 'severity', 'required_evidence', 'status'] if k in g}))
    return c


# ============================================================================
# 3. R1: Recuperar capacidades e experiências
# ============================================================================

def _load_registry() -> dict:
    """Reuso: capability registry local."""
    if not REGISTRY_PATH.exists():
        return {'capabilities': []}
    return yaml.safe_load(REGISTRY_PATH.read_text())


def find_capabilities(query: str, limit: int = 5) -> list[dict]:
    """Busca capacidades locais (registry) + remotas (LuxMemory)."""
    found = []
    # Local
    reg = _load_registry()
    for cap in reg.get('capabilities', []):
        score = 0
        for field in ['name', 'description', 'problem_types', 'evidence_kind', 'tags']:
            val = str(cap.get(field, '')).lower()
            if query.lower() in val:
                score += 1
        if score > 0:
            found.append({'source': 'local_registry', 'score': score, 'capability': cap})
    # Remoto (LuxMemory)
    try:
        client = LuxMemoryClient()
        result = client.search(query, mode='capabilities', limit=limit)
        # LuxMemory pode retornar dict {'results': [...]} ou list
        items = result.get('results', result) if isinstance(result, dict) else result
        for r in (items or []):
            if isinstance(r, dict):
                # Extrair nome + score
                name = r.get('name') or r.get('title') or r.get('id') or str(r)[:80]
                score = r.get('score', 1)
            else:
                name = str(r)[:80]
                score = 1
            found.append({'source': 'luxmemory', 'score': score, 'match_name': name, 'match': r})
    except Exception as e:
        pass  # API LuxMemory indisponivel, sem problema
    # Ordena
    found.sort(key=lambda x: -x['score'])
    return found[:limit]


def find_playbook(query: str) -> Optional[Path]:
    """Match simples por keyword nos playbooks."""
    if not PLAYBOOKS_DIR.exists():
        return None
    q = query.lower()
    for p in PLAYBOOKS_DIR.glob('*.md'):
        content = p.read_text().lower()
        # Match se query aparece no titulo ou nas primeiras 30 linhas
        head = '\n'.join(content.split('\n')[:30])
        if any(word in head for word in q.split() if len(word) > 3):
            return p
    return None


# ============================================================================
# 4. Operadores AOM como protocolo (texto-only, decision=human-guided)
# ============================================================================

# Os 8 operadores adaptativos do AOM (ASIE_BEHAVIOR_V0.md)
AOM_OPERATORS = {
    'radiografar': 'transformar corpus em superficie de decisao (sinais, lacunas, clusters) antes de buscar',
    'reformular': 'substituir consulta morta por nova baseada em termos observados',
    'trocar_identificador': 'quando uma chave (DOI, BR, CMRP) aparece, navegar por ela',
    'ponte_inesperada': 'seguir trilha surpreendente sem colapsar entidades',
    'paralelizar': 'manter N trilhas independentes (branching)',
    'ausencia_como_sinal': 'tratar bloqueio/atraso/vazio como atualizacao de estado',
    'parar_sem_apagar': 'estacionar trilha, preservar artefatos, exigir nova ancora',
    'densidade': 'priorizar por ocorrencia/recorrencia observada',
}

# 16 operacoes taxonomicas (ASIE_QUESTION_TRANSFORMATION_GRAMMAR)
AOM_OPERATIONS = [
    'narrowing', 'expansion', 'reframing', 'branching',
    'language_change', 'identifier_pivot', 'anchor_substitution',
    'mechanism_change', 'contextualization', 'title_anchor',
    'source_switch', 'independent_contrast', 'portfolio_split',
    'entity_resolution', 'parking', 'state_freeze',
]


def apply_operator(cycle: InvestigationCycle, operator: str, **kwargs) -> None:
    """Aplica 1 operador adaptativo (registra, não executa)."""
    if operator not in AOM_OPERATORS:
        raise ValueError(f"Operador desconhecido: {operator}")
    cycle.applied_operators.append(operator)
    cycle.representation_change = AOM_OPERATORS[operator]


# ============================================================================
# 5. Helpers: registrar evidencia, claim, gap
# ============================================================================

def add_evidence(cycle: InvestigationCycle, kind: str, source: str, uri: Optional[str] = None,
                 record_id: Optional[str] = None, observed_at: Optional[str] = None,
                 note: Optional[str] = None) -> EvidenceReference:
    eid = f"ev_{cycle.opportunity_id}_c{cycle.cycle_n}_{len(cycle.evidence)+1:03d}"
    ref = EvidenceReference(
        evidence_id=eid,
        kind=kind,
        source=source,
        uri=uri,
        record_id=record_id,
        observed_at=observed_at or datetime.now(timezone.utc).isoformat(),
        metadata_only=True,
        provenance_note=note,
    )
    cycle.evidence.append(ref)
    return ref


def add_claim(cycle: InvestigationCycle, statement: str, status: str = 'inferred',
              evidence_ids: tuple = (), gap_ids: tuple = (), note: Optional[str] = None) -> Claim:
    if status not in EPISTEMIC_STATUSES:
        raise ValueError(f"Status invalido: {status}")
    cid = f"cl_{cycle.opportunity_id}_c{cycle.cycle_n}_{len(cycle.claims)+1:03d}"
    claim = Claim(
        claim_id=cid,
        statement=statement,
        status=status,
        evidence_ids=evidence_ids,
        gap_ids=gap_ids,
        note=note,
    )
    cycle.claims.append(claim)
    return claim


def add_gap(cycle: InvestigationCycle, statement: str, severity: str = 'material',
            required_evidence: tuple = ()) -> EvidenceGap:
    gid = f"gp_{cycle.opportunity_id}_c{cycle.cycle_n}_{len(cycle.gaps)+1:03d}"
    gap = EvidenceGap(
        gap_id=gid,
        statement=statement,
        severity=severity,
        required_evidence=required_evidence,
        status='open',
    )
    cycle.gaps.append(gap)
    return gap


def discard_path(cycle: InvestigationCycle, path: str, reason: str) -> None:
    """Registra caminho descartado (AOM: paths_discarded)."""
    cycle.paths_discarded.append({
        'path': path,
        'reason': reason,
        'discarded_at': datetime.now(timezone.utc).isoformat(),
    })


def queue_next(cycle: InvestigationCycle, question: str, reason: str, query_plan: str = '') -> None:
    """Registra proxima pergunta (AOM: next_questions)."""
    cycle.next_questions.append({
        'q': question,
        'reason': reason,
        'query_plan': query_plan,
    })


def set_decision(cycle: InvestigationCycle, decision: str) -> None:
    """Decisao do ciclo. Valores: continue | branch | narrow | park | stop | reformulate."""
    valid = {'continue', 'branch', 'narrow', 'park', 'stop', 'reformulate', 'reframe'}
    if decision not in valid:
        raise ValueError(f"Decisao invalida: {decision}")
    cycle.decision = decision


# ============================================================================
# 6. Investigate: entry point do agente (1 oportunidade)
# ============================================================================

def investigate(opportunity: str, cycle_n: int = 1, auto_resume: bool = True) -> InvestigationCycle:
    """
    Inicia ou continua investigacao de uma oportunidade.

    Args:
        opportunity: descricao da oportunidade/pergunta
        cycle_n: numero do ciclo (default 1)
        auto_resume: se True, tenta carregar estado anterior

    Returns:
        InvestigationCycle pronta para ser preenchida pelo Hermes

    Usage pelo Hermes:
        from lux_agent import investigate
        c = investigate("tem um edital do CGU sobre Cross-Data?")
        # Hermes faz R1 (busca), preenche evidence/claims, salva
        # Proximo turno: investigate("...mesma pergunta...", cycle_n=2) -> carrega estado anterior
    """
    opid = stable_hash(opportunity)[:16]
    if auto_resume:
        existing = load_state(opid)
        if existing:
            existing.cycle_n += 1
            return existing
    return InvestigationCycle(op_id(opportunity), opportunity)


def op_id(opportunity: str) -> str:
    """Gera ID estavel para a oportunidade."""
    return stable_hash(opportunity)[:16]


# ============================================================================
# 7. Subagente (arquéologo) — reuso do delegate_task do Hermes
# ============================================================================

SUBAGENT_PROMPT_TEMPLATE = """Voce e um subagente arqueologo do Hermes. Sua missao e investigar {target} que esta em {path}.

Use terminal extensivamente. Foque em:
- estrutura de diretorios
- schemas JSON
- documentacao
- primeiras 50 linhas de cada arquivo .py principal
- contagem de itens

Reporte SOMENTE com EVidencias de arquivos. Nao invente.
Use {tokens_hint} tokens para saida.
Retorne JSON estruturado com chaves relevantes ao escopo.
"""


# ============================================================================
# 8. Bridge para LuxMemory (assessment + link)
# ============================================================================

def assess(cycle: InvestigationCycle) -> dict:
    """Aplica assess_manifest (TraceFoundry) sobre o estado atual."""
    manifest = {
        'dataset': {'source': 'lux_agent', 'name': cycle.opportunity_id},
        'decisions': [
            {'eligible': cl.status in ('observed', 'inferred'),
             'rejected_reasons': [] if cl.status in ('observed', 'inferred') else [cl.status]}
            for cl in cycle.claims
        ],
        'selected_asset_ids': [e.evidence_id for e in cycle.evidence if e.metadata_only],
        'warnings': [f"path_discarded: {p['path']}" for p in cycle.paths_discarded],
    }
    return assess_manifest(manifest)


def to_luxmemory_link(cycle: InvestigationCycle) -> dict:
    """Constroi link Hermes->LuxMemory usando build_link do TraceFoundry."""
    manifest = {
        'query': {'source': 'lux_agent', 'dataset_id': cycle.opportunity_id, 'version': 'v1', 'formats': ['md', 'jsonl']},
        'dataset': {
            'source': 'lux_agent',
            'dataset_id': cycle.opportunity_id,
            'version': 'v1',
            'name': cycle.question[:200],
            'asset_count': len(cycle.evidence),
            'assets': [
                {'asset_id': e.evidence_id, 'path': e.uri or e.source, 'size_bytes': None, 'format': e.kind}
                for e in cycle.evidence
            ],
        },
        'selected_asset_ids': [e.evidence_id for e in cycle.evidence],
        'download_performed': False,
    }
    return build_link(manifest, source_path=f"lux_agent/{cycle.opportunity_id}", memory_type='investigation_cycle')


# ============================================================================
# 9. Render do relatorio
# ============================================================================

def render_report(cycle: InvestigationCycle) -> str:
    """Gera relatorio Markdown do ciclo."""
    lines = [
        f"# Investigação: {cycle.question}",
        f"",
        f"**Opportunity ID:** `{cycle.opportunity_id}`  ",
        f"**Cycle:** {cycle.cycle_n}  ",
        f"**Decision:** `{cycle.decision or 'pending'}`  ",
        f"**Created:** {cycle.created_at}  ",
        f"**Updated:** {datetime.now(timezone.utc).isoformat()}",
        f"",
        f"## Operadores aplicados ({len(cycle.applied_operators)})",
    ]
    for op in cycle.applied_operators:
        lines.append(f"- {op}: {AOM_OPERATORS.get(op, '?')}")
    if not cycle.applied_operators:
        lines.append("- (nenhum)")
    lines.append(f"\n## Evidências ({len(cycle.evidence)})")
    for e in cycle.evidence:
        lines.append(f"- `{e.evidence_id}` [{e.kind}] {e.source} — {e.uri or e.record_id or 'no-uri'}")
    if not cycle.evidence:
        lines.append("- (nenhuma)")
    lines.append(f"\n## Claims ({len(cycle.claims)})")
    for c in cycle.claims:
        evs = ', '.join(c.evidence_ids) if c.evidence_ids else '—'
        lines.append(f"- **{c.status}** `{c.claim_id}`: {c.statement} (evidências: {evs})")
    if not cycle.claims:
        lines.append("- (nenhuma)")
    lines.append(f"\n## Gaps ({len(cycle.gaps)})")
    for g in cycle.gaps:
        lines.append(f"- **{g.severity}** `{g.gap_id}`: {g.statement}")
    if not cycle.gaps:
        lines.append("- (nenhuma)")
    if cycle.paths_discarded:
        lines.append(f"\n## Caminhos descartados ({len(cycle.paths_discarded)})")
        for p in cycle.paths_discarded:
            lines.append(f"- ❌ {p['path']}: {p['reason']}")
    if cycle.next_questions:
        lines.append(f"\n## Próximas perguntas ({len(cycle.next_questions)})")
        for nq in cycle.next_questions:
            lines.append(f"- ❓ {nq['q']} (motivo: {nq['reason']})")
    if cycle.representation_change:
        lines.append(f"\n## Mudança de representação")
        lines.append(f"> {cycle.representation_change}")
    if cycle.facts_added:
        lines.append(f"\n## Fatos adicionados ({len(cycle.facts_added)})")
        for f in cycle.facts_added:
            lines.append(f"- ✅ {f}")
    return '\n'.join(lines) + '\n'


# ============================================================================
# 10. CLI
# ============================================================================

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description='Lux Investigation Agent (operacional)')
    p.add_argument('opportunity', help='Descrição da oportunidade')
    p.add_argument('--cycle', type=int, default=1)
    p.add_argument('--resume', action='store_true', help='Carregar estado anterior')
    p.add_argument('--render', action='store_true', help='Renderizar relatorio')
    args = p.parse_args()

    c = investigate(args.opportunity, cycle_n=args.cycle, auto_resume=args.resume)
    print(f"# InvestigationCycle criada")
    print(f"  opportunity_id: {c.opportunity_id}")
    print(f"  cycle_n: {c.cycle_n}")
    print(f"  question: {c.question[:100]}")
    if args.render:
        print()
        print(render_report(c))
