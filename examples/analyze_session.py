#!/usr/bin/env python3
"""
Session Analysis Example

This example demonstrates how to analyze a recorded session using
the Curious LLM to understand user behavior patterns.

Usage:
    python analyze_session.py <session_id>
    python analyze_session.py --list  # List available sessions

Requirements:
    - A recorded session (use basic_recording.py first)
    - LLM API key configured (OpenAI, Anthropic, etc.)
    - pip install mnemosyne[all]
"""

import asyncio
import sys
from datetime import datetime, timedelta

# Add parent directory to path for development
sys.path.insert(0, str(__file__).rsplit("/", 2)[0])

from mnemosyne.store.database import Database
from mnemosyne.reason.curious import CuriousLLM
from mnemosyne.reason.intent import IntentInference
from mnemosyne.llm.factory import LLMFactory
from mnemosyne.config.settings import Settings


async def list_sessions(db: Database):
    """List all available sessions."""
    sessions = await db.list_sessions()

    if not sessions:
        print("📭 No sessions found. Run basic_recording.py first!")
        return

    print("\n📋 Available Sessions:")
    print("=" * 70)
    print(f"{'ID':<36} {'Name':<20} {'Events':<10} {'Created'}")
    print("-" * 70)

    for session in sessions:
        created = session.get("created_at", "Unknown")
        if isinstance(created, datetime):
            created = created.strftime("%Y-%m-%d %H:%M")
        print(
            f"{session['id']:<36} {session['name'][:20]:<20} "
            f"{session.get('event_count', 0):<10} {created}"
        )

    print("\n💡 Run: python analyze_session.py <session_id>")


async def analyze_session(session_id: str):
    """Analyze a recorded session with AI."""
    print(f"🔍 Analyzing session: {session_id}")
    print("=" * 50)

    # Initialize components
    settings = Settings.load()
    db = Database()

    # Check if session exists
    session = await db.get_session(session_id)
    if not session:
        print(f"❌ Session not found: {session_id}")
        print("💡 Run: python analyze_session.py --list")
        return

    print(f"📁 Session: {session['name']}")
    print(f"📅 Created: {session.get('created_at', 'Unknown')}")

    # Load events
    events = await db.get_events(session_id)
    print(f"📊 Total events: {len(events)}")

    if not events:
        print("⚠️  No events in this session!")
        return

    # Initialize LLM
    print("\n🤖 Initializing AI analysis...")
    try:
        llm = LLMFactory.create(
            provider=settings.llm.provider,
            model=settings.llm.model,
            api_key=settings.llm.api_key,
        )
    except Exception as e:
        print(f"❌ Failed to initialize LLM: {e}")
        print("💡 Run: mnemosyne setup")
        return

    # Phase 1: Intent Inference
    print("\n" + "=" * 50)
    print("🎯 PHASE 1: Intent Inference")
    print("=" * 50)

    intent_engine = IntentInference(llm)

    # Sample events for analysis (don't analyze every single event)
    sample_size = min(100, len(events))
    sampled_events = events[:sample_size]

    print(f"Analyzing {sample_size} events...")

    intents = await intent_engine.infer_batch(sampled_events)

    print("\n📋 Inferred Intents:")
    for i, (event, intent) in enumerate(zip(sampled_events[:10], intents[:10])):
        print(f"  {i+1}. [{event.type.name}] → {intent.action}")
        if intent.reasoning:
            print(f"      Why: {intent.reasoning[:60]}...")

    if len(intents) > 10:
        print(f"  ... and {len(intents) - 10} more")

    # Phase 2: Curious Analysis
    print("\n" + "=" * 50)
    print("🤔 PHASE 2: Curious Analysis")
    print("=" * 50)

    curious = CuriousLLM(llm, curiosity_threshold=0.6)

    print("Generating questions about your behavior...")
    questions = await curious.observe_and_wonder(events)

    if questions:
        print(f"\n❓ {len(questions)} Questions About Your Session:\n")
        for i, q in enumerate(questions, 1):
            importance = "🔴" if q.importance > 0.8 else "🟡" if q.importance > 0.5 else "🟢"
            print(f"{importance} [{q.category}] {q.question}")
            print(f"   Confidence: {q.confidence:.0%} | Importance: {q.importance:.0%}")
            print()
    else:
        print("🤷 No significant patterns detected in this session.")

    # Phase 3: Pattern Summary
    print("=" * 50)
    print("📊 PHASE 3: Pattern Summary")
    print("=" * 50)

    summary = await curious.generate_summary(events, intents)
    print(summary)

    # Cleanup
    await db.close()

    print("\n✅ Analysis complete!")


async def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("🧠 Mnemosyne Session Analyzer")
        print("\nUsage:")
        print("  python analyze_session.py <session_id>")
        print("  python analyze_session.py --list")
        return

    arg = sys.argv[1]

    db = Database()

    if arg == "--list":
        await list_sessions(db)
    else:
        await analyze_session(arg)

    await db.close()


if __name__ == "__main__":
    asyncio.run(main())
