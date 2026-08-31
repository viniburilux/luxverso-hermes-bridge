import argparse
import os
import json
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(os.environ.get('LUXMEMORY_ROOT=os.environ.get('LUXMEMORY_ROOT', '/app/data/memory')/app/luxverso-archive/LuxMemory'))
MEMORY_PATH = ROOT / 'data' / 'memory.jsonl'
SKILLS_PATH = ROOT / 'data' / 'skills.json'
CAPABILITIES_PATH = ROOT / 'data' / 'capabilities.jsonl'
DIM = 384


def normalize(text):
    text = unicodedata.normalize('NFKD', str(text or '')).encode('ascii', 'ignore').decode('ascii').lower()
    return re.findall(r'[a-z0-9_]{3,}', text)


def flatten(record):
    fields = {
        'project': record.get('project', ''),
        'problem': record.get('problem_objective', ''),
        'process': ' '.join(record.get('approach_process', [])),
        'discoveries': ' '.join(record.get('discoveries', [])),
        'decisions': ' '.join(record.get('decisions', [])),
        'results': ' '.join(record.get('results', [])),
        'artifacts': ' '.join(record.get('artifacts', [])),
        'tools': ' '.join(record.get('technology_tools', [])),
        'data': ' '.join(record.get('data_used', [])),
        'reuse': ' '.join(record.get('reuses', [])),
        'evidence': ' '.join(e.get('label', '') + ' ' + e.get('basis', '') for e in record.get('evidence', [])),
    }
    return fields


def flatten_capability(capability):
    gate = capability.get('validation_gate', {})
    return {
        'name': capability.get('name', ''),
        'statement': capability.get('statement', ''),
        'transfer_rationale': capability.get('transfer_rationale', ''),
        'domains': ' '.join(capability.get('domains_of_origin', []) + capability.get('domains_of_transfer', [])),
        'assets': ' '.join(capability.get('supporting_assets', [])),
        'gate': ' '.join(str(gate.get(k, '')) for k in ('question', 'minimum_experiment', 'success_signal', 'failure_signal')),
        'decision': capability.get('decision', ''),
        'status': capability.get('status', ''),
    }


def hashed_vector(tokens):
    vec = [0.0] * DIM
    for token in tokens:
        h = 2166136261
        for ch in token.encode('utf-8'):
            h ^= ch
            h = (h * 16777619) & 0xffffffff
        idx = h % DIM
        sign = 1.0 if ((h >> 16) & 1) else -1.0
        vec[idx] += sign
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def cosine(a, b):
    return sum(x * y for x, y in zip(a, b))


def overlap(query_tokens, text):
    tokens = set(normalize(text))
    if not query_tokens:
        return 0.0
    return len(set(query_tokens).intersection(tokens)) / math.sqrt(len(set(query_tokens)) * max(1, len(tokens)))


def load_index():
    records = [json.loads(line) for line in MEMORY_PATH.read_text(encoding='utf-8').splitlines() if line.strip()]
    skills = json.loads(SKILLS_PATH.read_text(encoding='utf-8'))
    for record in records:
        record['_fields'] = flatten(record)
        weighted = []
        weighted.extend(normalize(record['_fields']['project']) * 4)
        weighted.extend(normalize(record['_fields']['problem']) * 3)
        weighted.extend(normalize(record['_fields']['process']) * 2)
        weighted.extend(normalize(record['_fields']['reuse']) * 2)
        weighted.extend(normalize(record['_fields']['discoveries']))
        weighted.extend(normalize(record['_fields']['results']))
        weighted.extend(normalize(record['_fields']['artifacts']))
        record['_vector'] = hashed_vector(weighted)
    return records, skills


def load_capabilities():
    if not CAPABILITIES_PATH.exists():
        return []
    capabilities = [json.loads(line) for line in CAPABILITIES_PATH.read_text(encoding='utf-8').splitlines() if line.strip()]
    for capability in capabilities:
        capability['_fields'] = flatten_capability(capability)
        weighted = []
        weighted.extend(normalize(capability['_fields']['name']) * 4)
        weighted.extend(normalize(capability['_fields']['statement']) * 3)
        weighted.extend(normalize(capability['_fields']['transfer_rationale']) * 2)
        weighted.extend(normalize(capability['_fields']['domains']) * 2)
        weighted.extend(normalize(capability['_fields']['assets']))
        weighted.extend(normalize(capability['_fields']['gate']))
        capability['_vector'] = hashed_vector(weighted)
    return capabilities


