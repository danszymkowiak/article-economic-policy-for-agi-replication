"""ADVERSARIAL ARM (prereg s9; TASK-22). Separate from, and never pooled with, the main analysis.

A pre-specified, bounded search for the smallest plausible change that moves the top policy to the
bottom. It has its own store, ledger and spend ceiling under adversarial/; see README.md.

Layers as in llm_panel: catalogue.py and search.py are pure; arm.py is the application layer
(building jobs, planning, submitting through the study's guards, evaluating from its own store);
report.py renders; cli.py is the bootstrap (`python -m adversarial`).
"""
