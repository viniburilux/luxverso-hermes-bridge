"""
lux_agent.investigate
=====================

Agente investigativo operacional da infraestrutura LuxVerso dentro do Hermes.

Reusa:
- TraceFoundry oi_discovery (InvestigationState, Claim, EvidenceReference, EvidenceGap, ResearchMove, assess_manifest, build_link)
- LuxMemory API (:8787) via luxmemory_client
- Capability Registry local
- 3 playbooks operacionais

NAO EXPOS:
- Nomes de heuristicas/metodologias adaptativas (preservadas em documentacao privada)
- Forma canonica do metodo (reuso como PROTOCOLO via skill, sem nomear)
- Dados de projetos reais (tests usam fixtures sinteticas)
- Conteudo de repositorios privados

Preserva os 5 itens da documentacao privada conforme Boundary V0:
1. scripts experimentais
2. politica geral de geracao de perguntas
3. priorizacao e ranking
4. heuristicas de reformulacao como metodo
5. politica adaptativa de memoria e parada
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Reuso 1: TraceFoundry como biblioteca
# Path via env var (sem hardcode de estrutura local)
_tracefoundry = os.environ.get('TRACE_FOUNDRY_SRC')
if _tracefoundry:
    sys.path.insert(0, _tracefoundry)
try:
    from oi_discovery.investigation import (
        InvestigationState, Claim, EvidenceReference, EvidenceGap, ResearchMove,
        EPISTEMIC_STATUSES, INVESTIGATION_STATUSES, MOVE_STATUSES,
    )
    from oi_discovery.evaluation import assess_manifest
    from oi_discovery.bridge import build_link, stable_hash
    _TRACEFOUNDRY_AVAILABLE = True
except ImportError:
    # Modo degradado: shims minimos (sem oi_discovery disponivel)
    _TRACEFOUNDRY_AVAILABLE = False
    from dataclasses import dataclass, field
    EPISTEMIC_STATUSES = ('observed', 'inferred', 'hypothesis', 'insufficient', 'blocked', 'rejected', 'contradicted')

    @dataclass(frozen=True)
    class Claim:
        claim_id: str
        statement: str
        status: str
        evidence_ids: tuple = ()
        gap_ids: tuple = ()
        note: str = None
        def to_dict(self): return self.__dict__

    @dataclass(frozen=True)
    class EvidenceReference:
        evidence_id: str
        kind: str
        source: str
        uri: str = None
        record_id: str = None
        observed_at: str = None
        metadata_only: bool = True
        provenance_note: str = None
        def to_dict(self): return self.__dict__

    @dataclass(frozen=True)
    class EvidenceGap:
        gap_id: str
        statement: str
        severity: str = 'material'
        required_evidence: tuple = ()
        status: str = 'open'
        def to_dict(self): return self.__dict__

    InvestigationState = None
    ResearchMove = None
    INVESTIGATION_STATUSES = ('open', 'in_review', 'resolved', 'closed')
    MOVE_STATUSES = ('proposed', 'accepted', 'completed', 'rejected', 'blocked')

    def stable_hash(v):
        import hashlib, json
        return 'sha256:' + hashlib.sha256(json.dumps(v, sort_keys=True, default=str).encode()).hexdigest()

    def assess_manifest(m):
        selected = m.get('selected_asset_ids', [])
        return {'conclusion': 'candidates_found' if selected else 'insufficient_evidence',
                'basis': 'eligible_candidates_present' if selected else 'no_eligible_candidates',
                'candidate_count': len(selected), 'rejected_count': 0, 'next_action': 'review'}

    def build_link(manifest, source_path, memory_type='result', capability_ids=None, gate_id=None):
        return {'link_id': f'link_{source_path}', 'source_type': 'oi_discovery_manifest', 'observations': []}

# Reuso 2: Cliente LuxMemory (opcional, modo degradado se indisponivel)
_luxmem_int = os.environ.get('HERMES_INTEGRATIONS')
if _luxmem_int:
    sys.path.insert(0, _luxmem_int)
try:
    from luxmemory_client import LuxMemoryClient
    _LUXMEMORY_AVAILABLE = True
except ImportError:
    _LUXMEMORY_AVAILABLE = False
    class LuxMemoryClient:
        def search(self, *a, **kw): return {'results': []}
        def answer(self, *a, **kw): return {'answer': 'luxmemory unavailable'}
        def capabilities(self, *a, **kw): return []

# Reuso 3: Capability Registry local
import yaml

AGENT_ROOT = Path(os.environ.get('LUX_AGENT_ROOT', '/home/vinicius/.hermes/lux_agent'))
STATE_DIR = AGENT_ROOT / 'state'
CYCLES_DIR = AGENT_ROOT / 'cycles'
ARTIFACTS_DIR = AGENT_ROOT / 'artifacts'
REGISTRY_PATH = Path(os.environ.get('LUX_REGISTRY_PATH', '/home/vinicius/.hermes/capabilities/registry.yaml'))
PLAYBOOKS_DIR = Path(os.environ.get('LUX_PLAYBOOKS_DIR', '/home/vinicius/.hermes/playbooks'))


# ============================================================================
# 1. Schema canônico: reuso do TraceFoundry
# ============================================================================

class InvestigationCycle:
    """
    Um ciclo de investigacao do agente.
    Reusa: InvestigationState (TraceFoundry), Claim, EvidenceReference.
    Estende: campos de evolucao do estado (sem expor nomes da metodologia privada).
    """

    def __init__(self, opportunity_id: str, question: str):
        self.opportunity_id = opportunity_id
        self.question = question
        self.cycle_n = 0
        self.created_at = datetime.now(timezone.utc).isoformat()
        # TraceFoundry
        self.evidence: list[EvidenceReference] = []
        self.claims: list[Claim] = []
        self.gaps: list[EvidenceGap] = []
        # Extensoes operacionais (campos genericos, sem nomes do metodo privado)
        self.facts_added: list[str] = []
        self.inferences: list[str] = []
        self.open_questions: list[dict] = []
        self.discarded_paths: list[dict] = []
        self.next_actions: list[dict] = []
        self.decision: Optional[str] = None  # continue | branch | narrow | park | stop | reformulate
        self.adaptive_actions: list[str] = []  # 1 linha por acao adaptativa (sem nome)

    def to_dict(self) -> dict:
        return {
            'opportunity_id': self.opportunity_id,
            'question': self.question,
            'cycle_n': self.cycle_n,
            'created_at': self.created_at,
            'updated_at': datetime.now(timezone.utc).isoformat(),
            'evidence': [e.to_dict() for e in self.evidence],
            'claims': [c.to_dict() for c in self.claims],
            'gaps': [g.to_dict() for g in self.gaps],
            'facts_added': self.facts_added,
            'inferences': self.inferences,
            'open_questions': self.open_questions,
            'discarded_paths': self.discarded_paths,
            'next_actions': self.next_actions,
            'decision': self.decision,
            'adaptive_actions_count': len(self.adaptive_actions),
        }


# ============================================================================
# 2. Persistencia
# ============================================================================

def _opportunity_dir(opportunity_id: str) -> Path:
    d = AGENT_ROOT / opportunity_id
    d.mkdir(exist_ok=True)
    (d / 'cycles').mkdir(exist_ok=True)
    (d / 'artifacts').mkdir(exist_ok=True)
    return d


def save_cycle(cycle: InvestigationCycle) -> Path:
    odir = _opportunity_dir(cycle.opportunity_id)
    p = odir / 'cycles' / f'cycle_{cycle.cycle_n:03d}.json'
    p.write_text(json.dumps(cycle.to_dict(), indent=2, ensure_ascii=False))
    return p


def load_state(opportunity_id: str) -> Optional[InvestigationCycle]:
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
    c.open_questions = latest.get('open_questions', [])
    c.discarded_paths = latest.get('discarded_paths', [])
    c.next_actions = latest.get('next_actions', [])
    c.decision = latest.get('decision')
    c.adaptive_actions = ['__' for _ in range(latest.get('adaptive_actions_count', 0))]
    for e in latest.get('evidence', []):
        c.evidence.append(EvidenceReference(**{k: e[k] for k in ['evidence_id', 'kind', 'source', 'uri', 'record_id', 'observed_at', 'metadata_only', 'provenance_note'] if k in e}))
    for cl in latest.get('claims', []):
        c.claims.append(Claim(**{k: cl[k] for k in ['claim_id', 'statement', 'status', 'evidence_ids', 'gap_ids', 'note'] if k in cl}))
    for g in latest.get('gaps', []):
        c.gaps.append(EvidenceGap(**{k: g[k] for k in ['gap_id', 'statement', 'severity', 'required_evidence', 'status'] if k in g}))
    return c


# ============================================================================
# 3. R1: Recuperar capacidades e experiencias
# ============================================================================

def _load_registry() -> dict:
    if not REGISTRY_PATH.exists():
        return {'capabilities': []}
    return yaml.safe_load(REGISTRY_PATH.read_text())


def find_capabilities(query: str, limit: int = 5) -> list[dict]:
    found = []
    reg = _load_registry()
    for cap in reg.get('capabilities', []):
        score = 0
        for field in ['name', 'description', 'problem_types', 'evidence_kind', 'tags']:
            val = str(cap.get(field, '')).lower()
            if query.lower() in val:
                score += 1
        if score > 0:
            found.append({'source': 'local_registry', 'score': score, 'capability': cap})
    try:
        client = LuxMemoryClient()
        result = client.search(query, mode='capabilities', limit=limit)
        items = result.get('results', result) if isinstance(result, dict) else result
        for r in (items or []):
            if isinstance(r, dict):
                name = r.get('name') or r.get('title') or r.get('id') or str(r)[:80]
                score = r.get('score', 1)
            else:
                name = str(r)[:80]
                score = 1
            found.append({'source': 'luxmemory', 'score': score, 'match_name': name, 'match': r})
    except Exception:
        pass
    found.sort(key=lambda x: -x['score'])
    return found[:limit]


def find_playbook(query: str) -> Optional[Path]:
    if not PLAYBOOKS_DIR.exists():
        return None
    q = query.lower()
    for p in PLAYBOOKS_DIR.glob('*.md'):
        content = p.read_text().lower()
        head = '\n'.join(content.split('\n')[:30])
        if any(word in head for word in q.split() if len(word) > 3):
            return p
    return None


# ============================================================================
# 4. Acoes adaptativas (PROTOCOLO generico, sem nomear metodo privado)
# ============================================================================

def apply_action(cycle: InvestigationCycle, action_description: str) -> None:
    """
    Aplica 1 acao adaptativa (registra).
    A descricao eh generica; o catalogo de 8 acoes canonicas NAO eh exposto aqui.
    Use find_capabilities() para descobrir heuristicas disponiveis.
    """
    cycle.adaptive_actions.append(action_description)


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
    cycle.discarded_paths.append({
        'path': path,
        'reason': reason,
        'discarded_at': datetime.now(timezone.utc).isoformat(),
    })


def queue_next(cycle: InvestigationCycle, action: str, reason: str, query_plan: str = '') -> None:
    cycle.next_actions.append({
        'action': action,
        'reason': reason,
        'query_plan': query_plan,
    })


def set_decision(cycle: InvestigationCycle, decision: str) -> None:
    valid = {'continue', 'branch', 'narrow', 'park', 'stop', 'reformulate', 'reframe'}
    if decision not in valid:
        raise ValueError(f"Decisao invalida: {decision}")
    cycle.decision = decision


# ============================================================================
# 6. Investigate: entry point
# ============================================================================

def investigate(opportunity: str, cycle_n: int = 1, auto_resume: bool = True) -> InvestigationCycle:
    opid = stable_hash(opportunity)[:16]
    if auto_resume:
        existing = load_state(opid)
        if existing:
            existing.cycle_n += 1
            return existing
    return InvestigationCycle(stable_hash(opportunity)[:16], opportunity)


# ============================================================================
# 7. Bridge para LuxMemory
# ============================================================================

def assess(cycle: InvestigationCycle) -> dict:
    manifest = {
        'dataset': {'source': 'lux_agent', 'name': cycle.opportunity_id},
        'decisions': [
            {'eligible': cl.status in ('observed', 'inferred'),
             'rejected_reasons': [] if cl.status in ('observed', 'inferred') else [cl.status]}
            for cl in cycle.claims
        ],
        'selected_asset_ids': [e.evidence_id for e in cycle.evidence if e.metadata_only],
        'warnings': [f"path_discarded: {p['path']}" for p in cycle.discarded_paths],
    }
    return assess_manifest(manifest)


def to_luxmemory_link(cycle: InvestigationCycle) -> dict:
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
# 8. Render do relatorio (sem expor nomes)
# ============================================================================

def render_report(cycle: InvestigationCycle) -> str:
    lines = [
        f"# Investigacao: {cycle.question}",
        f"",
        f"**Opportunity ID:** `{cycle.opportunity_id}`  ",
        f"**Cycle:** {cycle.cycle_n}  ",
        f"**Decision:** `{cycle.decision or 'pending'}`  ",
        f"**Created:** {cycle.created_at}  ",
        f"**Updated:** {datetime.now(timezone.utc).isoformat()}",
        f"",
        f"## Acoes adaptativas ({len(cycle.adaptive_actions)})",
    ]
    for a in cycle.adaptive_actions:
        lines.append(f"- {a}")
    if not cycle.adaptive_actions:
        lines.append("- (nenhuma)")
    lines.append(f"\n## Evidencias ({len(cycle.evidence)})")
    for e in cycle.evidence:
        lines.append(f"- `{e.evidence_id}` [{e.kind}] {e.source} - {e.uri or e.record_id or 'no-uri'}")
    if not cycle.evidence:
        lines.append("- (nenhuma)")
    lines.append(f"\n## Claims ({len(cycle.claims)})")
    for c in cycle.claims:
        evs = ', '.join(c.evidence_ids) if c.evidence_ids else '-'
        lines.append(f"- **{c.status}** `{c.claim_id}`: {c.statement} (evidencias: {evs})")
    if not cycle.claims:
        lines.append("- (nenhuma)")
    lines.append(f"\n## Gaps ({len(cycle.gaps)})")
    for g in cycle.gaps:
        lines.append(f"- **{g.severity}** `{g.gap_id}`: {g.statement}")
    if not cycle.gaps:
        lines.append("- (nenhuma)")
    if cycle.discarded_paths:
        lines.append(f"\n## Caminhos descartados ({len(cycle.discarded_paths)})")
        for p in cycle.discarded_paths:
            lines.append(f"- descartado: {p['path']}: {p['reason']}")
    if cycle.next_actions:
        lines.append(f"\n## Proximas acoes ({len(cycle.next_actions)})")
        for nq in cycle.next_actions:
            lines.append(f"- {nq['action']} (motivo: {nq['reason']})")
    if cycle.facts_added:
        lines.append(f"\n## Fatos adicionados ({len(cycle.facts_added)})")
        for f in cycle.facts_added:
            lines.append(f"- {f}")
    return '\n'.join(lines) + '\n'


# ============================================================================
# 9. CLI
# ============================================================================

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description='Lux Investigation Agent (operacional)')
    p.add_argument('opportunity', help='Descricao da oportunidade')
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
