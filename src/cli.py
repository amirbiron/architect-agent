#!/usr/bin/env python3
"""
Architect Agent - CLI Tool
===========================
Command line interface for testing the agent locally.

Usage:
    python -m src.cli
    python -m src.cli --session <session_id>
"""
import asyncio
import argparse
import sys
from datetime import datetime

# Add colors for better UX
class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header():
    """Print welcome header."""
    print(f"""
{Colors.CYAN}╔══════════════════════════════════════════════════════════════╗
║                                                                ║
║   🏗️  {Colors.BOLD}ARCHITECT AGENT{Colors.END}{Colors.CYAN} - AI Architecture Advisor               ║
║                                                                ║
║   Commands:                                                    ║
║     /quit    - Exit the conversation                          ║
║     /status  - Show current session status                    ║
║     /reset   - Start over (keep requirements)                 ║
║     /clear   - Start completely fresh                         ║
║     /export  - Export blueprint to file                       ║
║                                                                ║
╚══════════════════════════════════════════════════════════════╝{Colors.END}
""")


def print_assistant(message: str):
    """Print assistant message."""
    print(f"\n{Colors.GREEN}🤖 Agent:{Colors.END}")
    print(f"   {message.replace(chr(10), chr(10) + '   ')}")


def print_status(ctx):
    """Print session status."""
    print(f"""
{Colors.YELLOW}━━━━━━━━━━━━━━━ Session Status ━━━━━━━━━━━━━━━{Colors.END}
  Session ID:    {ctx.session_id[:8]}...
  Current Node:  {ctx.current_node}
  Confidence:    {ctx.confidence_score:.0%}
  Iteration:     {ctx.iteration_count}/5
  Requirements:  {len(ctx.requirements)}
  Constraints:   {len(ctx.constraints)}
  Conflicts:     {len(ctx.conflicts)} ({sum(1 for c in ctx.conflicts if not c.resolved)} unresolved)
  Has Blueprint: {'✅' if ctx.blueprint else '❌'}
{Colors.YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.END}
""")


async def run_cli(session_id: str = None):
    """Run the CLI interface."""
    from src.agent.graph import run_agent, continue_conversation
    from src.agent.state import ProjectContext

    print_header()

    ctx = None

    if session_id:
        # Try to load existing session
        print(f"{Colors.YELLOW}Loading session: {session_id}{Colors.END}")
        # In real implementation, load from DB
        # For now, start fresh
        ctx = None

    # Get initial message
    print(f"{Colors.BLUE}👤 You:{Colors.END} ", end="")
    initial_message = input().strip()

    if not initial_message:
        print(f"{Colors.RED}Please provide a project description.{Colors.END}")
        return

    # Run initial analysis
    print(f"\n{Colors.CYAN}⏳ Analyzing...{Colors.END}")
    try:
        ctx = await run_agent(initial_message)
    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.END}")
        return

    # Print response
    last_response = ""
    for msg in reversed(ctx.conversation_history):
        if msg.get("role") == "assistant":
            last_response = msg.get("content", "")
            break
    print_assistant(last_response)

    # Main conversation loop
    while True:
        print(f"\n{Colors.BLUE}👤 You:{Colors.END} ", end="")
        try:
            user_input = input().strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n{Colors.YELLOW}Goodbye!{Colors.END}")
            break

        if not user_input:
            continue

        # Handle commands
        if user_input.lower() == "/quit":
            print(f"{Colors.YELLOW}Goodbye!{Colors.END}")
            break

        elif user_input.lower() == "/status":
            if ctx:
                print_status(ctx)
            continue

        elif user_input.lower() == "/reset":
            if ctx:
                ctx.current_node = "intake"
                ctx.confidence_score = 0.0
                ctx.iteration_count = 0
                ctx.blueprint = None
                print(f"{Colors.GREEN}Session reset. Requirements kept.{Colors.END}")
            continue

        elif user_input.lower() == "/clear":
            ctx = None
            print(f"{Colors.GREEN}Session cleared. Send a new project description.{Colors.END}")
            continue

        elif user_input.lower() == "/export":
            if ctx and ctx.blueprint:
                filename = f"blueprint_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                try:
                    with open(filename, "w", encoding="utf-8") as f:
                        f.write(f"# {ctx.project_name or 'Architecture Blueprint'}\n\n")
                        f.write(f"## Executive Summary\n{ctx.blueprint.executive_summary}\n\n")
                        if ctx.blueprint.diagram:
                            f.write(f"## Architecture Diagram\n```mermaid\n{ctx.blueprint.diagram}\n```\n\n")
                        if ctx.blueprint.adrs:
                            f.write("## Architecture Decision Records\n\n")
                            for adr in ctx.blueprint.adrs:
                                f.write(f"### ADR-{adr.number}: {adr.title}\n")
                                f.write(f"**Status:** {adr.status}\n\n")
                                f.write(f"**Context:** {adr.context}\n\n")
                                f.write(f"**Decision:** {adr.decision}\n\n")
                                f.write("**Consequences:**\n")
                                for c in adr.consequences:
                                    f.write(f"- {c}\n")
                                f.write("\n")
                    print(f"{Colors.GREEN}Exported to: {filename}{Colors.END}")
                except Exception as e:
                    print(f"{Colors.RED}Export failed: {e}{Colors.END}")
            else:
                print(f"{Colors.YELLOW}No blueprint to export yet.{Colors.END}")
            continue

        # Regular message - continue conversation
        if not ctx:
            print(f"{Colors.CYAN}⏳ Analyzing...{Colors.END}")
            ctx = await run_agent(user_input)
        else:
            print(f"{Colors.CYAN}⏳ Processing...{Colors.END}")
            ctx = await continue_conversation(
                session_id=ctx.session_id,
                user_message=user_input,
                current_ctx=ctx
            )

        # Print response
        last_response = ""
        for msg in reversed(ctx.conversation_history):
            if msg.get("role") == "assistant":
                last_response = msg.get("content", "")
                break
        print_assistant(last_response)

        # Check if done
        if ctx.is_done():
            print(f"\n{Colors.GREEN}✅ Blueprint generated! Use /export to save it.{Colors.END}")


def main():
    parser = argparse.ArgumentParser(description="Architect Agent CLI")
    parser.add_argument("--session", "-s", help="Resume existing session ID")
    args = parser.parse_args()

    try:
        asyncio.run(run_cli(args.session))
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Interrupted.{Colors.END}")
        sys.exit(0)


if __name__ == "__main__":
    main()
