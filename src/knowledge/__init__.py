"""
Architect Agent - Knowledge Package
====================================
Architectural patterns and decision matrix.

Note: Use explicit imports to avoid circular dependencies:
    from src.knowledge.patterns import PATTERNS
    from src.knowledge.decision_matrix import score_pattern
"""

__all__ = [
    "PATTERNS",
    "get_pattern",
    "get_all_pattern_names",
    "score_pattern",
    "score_all_patterns",
    "get_top_recommendations",
    "convert_to_architectural_decisions",
    "detect_conflicts",
    "ScoredPattern",
]


def __getattr__(name):
    """Lazy imports to avoid circular dependencies."""
    if name in ("PATTERNS", "get_pattern", "get_all_pattern_names"):
        from .patterns import PATTERNS, get_pattern, get_all_pattern_names
        return locals()[name]
    elif name in ("score_pattern", "score_all_patterns", "get_top_recommendations",
                  "convert_to_architectural_decisions", "detect_conflicts", "ScoredPattern"):
        from .decision_matrix import (
            score_pattern, score_all_patterns, get_top_recommendations,
            convert_to_architectural_decisions, detect_conflicts, ScoredPattern
        )
        return locals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