def public_capability(capability, score=None, embedding_score=None, structured_score=None):
    gate = capability.get('validation_gate', {})
    output = {
        'capability_id': capability.get('capability_id'),
        'capability_type': capability.get('capability_type'),
        'name': capability.get('name'),
        'statement': capability.get('statement'),
        'confidence': capability.get('confidence'),
        'evidence_level': capability.get('evidence_level'),
        'status': capability.get('status'),
        'decision': capability.get('decision'),
        'supporting_assets': capability.get('supporting_assets', []),
        'domains_of_origin': capability.get('domains_of_origin', []),
        'domains_of_transfer': capability.get('domains_of_transfer', []),
        'transfer_rationale': capability.get('transfer_rationale', ''),
        'validation_gate': gate,
        'relations': capability.get('relations', []),
    }
    if score is not None:
        output['score'] = round(float(score), 6)
    if embedding_score is not None:
        output['embedding_score'] = round(float(embedding_score), 6)
    if structured_score is not None:
        output['structured_score'] = round(float(structured_score), 6)
    return output


def relation_neighbors(asset_id, records):
    neighbors = set()
    for record in records:
        for rel in record.get('relations', []):
            target = rel.get('target_asset_id')
            if record['asset_id'] == asset_id:
                neighbors.add(target)
            if target == asset_id:
                neighbors.add(record['asset_id'])
    return neighbors


def search(query, mode='structured', limit=8):
    records, _ = load_index()
    qtokens = normalize(query)
    qvec = hashed_vector(qtokens)
    results = []
    for record in records:
        fields = record['_fields']
        embedding_score = max(0.0, cosine(qvec, record['_vector']))
        field_score = (
            0.25 * overlap(qtokens, fields['project']) +
            0.20 * overlap(qtokens, fields['problem']) +
            0.18 * overlap(qtokens, fields['process']) +
            0.16 * overlap(qtokens, fields['reuse']) +
            0.10 * overlap(qtokens, fields['discoveries']) +
            0.06 * overlap(qtokens, fields['results']) +
            0.05 * overlap(qtokens, fields['evidence'])
        )
        exact_name = 0.15 if all(t in normalize(fields['project']) for t in qtokens[:2]) and qtokens[:2] else 0.0
        evidence_score = overlap(qtokens, fields['evidence'])
        if mode == 'embedding':
            score = embedding_score
        else:
            score = 0.42 * embedding_score + 0.43 * field_score + 0.15 * evidence_score + exact_name
            if any(n in qtokens for n in ['relacionado', 'relacao', 'projetos', 'projeto']):
                score += 0.03 * min(3, len(relation_neighbors(record['asset_id'], records)))
        results.append({
            'asset_id': record['asset_id'],
            'project': record['project'],
            'score': round(float(score), 6),
            'embedding_score': round(float(embedding_score), 6),
            'structured_score': round(float(field_score), 6),
            'evidence_score': round(float(evidence_score), 6),
            'problem_objective': record['problem_objective'],
            'current_state': record['current_state'],
            'reuses': record['reuses'][:4],
            'evidence': record['evidence'][:3],
            'relations': record['relations'][:8],
        })
    results.sort(key=lambda r: (-r['score'], r['project'].lower()))
    return results[:limit]


def search_capabilities(query, mode='structured', limit=8, capability_type=None):
    capabilities = load_capabilities()
    qtokens = normalize(query)
    qvec = hashed_vector(qtokens)
    results = []
    for capability in capabilities:
        if capability_type and capability.get('capability_type') != capability_type:
            continue
        fields = capability['_fields']
        embedding_score = max(0.0, cosine(qvec, capability['_vector']))
        structured_score = (
            0.34 * overlap(qtokens, fields['name']) +
            0.28 * overlap(qtokens, fields['statement']) +
            0.16 * overlap(qtokens, fields['transfer_rationale']) +
            0.10 * overlap(qtokens, fields['domains']) +
            0.07 * overlap(qtokens, fields['assets']) +
            0.05 * overlap(qtokens, fields['gate'])
        )
        exact_name = 0.14 if qtokens and all(t in normalize(fields['name']) for t in qtokens[:2]) else 0.0
        if mode == 'embedding':
            score = embedding_score
        else:
            score = 0.48 * embedding_score + 0.42 * structured_score + exact_name
        results.append(public_capability(capability, score, embedding_score, structured_score))
    results.sort(key=lambda r: (-r['score'], r['name'].lower()))
    return results[:limit]


