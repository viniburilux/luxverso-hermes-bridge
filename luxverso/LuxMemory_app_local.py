from flask import Flask, jsonify, render_template, request
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, '/app/.hermes/integrations')
from retrieve_patched import (  # noqa: E402
    capability_summary,
    compare,
    grounded_answer,
    load_capabilities,
    load_index,
    search,
    search_capabilities,
)
from consult_resume import consult_resume  # noqa: E402

app = Flask(__name__, template_folder=str(ROOT / 'templates'), static_folder=str(ROOT / 'static'))


def records_by_id():
    records, _ = load_index()
    return {r['asset_id']: r for r in records}


def capabilities_by_id():
    return {c['capability_id']: c for c in load_capabilities()}


def bounded_limit():
    try:
        return min(max(int(request.args.get('limit', 8)), 1), 30)
    except ValueError:
        return 8


@app.route('/')
def index():
    records, skills = load_index()
    cap_summary = capability_summary()
    counts = {
        'assets': len(records),
        'skills': len(skills),
        'relations': sum(len(r.get('relations', [])) for r in records),
        'evidence': sum(len(r.get('evidence', [])) for r in records),
        'capabilities': cap_summary['records'],
        'transferable': cap_summary['by_type'].get('transferable_capability', 0),
    }
    return render_template('index.html', counts=counts)


@app.route('/api/search')
def api_search():
    query = request.args.get('q', '').strip()
    mode = request.args.get('mode', 'answer')
    limit = bounded_limit()
    if not query:
        return jsonify({'error': 'Informe uma pergunta ou consulta.'}), 400
    if mode == 'answer':
        return jsonify(grounded_answer(query, limit))
    if mode == 'compare':
        return jsonify(compare(query, limit))
    if mode == 'capabilities':
        return jsonify({'query': query, 'mode': mode, 'results': search_capabilities(query, 'structured', limit)})
    if mode not in ('structured', 'embedding'):
        mode = 'structured'
    return jsonify({'query': query, 'mode': mode, 'results': search(query, mode, limit)})


@app.route('/api/resume')
def api_resume():
    query = request.args.get('q', '').strip()
    objective = request.args.get('objective', '').strip() or None
    limit = bounded_limit()
    if not query:
        return jsonify({'error': 'Informe o projeto ou pergunta para retomada.'}), 400
    return jsonify(consult_resume(query, objective, limit))


@app.route('/api/skills')
def api_skills():
    _, skills = load_index()
    return jsonify({'skills': skills})


@app.route('/api/capabilities')
def api_capabilities():
    query = request.args.get('q', '').strip()
    capability_type = request.args.get('type', '').strip() or None
    limit = bounded_limit()
    if query:
        results = search_capabilities(query, 'structured', limit, capability_type)
    else:
        results = [
            c for c in capability_summary()['opportunities']
        ] if capability_type == 'opportunity' else [
            {
                'capability_id': c.get('capability_id'),
                'capability_type': c.get('capability_type'),
                'name': c.get('name'),
                'statement': c.get('statement'),
                'confidence': c.get('confidence'),
                'evidence_level': c.get('evidence_level'),
                'status': c.get('status'),
                'decision': c.get('decision'),
                'supporting_assets': c.get('supporting_assets', []),
                'domains_of_origin': c.get('domains_of_origin', []),
                'domains_of_transfer': c.get('domains_of_transfer', []),
                'transfer_rationale': c.get('transfer_rationale', ''),
                'validation_gate': c.get('validation_gate', {}),
                'relations': c.get('relations', []),
            }
            for c in load_capabilities()
            if not capability_type or c.get('capability_type') == capability_type
        ][:limit]
    return jsonify({'capabilities': results, 'summary': capability_summary()})


@app.route('/api/capabilities/<capability_id>')
def api_capability(capability_id):
    capability = capabilities_by_id().get(capability_id)
    if not capability:
        return jsonify({'error': 'Capacidade não encontrada.'}), 404
    return jsonify(capability)


@app.route('/api/assets')
def api_assets():
    records, _ = load_index()
    q = request.args.get('q', '').strip().lower()
    if q:
        records = [r for r in records if q in r.get('project', '').lower() or q in r.get('problem_objective', '').lower()]
    return jsonify({'assets': records})


@app.route('/api/assets/<asset_id>')
def api_asset(asset_id):
    record = records_by_id().get(asset_id)
    if not record:
        return jsonify({'error': 'Ativo não encontrado.'}), 404
    return jsonify(record)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8787, debug=False)
