"""Taisho Canon Digest Detection System.

Discovers digest (chāojīng 抄經) relationships across ~2,459 texts in the
Taisho canon using a multi-stage pipeline: extraction, fingerprinting,
alignment, scoring, and reporting.
"""

__all__ = [
    "config",
    "extract",
    "fingerprint",
    "candidates",
    "align",
    "score",
    "report",
    "pipeline",
    "models",
    "phonetic",
]