def capability_summary():
    capabilities = load_capabilities()
    counts = Counter(c.get('capability_type') for c in capabilities)
    decisions = Counter(c.get('decision') for c in capabilities if c.get('decision'))
    return {
        'records': len(capabilities),
        'by_type': dict(counts),
        'by_decision': dict(decisions),
        'opportunities': [public_capability(c) for c in capabilities if c.get('capability_type') == 'opportunity'],
        'validations': [public_capability(c) for c in capabilities if c.get('capability_type') == 'validation'],
    }


def matching_skills(query, skills, limit=5):
    q = set(normalize(query))
    scored = []
    for skill in skills:
        text = ' '.join([skill['name'], skill['when_to_use'], *skill['process'], *skill['outputs']])
        hit = len(q.intersection(set(normalize(text))))
        scored.append((hit, skill))
    scored.sort(key=lambda x: (-x[0], x[1]['name']))
    return [s for score, s in scored[:limit] if score > 0] or [s for _, s in scored[:2]]


def grounded_answer(query, limit=6):
    records, skills = load_index()
    structured = search(query, 'structured', limit)
    capabilities = search_capabilities(query, 'structured', limit)
    matched = matching_skills(query, skills)
    lines = [f'Pergunta: {query}', '', 'Resposta fundamentada no acervo:']
    if not structured:
        lines.append('Não encontrei um candidato suficiente no índice inicial.')
    else:
        lines.append(f'Encontrei {len(structured)} candidatos. Os mais relevantes são:')
        for item in structured[:5]:
            lines.append(f"- [{item['asset_id']}] {item['project']}: {item['problem_objective']}")
            for ev in item['evidence']:
                lines.append(f"  Evidência: {ev['label']} — {ev['uri']}")
    lines += ['', 'Capacidades, combinações e gates relacionados:']
    for item in capabilities[:5]:
        gate = item.get('validation_gate', {})
        lines.append(f"- [{item['capability_id']}] {item['name']} ({item['capability_type']}): {item['statement']}")
        lines.append(f"  Estado: {item.get('status') or 'não especificado'}; decisão: {item.get('decision') or 'não especificada'}; gate: {gate.get('question', 'não especificado')}")
    lines += ['', 'Habilidades potencialmente relacionadas:']
    for skill in matched:
        lines.append(f"- {skill['skill_id']} — {skill['name']} (exemplos: {', '.join(x['project'] for x in skill['historical_examples'][:4])})")
    lines += ['', 'Limite: esta resposta usa recuperação lexical/hash-embedding sobre a memória estruturada e a camada derivada de capacidades; não afirma fatos que não estejam registrados em evidências.']
    return {'query': query, 'mode': 'structured_plus_evidence_and_capabilities', 'answer': '\n'.join(lines), 'results': structured, 'capabilities': capabilities, 'skills': matched}


def compare(query, limit=8):
    return {
        'query': query,
        'embedding_puro': search(query, 'embedding', limit),
        'memoria_estruturada_embedding_evidencia': search(query, 'structured', limit),
        'capacidades_estruturadas': search_capabilities(query, 'structured', limit),
        'note': 'O modo embedding usa hash embedding determinístico local, sem modelo pré-treinado. Ele é um baseline de recall, não uma representação semântica forte.'
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('query', nargs='*')
    parser.add_argument('--mode', choices=['structured', 'embedding', 'answer', 'compare', 'capabilities'], default='answer')
    parser.add_argument('--limit', type=int, default=8)
    args = parser.parse_args()
    query = ' '.join(args.query).strip()
    if not query:
        parser.error('informe uma pergunta ou consulta')
    if args.mode == 'answer':
        output = grounded_answer(query, args.limit)
    elif args.mode == 'compare':
        output = compare(query, args.limit)
    elif args.mode == 'capabilities':
        output = {'query': query, 'mode': args.mode, 'results': search_capabilities(query, 'structured', args.limit)}
    else:
        output = {'query': query, 'mode': args.mode, 'results': search(query, args.mode, args.limit)}
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
