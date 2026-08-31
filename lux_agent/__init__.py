"""
lux_agent package
=================
Agente investigativo operacional LuxVerso dentro do Hermes.

Entry points:
  - from lux_agent import investigate, save_cycle, load_state, render_report, ...
  - python3 ~/.hermes/lux_agent/run.py "oportunidade"
"""
from .investigate import (
    # classe principal
    InvestigationCycle,
    # ciclo de vida
    investigate, save_cycle, load_state,
    # recuperacao (R1)
    find_capabilities, find_playbook,
    # acao adaptativa
    apply_action,
    # registros
    add_evidence, add_claim, add_gap, discard_path, queue_next, set_decision,
    # bridge
    assess, to_luxmemory_link,
    # render
    render_report,
    # paths
    AGENT_ROOT, STATE_DIR, CYCLES_DIR, ARTIFACTS_DIR,
)
