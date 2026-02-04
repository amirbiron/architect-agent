"""
Architect Agent - Decision Matrix & Scoring System
====================================================
The deterministic scoring system that combines mathematical weights
with constraint analysis to recommend architectural patterns.

This is the "hard logic" core of the agent that ensures consistent,
reproducible decisions based on defined criteria.
"""
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

from .patterns import PATTERNS, get_pattern
from ..agent.state import (
    Constraint, PriorityRanking, Priority, DecisionProfile,
    ArchitecturalDecision
)


# ============================================================
# SCORING WEIGHTS AND THRESHOLDS
# ============================================================

# Constraint impact on pattern scores (negative adjustments)
CONSTRAINT_IMPACTS: Dict[str, Dict[str, int]] = {
    "budget": {
        "microservices": -30,  # High cost
        "cqrs": -25,
        "event_driven": -20,
        "serverless": -10,
        "modular_monolith": -5,
        "monolith": 0
    },
    "timeline": {
        "microservices": -35,  # Takes time to set up
        "cqrs": -30,
        "event_driven": -20,
        "modular_monolith": -10,
        "serverless": -5,
        "monolith": 0
    },
    "team": {
        # Smaller/less experienced teams penalize complex patterns
        "microservices": -25,
        "cqrs": -30,
        "event_driven": -20,
        "modular_monolith": -10,
        "serverless": -15,
        "monolith": 0
    },
    "compliance": {
        # Compliance needs favor more controlled environments
        "serverless": -20,  # Vendor dependency
        "microservices": -10,
        "event_driven": -5,
        "cqrs": 5,  # Good audit trail
        "modular_monolith": 0,
        "monolith": 0
    },
    "technical": {
        # Technical constraints are pattern-specific, applied separately
    }
}

# Minimum score threshold for recommendation
MIN_SCORE_THRESHOLD = 40

# Score categories
SCORE_EXCELLENT = 80
SCORE_GOOD = 60
SCORE_ACCEPTABLE = 40


# ============================================================
# SCORING FUNCTIONS
# ============================================================

@dataclass
class ScoredPattern:
    """A pattern with its calculated score and details."""
    name: str
    score: float
    base_score: float
    adjustments: Dict[str, float]
    breakdown: Dict[str, float]
    viable: bool
    reasoning: str


def calculate_base_score(
    pattern_name: str,
    weights: Dict[str, float]
) -> Tuple[float, Dict[str, float]]:
    """
    Calculate base score for a pattern using weighted scoring.

    Args:
        pattern_name: Name of the architectural pattern
        weights: Priority weights from user (should sum to 1.0)

    Returns:
        Tuple of (total_score, breakdown_dict)
    """
    pattern = get_pattern(pattern_name)
    if not pattern:
        return 0.0, {}

    scoring = pattern.get("scoring", {})
    breakdown = {}
    total = 0.0

    for criterion, weight in weights.items():
        criterion_score = scoring.get(criterion, 50)  # Default to 50 if not defined
        weighted = criterion_score * weight
        breakdown[criterion] = weighted
        total += weighted

    return total, breakdown


def apply_constraint_adjustments(
    base_score: float,
    pattern_name: str,
    constraints: List[Constraint]
) -> Tuple[float, Dict[str, float]]:
    """
    Apply negative adjustments based on constraints.

    Args:
        base_score: The initial calculated score
        pattern_name: Name of the pattern
        constraints: List of project constraints

    Returns:
        Tuple of (adjusted_score, adjustments_dict)
    """
    adjustments = {}
    total_adjustment = 0.0

    for constraint in constraints:
        constraint_type = constraint.type

        # Get impact for this constraint type
        impacts = CONSTRAINT_IMPACTS.get(constraint_type, {})
        impact = impacts.get(pattern_name, 0)

        # Scale impact by severity
        severity_multiplier = {
            Priority.CRITICAL: 1.5,
            Priority.HIGH: 1.2,
            Priority.MEDIUM: 1.0,
            Priority.LOW: 0.7
        }.get(constraint.severity, 1.0)

        adjustment = impact * severity_multiplier
        adjustments[f"{constraint_type}:{constraint.description[:30]}"] = adjustment
        total_adjustment += adjustment

    adjusted_score = max(0, base_score + total_adjustment)
    return adjusted_score, adjustments


