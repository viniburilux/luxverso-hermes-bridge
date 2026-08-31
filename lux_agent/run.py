#!/usr/bin/env python3
"""
Lux Investigation Agent — Entry point CLI.

Uso:
  python3 run.py "tem um edital sobre X?"
  python3 run.py "investigue oportunidade Y" --resume
  python3 run.py --render <opportunity_id>

O Hermes usa este script quando o usuario faz uma pergunta investigativa.
O agente reusa TraceFoundry, LuxMemory API, Capability Registry, playbooks.
"""
import sys
import os
import argparse
from pathlib import Path

# Adiciona o proprio diretorio ao path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, '/home/vinicius/.hermes/integrations')
sys.path.insert(0, '/home/vinicius/luxverso-archive/TraceFoundry/src')

from lux_agent import investigate, save_cycle, render_report


def main():
    p = argparse.ArgumentParser(description='Lux Investigation Agent')
    p.add_argument('opportunity', nargs='?', help='Descricao da oportunidade (opcional se --list)')
    p.add_argument('--resume', action='store_true', help='Carregar estado anterior')
    p.add_argument('--render', metavar='OPID', help='Renderizar relatorio de uma oportunidade')
    p.add_argument('--list', action='store_true', help='Listar oportunidades existentes')
    args = p.parse_args()

    if args.list:
        base = Path('/home/vinicius/.hermes/lux_agent')
        opps = sorted([d for d in base.iterdir() if d.is_dir() and not d.name.startswith('.')])
        if not opps:
            print('(nenhuma oportunidade)')
            return
        for o in opps:
            cycles = list((o / 'cycles').glob('cycle_*.json'))
            print(f"  {o.name}: {len(cycles)} ciclo(s)")
        return

    if args.render:
        from lux_agent import load_state, render_report
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
    print(f"📋 InvestigationCycle criada")
    print(f"  opportunity_id: {c.opportunity_id}")
    print(f"  cycle_n: {c.cycle_n}")
    print(f"  question: {c.question}")
    print(f"  path: lux_agent/{c.opportunity_id}/cycles/cycle_{c.cycle_n:03d}.json")
    print()
    print(f"Próximos passos para o Hermes:")
    print(f"  1. R1: buscar capacidades e experiencias (find_capabilities, find_playbook)")
    print(f"  2. R2: executar investigacao (search_files, web_search, delegate_task)")
    print(f"  3. S: extrair sinais (add_evidence, add_claim, add_gap, discard_path)")
    print(f"  4. P': decidir (set_decision, queue_next)")
    print(f"  5. save_cycle(c) para persistir")


if __name__ == '__main__':
    main()
