# Enrichment Phase

This directory contains the helper modules used by `phase_enrichment.py`.

The enrichment phase differs from simpler pipeline phases because only the
initial decomposition step runs through the generic StepDefinition runner.

All later stages are orchestrated explicitly in Python and operate per episode:

1. retrieval
2. retrieval review
3. expansion
4. evaluation
5. decision
6. reassembly

This design keeps the control logic explicit and ensures that AI output is
always validated before it can alter chapter text.

Core rule:
**AI proposes; Python disposes.**