def score_pattern(
    pattern_name: str,
    priorities: Optional[PriorityRanking],
    constraints: List[Constraint],
    profile: Optional[DecisionProfile] = None
) -> ScoredPattern:
    """
    Calculate final score for a pattern considering all factors.

    Args:
        pattern_name: Name of the architectural pattern
        priorities: User's priority ranking (1-5 scale)
        constraints: List of project constraints
        profile: Optional decision profile override

    Returns:
        ScoredPattern with full scoring details
    """
    # Get weights from priorities or profile
    if priorities:
        weights = priorities.to_weights()
    elif profile:
        weights = _get_profile_weights(profile)
    else:
        # Balanced default
        weights = {
            "time_to_market": 0.2,
            "cost": 0.2,
            "scale": 0.2,
            "reliability": 0.2,
            "security": 0.2
        }

    # Calculate base score
    base_score, breakdown = calculate_base_score(pattern_name, weights)

    # Apply constraint adjustments
    final_score, adjustments = apply_constraint_adjustments(
        base_score, pattern_name, constraints
    )

    # Determine viability and generate reasoning
    viable = final_score >= MIN_SCORE_THRESHOLD
    reasoning = _generate_reasoning(pattern_name, final_score, breakdown, adjustments)

    return ScoredPattern(
        name=pattern_name,
        score=round(final_score, 2),
        base_score=round(base_score, 2),
        adjustments=adjustments,
        breakdown=breakdown,
        viable=viable,
        reasoning=reasoning
    )


def score_all_patterns(
    priorities: Optional[PriorityRanking],
    constraints: List[Constraint],
    profile: Optional[DecisionProfile] = None
) -> List[ScoredPattern]:
    """
    Score all available patterns and return sorted list.

    Returns:
        List of ScoredPattern sorted by score (highest first)
    """
    results = []

    for pattern_name in PATTERNS.keys():
        scored = score_pattern(pattern_name, priorities, constraints, profile)
        results.append(scored)

    # Sort by score descending
    results.sort(key=lambda x: x.score, reverse=True)

    return results


def get_top_recommendations(
    priorities: Optional[PriorityRanking],
    constraints: List[Constraint],
    profile: Optional[DecisionProfile] = None,
    top_n: int = 3
) -> List[ScoredPattern]:
    """
    Get top N recommended patterns.

    Returns:
        List of top N viable patterns
    """
    all_scored = score_all_patterns(priorities, constraints, profile)

    # Filter to viable patterns only
    viable = [p for p in all_scored if p.viable]

    # Return top N (or all viable if less than N)
    return viable[:top_n]


def convert_to_architectural_decisions(
    scored_patterns: List[ScoredPattern]
) -> List[ArchitecturalDecision]:
    """
    Convert scored patterns to ArchitecturalDecision models.

    Returns:
        List of ArchitecturalDecision ready for the state
    """
    decisions = []

    for sp in scored_patterns:
        pattern_data = get_pattern(sp.name)
        decisions.append(ArchitecturalDecision(
            pattern=sp.name,
            justification=sp.reasoning,
            trade_offs=pattern_data.get("cons", []),
            alternatives_considered=[p.name for p in scored_patterns if p.name != sp.name],
            score=sp.score
        ))

    return decisions


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def _get_profile_weights(profile: DecisionProfile) -> Dict[str, float]:
    """Get weights for a decision profile."""
    profiles = {
        DecisionProfile.MVP_FAST: {
            "time_to_market": 0.4, "cost": 0.25, "scale": 0.1,
            "reliability": 0.15, "security": 0.1
        },
        DecisionProfile.COST_FIRST: {
            "time_to_market": 0.15, "cost": 0.4, "scale": 0.15,
            "reliability": 0.15, "security": 0.15
        },
        DecisionProfile.SCALE_FIRST: {
            "time_to_market": 0.1, "cost": 0.15, "scale": 0.4,
            "reliability": 0.2, "security": 0.15
        },
        DecisionProfile.SECURITY_FIRST: {
            "time_to_market": 0.1, "cost": 0.1, "scale": 0.15,
            "reliability": 0.25, "security": 0.4
        },
    }
    return profiles.get(profile, profiles[DecisionProfile.MVP_FAST])


