#!/usr/bin/env python3
"""
Memory Search Example

This example demonstrates how to use Mnemosyne's semantic memory
system to search through past behaviors and insights.

Usage:
    python memory_search.py "how do I usually start my day"
    python memory_search.py --recent
    python memory_search.py --important

Requirements:
    - Some recorded sessions with analyzed data
    - pip install mnemosyne[all]
"""

import asyncio
import sys
from datetime import datetime, timedelta

# Add parent directory to path for development
sys.path.insert(0, str(__file__).rsplit("/", 2)[0])

from mnemosyne.memory.manager import MemoryManager
from mnemosyne.memory.vector_store import VectorStore
from mnemosyne.config.settings import Settings


async def search_memories(query: str, limit: int = 10):
    """Search memories semantically."""
    print(f"🔍 Searching: '{query}'")
    print("=" * 50)

    try:
        memory = MemoryManager()
        await memory.initialize()

        results = await memory.search(query, limit=limit)

        if not results:
            print("📭 No matching memories found.")
            print("\n💡 Tips:")
            print("   - Record some sessions with basic_recording.py")
            print("   - Analyze them with analyze_session.py")
            print("   - Try broader search terms")
            return

        print(f"\n📚 Found {len(results)} memories:\n")

        for i, mem in enumerate(results, 1):
            relevance = mem.get("score", 0)
            stars = "⭐" * int(relevance * 5)

            print(f"{i}. {stars} (relevance: {relevance:.0%})")
            print(f"   📅 {mem.get('timestamp', 'Unknown')}")
            print(f"   💭 {mem.get('content', '')[:200]}...")
            if mem.get("context"):
                print(f"   🏷️  Context: {mem['context']}")
            print()

        await memory.close()

    except Exception as e:
        print(f"❌ Error: {e}")


async def show_recent(days: int = 7, limit: int = 20):
    """Show recent memories."""
    print(f"📅 Recent Memories (last {days} days)")
    print("=" * 50)

    try:
        memory = MemoryManager()
        await memory.initialize()

        since = datetime.now() - timedelta(days=days)
        results = await memory.get_recent(since=since, limit=limit)

        if not results:
            print("📭 No recent memories found.")
            return

        print(f"\n📚 {len(results)} recent memories:\n")

        for i, mem in enumerate(results, 1):
            importance = mem.get("importance", 0)
            indicator = "🔴" if importance > 0.8 else "🟡" if importance > 0.5 else "🟢"

            print(f"{i}. {indicator} [{mem.get('type', 'memory')}]")
            print(f"   📅 {mem.get('timestamp', 'Unknown')}")
            print(f"   💭 {mem.get('content', '')[:150]}...")
            print()

        await memory.close()

    except Exception as e:
        print(f"❌ Error: {e}")


async def show_important(threshold: float = 0.7, limit: int = 20):
    """Show important memories above threshold."""
    print(f"⭐ Important Memories (importance > {threshold:.0%})")
    print("=" * 50)

    try:
        memory = MemoryManager()
        await memory.initialize()

        results = await memory.get_important(threshold=threshold, limit=limit)

        if not results:
            print("📭 No important memories found above threshold.")
            print(f"💡 Try lowering the threshold (current: {threshold:.0%})")
            return

        print(f"\n📚 {len(results)} important memories:\n")

        for i, mem in enumerate(results, 1):
            importance = mem.get("importance", 0)
            stars = "⭐" * int(importance * 5)

            print(f"{i}. {stars} (importance: {importance:.0%})")
            print(f"   📅 {mem.get('timestamp', 'Unknown')}")
            print(f"   🏷️  {mem.get('category', 'general')}")
            print(f"   💭 {mem.get('content', '')[:150]}...")
            print()

        await memory.close()

    except Exception as e:
        print(f"❌ Error: {e}")


async def show_stats():
    """Show memory statistics."""
    print("📊 Memory Statistics")
    print("=" * 50)

    try:
        memory = MemoryManager()
        await memory.initialize()

        stats = await memory.get_stats()

        print(f"\n📈 Overview:")
        print(f"   Total memories: {stats.get('total_count', 0)}")
        print(f"   Categories: {stats.get('category_count', 0)}")
        print(f"   Average importance: {stats.get('avg_importance', 0):.0%}")
        print(f"   Storage size: {stats.get('storage_size_mb', 0):.2f} MB")

        if stats.get("categories"):
            print(f"\n🏷️  By Category:")
            for cat, count in stats["categories"].items():
                print(f"   {cat}: {count}")

        if stats.get("timeline"):
            print(f"\n📅 Timeline:")
            for period, count in stats["timeline"].items():
                print(f"   {period}: {count} memories")

        await memory.close()

    except Exception as e:
        print(f"❌ Error: {e}")


async def main():
    """Main entry point."""
    print("🧠 Mnemosyne Memory Search")
    print()

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python memory_search.py <query>      # Semantic search")
        print("  python memory_search.py --recent     # Recent memories")
        print("  python memory_search.py --important  # Important memories")
        print("  python memory_search.py --stats      # Memory statistics")
        print()
        print("Examples:")
        print('  python memory_search.py "morning routine"')
        print('  python memory_search.py "git workflow"')
        print('  python memory_search.py "why do I always"')
        return

    arg = sys.argv[1]

    if arg == "--recent":
        await show_recent()
    elif arg == "--important":
        await show_important()
    elif arg == "--stats":
        await show_stats()
    else:
        query = " ".join(sys.argv[1:])
        await search_memories(query)


if __name__ == "__main__":
    asyncio.run(main())
