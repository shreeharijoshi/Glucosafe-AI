"""Evaluation components (to be implemented after data validation)."""
"""Evaluation design components."""

from .lopo import build_lopo_manifest, save_lopo_manifest
from .baseline import evaluate_model_a

__all__ = ["build_lopo_manifest", "save_lopo_manifest", "evaluate_model_a"]