def _generate_reasoning(
    pattern_name: str,
    final_score: float,
    breakdown: Dict[str, float],
    adjustments: Dict[str, float]
) -> str:
    """Generate human-readable reasoning for the score."""
    pattern = get_pattern(pattern_name)
    if not pattern:
        return "Unknown pattern"

    # Find strongest and weakest points
    sorted_breakdown = sorted(breakdown.items(), key=lambda x: x[1], reverse=True)
    strongest = sorted_breakdown[0] if sorted_breakdown else ("N/A", 0)
    weakest = sorted_breakdown[-1] if sorted_breakdown else ("N/A", 0)

    # Score category
    if final_score >= SCORE_EXCELLENT:
        category = "מצוין"
    elif final_score >= SCORE_GOOD:
        category = "טוב"
    elif final_score >= SCORE_ACCEPTABLE:
        category = "סביר"
    else:
        category = "לא מומלץ"

    # Build reasoning
    reasoning_parts = [
        f"**{pattern['name']}** ({category} - {final_score:.0f}/100)",
        f"",
        f"החוזקה העיקרית: {_translate_criterion(strongest[0])}",
        f"נקודת החולשה: {_translate_criterion(weakest[0])}",
    ]

    # Add constraint impacts if significant
    significant_adjustments = {k: v for k, v in adjustments.items() if abs(v) >= 10}
    if significant_adjustments:
        reasoning_parts.append("")
        reasoning_parts.append("השפעת אילוצים:")
        for constraint, impact in significant_adjustments.items():
            sign = "+" if impact > 0 else ""
            reasoning_parts.append(f"  • {constraint.split(':')[0]}: {sign}{impact:.0f}")

    return "\n".join(reasoning_parts)


def _translate_criterion(criterion: str) -> str:
    """Translate criterion name to Hebrew."""
    translations = {
        "time_to_market": "מהירות יציאה לשוק",
        "cost": "עלות",
        "scale": "סקיילביליטי",
        "reliability": "אמינות",
        "security": "אבטחה"
    }
    return translations.get(criterion, criterion)


# ============================================================
# CONFLICT DETECTION RULES
# ============================================================

CONFLICT_RULES = [
    {
        "name": "scale_vs_cost",
        "check": lambda reqs, constraints: (
            any("scale" in r.description.lower() or "million" in r.description.lower()
                for r in reqs) and
            any(c.type == "budget" and c.severity in [Priority.HIGH, Priority.CRITICAL]
                for c in constraints)
        ),
        "explanation": "דרישת סקייל גבוהה מתנגשת עם אילוץ תקציב",
        "compromises": [
            "להתחיל בארכיטקטורה פשוטה עם תוכנית הגירה עתידית",
            "לבחור בפתרון managed שמאפשר סקייל הדרגתי",
            "להגדיר שלבי גדילה עם תקציב לכל שלב"
        ]
    },
    {
        "name": "speed_vs_security",
        "check": lambda reqs, constraints: (
            any(c.type == "timeline" and c.severity in [Priority.HIGH, Priority.CRITICAL]
                for c in constraints) and
            any("compliance" in r.description.lower() or "security" in r.description.lower()
                or "gdpr" in r.description.lower() or "pci" in r.description.lower()
                for r in reqs)
        ),
        "explanation": "דרישות אבטחה/ציות מתנגשות עם לוחות זמנים צפופים",
        "compromises": [
            "להשיק MVP עם אבטחה בסיסית ולהוסיף שכבות בהדרגה",
            "להשתמש בפתרונות managed עם compliance מובנה",
            "לצמצם scope ל-features חיוניים בלבד"
        ]
    },
    {
        "name": "reliability_vs_cost",
        "check": lambda reqs, constraints: (
            any("uptime" in r.description.lower() or "99.9" in r.description.lower()
                or "availability" in r.description.lower() for r in reqs) and
            any(c.type == "budget" and c.severity in [Priority.HIGH, Priority.CRITICAL]
                for c in constraints)
        ),
        "explanation": "דרישת זמינות גבוהה דורשת השקעה משמעותית",
        "compromises": [
            "להתחיל עם SLA נמוך יותר ולשדרג בהדרגה",
            "להשתמש ב-managed services במקום self-hosted",
            "להגדיר רמות SLA שונות לרכיבים שונים"
        ]
    }
]


def detect_conflicts(
    requirements: List,
    constraints: List[Constraint]
) -> List[Dict]:
    """
    Detect conflicts between requirements and constraints.

    Returns:
        List of conflict dictionaries
    """
    conflicts = []

    for rule in CONFLICT_RULES:
        if rule["check"](requirements, constraints):
            conflicts.append({
                "name": rule["name"],
                "explanation": rule["explanation"],
                "compromises": rule["compromises"]
            })

    return conflicts
