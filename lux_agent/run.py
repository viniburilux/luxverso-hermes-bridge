#!/usr/bin/env python3
"""
Lux Investigation Agent — Entry point CLI.

Uso:
  python3 run.py "oportunidade aqui"
  python3 run.py "oportunidade" --resume
  python3 run.py --render <opportunity_id>
  python3 run.py --list

Configuracao via variaveis de ambiente:
  HERMES_HOME         - raiz do Hermes (default: diretorio deste script)
  TRACE_FOUNDRY_SRC   - path para TraceFoundry/src (opcional, modo degradado se faltar)
  HERMES_INTEGRATIONS - path para integracoes Hermes (opcional)
  LUX_AGENT_ROOT      - raiz do agente (default: <HERMES_HOME>/lux_agent)
"""
import sys
import os
from pathlib import Path

# Paths via env var (sem hardcode de estrutura local)
HERMES_HOME = Path(os.environ.get('HERMES_HOME', str(Path(__file__).parent.parent)))
if str(HERMES_HOME) not in sys.path:
    sys.path.insert(0, str(HERMES_HOME))

_int = os.environ.get('HERMES_INTEGRATIONS')
if _int:
    sys.path.insert(0, _int)

_tf = os.environ.get('TRACE_FOUNDRY_SRC')
if _tf:
    sys.path.insert(0, _tf)

from lux_agent import investigate, save_cycle, render_report


def main():
    import argparse
    p = argparse.ArgumentParser(description='Lux Investigation Agent')
    p.add_argument('opportunity', nargs='?', help='Descricao da oportunidade (opcional se --list)')
    p.add_argument('--resume', action='store_true', help='Carregar estado anterior')
    p.add_argument('--render', metavar='OPID', help='Renderizar relatorio de uma oportunidade')
    p.add_argument('--list', action='store_true', help='Listar oportunidades existentes')
    args = p.parse_args()

    if args.list:
        from lux_agent import AGENT_ROOT
        opps = sorted([d for d in AGENT_ROOT.iterdir() if d.is_dir() and not d.name.startswith('.')])
        if not opps:
            print('(nenhuma oportunidade)')
            return
        for o in opps:
            cycles = list((o / 'cycles').glob('cycle_*.json'))
            print(f"  {o.name}: {len(cycles)} ciclo(s)")
        return

    if args.render:
        from lux_agent import load_state
        c = load_state(args.render)
        if c is None:
            print(f"Oportunidade {args.render} nao encontrada")
            sys.exit(1)
        print(render_report(c))
        return

    if not args.opportunity:
        p.print_help()
        sys.exit(1)

    c = investigate(args.opportunity, auto_resume=args.resume)
    print(f"InvestigationCycle criada")
    print(f"  opportunity_id: {c.opportunity_id}")
    print(f"  cycle_n: {c.cycle_n}")
    print(f"  question: {c.question}")
    print(f"  path: lux_agent/{c.opportunity_id}/cycles/cycle_{c.cycle_n:03d}.json")
    print()
    print("Proximos passos para o Hermes:")
    print("  1. R1: buscar capacidades (find_capabilities, find_playbook)")
    print("  2. R2: executar investigacao (search_files, web_search, delegate_task)")
    print("  3. S: extrair sinais (add_evidence, add_claim, add_gap, discard_path)")
    print("  4. P': decidir (set_decision, queue_next)")
    print("  5. save_cycle(c) para persistir")


if __name__ == '__main__':
    main()
