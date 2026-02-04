"""
Architect Agent - Conflict Node
================================
Detects conflicts between requirements and proposes compromises.
"""
import logging
from typing import Tuple, List

from ..state import (
    ProjectContext, Conflict, ConflictAnalysis, Priority
)
from ...llm.client import LLMClient
from ...llm.prompts import CONFLICT_DETECTION_PROMPT, BASE_SYSTEM_PROMPT
from ...knowledge.decision_matrix import detect_conflicts

logger = logging.getLogger(__name__)


async def conflict_node(
    ctx: ProjectContext,
    llm: LLMClient
) -> Tuple[ProjectContext, str]:
    """
    Conflict node - detects and reports requirement conflicts.

    Args:
        ctx: Current project context
        llm: LLM client instance

    Returns:
        Tuple of (updated context, reply message)
    """
    logger.info(f"[{ctx.session_id}] Running conflict node")
    ctx.current_node = "conflict"

    # First, run deterministic conflict detection
    rule_based_conflicts = detect_conflicts(ctx.requirements, ctx.constraints)

    # Then use LLM for nuanced conflict detection
    llm_conflicts = await _detect_conflicts_llm(ctx, llm)

    # Merge conflicts (avoid duplicates)
    all_conflicts = _merge_conflicts(rule_based_conflicts, llm_conflicts)

    # Update context
    ctx.conflicts = all_conflicts

    if not ctx.conflicts:
        reply = "✅ לא זיהיתי סתירות משמעותיות בדרישות. ממשיכים!"
        ctx.add_message("assistant", reply)
        logger.info(f"[{ctx.session_id}] No conflicts detected")
        return ctx, reply

    # Build conflict report
    reply = _build_conflict_reply(ctx.conflicts)
    ctx.add_message("assistant", reply)
    ctx.waiting_for_user = True

    logger.info(f"[{ctx.session_id}] Detected {len(ctx.conflicts)} conflicts")
    return ctx, reply


async def _detect_conflicts_llm(
    ctx: ProjectContext,
    llm: LLMClient
) -> List[Conflict]:
    """Use LLM to detect nuanced conflicts."""
    requirements_str = "\n".join([
        f"- [{r.category}] {r.description} (priority: {r.priority})"
        for r in ctx.requirements
    ])

    constraints_str = "\n".join([
        f"- [{c.type}] {c.description} (severity: {c.severity})"
        for c in ctx.constraints
    ])

    priorities_str = ""
    if ctx.priority_ranking:
        priorities_str = ctx.priority_ranking.model_dump_json()
    elif ctx.decision_profile:
        priorities_str = f"Profile: {ctx.decision_profile.value}"

    prompt = CONFLICT_DETECTION_PROMPT.format(
        requirements=requirements_str or "אין",
        constraints=constraints_str or "אין",
        priorities=priorities_str or "לא הוגדרו"
    )

    try:
        response = await llm.generate_structured(
            prompt=prompt,
            response_model=ConflictAnalysis,
            system_prompt=BASE_SYSTEM_PROMPT
        )
        return response.conflicts
    except Exception as e:
        logger.warning(f"LLM conflict detection failed: {e}")
        return []


def _merge_conflicts(
    rule_based: List[dict],
    llm_conflicts: List[Conflict]
) -> List[Conflict]:
    """Merge rule-based and LLM-detected conflicts."""
    conflicts = []

    # Add rule-based conflicts
    for rc in rule_based:
        conflicts.append(Conflict(
            requirements=rc.get("requirements", []),
            explanation=rc.get("explanation", ""),
            compromises=rc.get("compromises", []),
            resolved=False
        ))

    # Add LLM conflicts (check for duplicates)
    existing_explanations = {c.explanation.lower() for c in conflicts}

    for lc in llm_conflicts:
        if lc.explanation.lower() not in existing_explanations:
            conflicts.append(lc)
            existing_explanations.add(lc.explanation.lower())

    return conflicts


def _build_conflict_reply(conflicts: List[Conflict]) -> str:
    """Build a user-friendly conflict report."""
    parts = ["### ⚠️ זיהיתי סתירות בדרישות:\n"]

    for i, conflict in enumerate(conflicts, 1):
        parts.append(f"""
**קונפליקט #{i}:** {conflict.explanation}
""")
        if conflict.requirements:
            parts.append("דרישות מעורבות:")
            for req in conflict.requirements[:3]:
                parts.append(f"  • {req}")

        parts.append("\n**פשרות אפשריות:**")
        for j, comp in enumerate(conflict.compromises, 1):
            parts.append(f"  {j}. {comp}")

        parts.append("")

    parts.append("""
---
**איזה מסלול פשרה מעדיף?**
(ענה עם מספר הקונפליקט ומספר הפשרה, למשל: "1-2" לקונפליקט 1, פשרה 2)

או כתוב "דלג" להמשיך בלי לפתור עכשיו.
""")

    return "\n".join(parts)


def process_conflict_response(
    ctx: ProjectContext,
    user_message: str
) -> bool:
    """
    Process user's response to conflict resolution.

    Returns:
        True if response was processed successfully
    """
    message = user_message.strip().lower()

    # Skip resolution
    if message in ["דלג", "skip", "המשך", "continue"]:
        return True

    # Try to parse "X-Y" format (conflict-compromise)
    import re
    matches = re.findall(r"(\d+)\s*[-:]\s*(\d+)", message)

    for conflict_num, compromise_num in matches:
        conflict_idx = int(conflict_num) - 1
        compromise_idx = int(compromise_num) - 1

        if 0 <= conflict_idx < len(ctx.conflicts):
            conflict = ctx.conflicts[conflict_idx]
            if 0 <= compromise_idx < len(conflict.compromises):
                conflict.resolved = True
                conflict.chosen_compromise = conflict.compromises[compromise_idx]
                logger.info(
                    f"Resolved conflict {conflict_idx + 1} "
                    f"with compromise {compromise_idx + 1}"
                )

    return True
