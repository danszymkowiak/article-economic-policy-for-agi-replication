"""EXPLORATORY reversed-scale probe (TASK-38; prereg s13). Separate from, and never pooled with,
the main analysis and the adversarial arm.

Asks the study model to rate with 0 = best and 100 = worst, on the adversarial arm's search panel,
and compares the converted scores (100 - x) with the arm's baseline run, using the arm's rerun as
the noise reference. Own store, ledger and ceiling under scale_probe/; see README.md.

analysis.py is pure; probe.py is the application layer; report.py renders; cli.py is the
bootstrap (`python -m scale_probe`).
"""
