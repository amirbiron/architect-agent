"""
Architect Agent - Deep Dive Node
=================================
Asks follow-up questions to gather more information
when confidence is low.
"""
import logging
from typing import Tuple, List
from pydantic import BaseModel, Field

from ..state import ProjectContext, Requirement, Constraint
from ...llm.client import LLMClient
from ...llm.prompts import DEEP_DIVE_PROMPT, BASE_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class DeepDiveResponse(BaseModel):
    """LLM response for deep dive analysis."""
    new_requirements: List[Requirement] = Field(default_factory=list)
    new_constraints: List[Constraint] = Field(default_factory=list)
    follow_up_questions: List[str] = Field(default_factory=list)
    ready_to_proceed: bool = False
    summary: str = ""


async def deep_dive_node(
    ctx: ProjectContext,
    llm: LLMClient
) -> Tuple[ProjectContext, str]:
    """
    Deep dive node - processes user responses and asks follow-up questions.

    Args:
        ctx: Current project context
        llm: LLM client instance

    Returns:
        Tuple of (updated context, reply message)
    """
    logger.info(f"[{ctx.session_id}] Running deep dive node")
    ctx.current_node = "deep_dive"

    # Get recent user messages (answers to previous questions)
    recent_user_messages = _get_recent_user_messages(ctx)

    # Analyze responses
    response = await _analyze_responses(ctx, llm, recent_user_messages)

    # Update context with new information
    if response.new_requirements:
        ctx.requirements.extend(response.new_requirements)
        logger.info(f"Added {len(response.new_requirements)} new requirements")

    if response.new_constraints:
        ctx.constraints.extend(response.new_constraints)
        logger.info(f"Added {len(response.new_constraints)} new constraints")

    # Update open questions
    ctx.open_questions = response.follow_up_questions[:3]

    # Build reply
    if response.ready_to_proceed or not response.follow_up_questions:
        reply = _build_proceed_reply(response.summary)
        ctx.waiting_for_user = False
        # Bump confidence since we got more info
        ctx.confidence_score = min(ctx.confidence_score + 0.15, 0.9)
    else:
        reply = _build_questions_reply(response)
        ctx.waiting_for_user = True

    ctx.add_message("assistant", reply)
    return ctx, reply


def _get_recent_user_messages(ctx: ProjectContext) -> str:
    """Extract recent user messages from history."""
    user_messages = []

    for msg in ctx.conversation_history[-6:]:  # Last 6 messages
        if msg.get("role") == "user":
            user_messages.append(msg.get("content", ""))

    return "\n---\n".join(user_messages)


async def _analyze_responses(
    ctx: ProjectContext,
    llm: LLMClient,
    user_responses: str
) -> DeepDiveResponse:
    """Analyze user responses and extract information."""

    # Build context summary
    current_context = f"""
שם הפרויקט: {ctx.project_name or 'לא הוגדר'}
דרישות קיימות: {len(ctx.requirements)}
אילוצים קיימים: {len(ctx.constraints)}
עדיפויות: {ctx.decision_profile or ctx.priority_ranking or 'לא הוגדרו'}
רמת ביטחון נוכחית: {ctx.confidence_score:.2f}
"""

    open_questions_str = "\n".join([
        f"- {q}" for q in ctx.open_questions
    ]) if ctx.open_questions else "אין שאלות פתוחות"

    prompt = DEEP_DIVE_PROMPT.format(
        user_responses=user_responses or "אין תשובות חדשות",
        current_context=current_context,
        open_questions=open_questions_str
    )

    try:
        response = await llm.generate_structured(
            prompt=prompt,
            response_model=DeepDiveResponse,
            system_prompt=BASE_SYSTEM_PROMPT
        )
        return response
    except Exception as e:
        logger.warning(f"Deep dive analysis failed: {e}")
        return DeepDiveResponse(
            ready_to_proceed=True,
            summary="ממשיכים עם המידע הקיים"
        )


def _build_proceed_reply(summary: str) -> str:
    """Build reply indicating we have enough info to proceed."""
    return f"""
## ✅ יש לי מספיק מידע

{summary}

ממשיך לשלב הבא - ניתוח והמלצה על ארכיטקטורה...
"""


def _build_questions_reply(response: DeepDiveResponse) -> str:
    """Build reply with follow-up questions."""
    parts = ["## 🔍 צריך עוד קצת מידע\n"]

    if response.summary:
        parts.append(response.summary)
        parts.append("")

    if response.new_requirements or response.new_constraints:
        parts.append("**עדכנתי את ההבנה שלי:**")
        if response.new_requirements:
            parts.append(f"  • {len(response.new_requirements)} דרישות חדשות")
        if response.new_constraints:
            parts.append(f"  • {len(response.new_constraints)} אילוצים חדשים")
        parts.append("")

    parts.append("**שאלות נוספות:**\n")
    for i, q in enumerate(response.follow_up_questions[:3], 1):
        parts.append(f"{i}. {q}")

    return "\n".join(parts)


def process_deep_dive_response(
    ctx: ProjectContext,
    user_message: str
) -> None:
    """
    Process user's answers to deep dive questions.
    Simply stores the message - actual processing happens in the node.
    """
    ctx.add_message("user", user_message)
    ctx.waiting_for_user = False
