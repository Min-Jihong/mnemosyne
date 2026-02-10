import json
import sqlite3
import time
from pathlib import Path
from typing import Any

from mnemosyne.memory.types import Memory, MemoryType
from mnemosyne.memory.vector_store import VectorStore
from mnemosyne.llm.base import BaseLLMProvider


class PersistentMemory:
    
    def __init__(
        self,
        data_dir: Path | str,
        llm: BaseLLMProvider | None = None,
    ):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self._db_path = self.data_dir / "memory.db"
        self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        self._init_schema()
        
        self._vector_store = VectorStore(self.data_dir / "vectors")
        self._llm = llm
    
    def _init_schema(self) -> None:
        cursor = self._conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                context TEXT,
                importance REAL DEFAULT 0.5,
                created_at REAL,
                last_accessed REAL,
                access_count INTEGER DEFAULT 0,
                tags TEXT
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(type)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_importance ON memories(importance)
        """)
        
        self._conn.commit()
    
    def remember(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.OBSERVATION,
        context: dict[str, Any] | None = None,
        importance: float = 0.5,
        tags: list[str] | None = None,
    ) -> Memory:
        memory = Memory(
            type=memory_type,
            content=content,
            context=context or {},
            importance=importance,
            tags=tags or [],
        )
        
        cursor = self._conn.cursor()
        cursor.execute("""
            INSERT INTO memories (id, type, content, context, importance, 
                                 created_at, last_accessed, access_count, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            memory.id,
            memory.type.value,
            memory.content,
            json.dumps(memory.context),
            memory.importance,
            memory.created_at,
            memory.last_accessed,
            memory.access_count,
            json.dumps(memory.tags),
        ))
        self._conn.commit()
        
        try:
            self._vector_store.add(memory)
        except Exception:
            pass
        
        return memory
    
    def remember_command(
        self,
        command: str,
        result: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> Memory:
        ctx = context or {}
        ctx["result"] = result
        
        return self.remember(
            content=command,
            memory_type=MemoryType.COMMAND,
            context=ctx,
            importance=0.7,
            tags=["command"],
        )
    
    def remember_conversation(
        self,
        user_message: str,
        assistant_response: str,
        context: dict[str, Any] | None = None,
    ) -> Memory:
        content = f"User: {user_message}\nAssistant: {assistant_response}"
        
        return self.remember(
            content=content,
            memory_type=MemoryType.CONVERSATION,
            context=context or {},
            importance=0.6,
            tags=["conversation"],
        )
    
    def remember_insight(
        self,
        insight: str,
        source: str = "",
        confidence: float = 0.5,
    ) -> Memory:
        return self.remember(
            content=insight,
            memory_type=MemoryType.INSIGHT,
            context={"source": source, "confidence": confidence},
            importance=0.8,
            tags=["insight"],
        )
    
    def recall(
        self,
        query: str,
        n_results: int = 10,
        memory_types: list[MemoryType] | None = None,
    ) -> list[Memory]:
        try:
            results = self._vector_store.search(
                query=query,
                n_results=n_results,
                memory_types=memory_types,
            )
            
            memories = []
            for memory, score in results:
                self._update_access(memory.id)
                memory.access()
                memories.append(memory)
            
            return memories
            
        except Exception:
            return self._recall_from_db(query, n_results, memory_types)
    
    def _recall_from_db(
        self,
        query: str,
        n_results: int,
        memory_types: list[MemoryType] | None,
    ) -> list[Memory]:
        cursor = self._conn.cursor()
        
        sql = """
            SELECT id, type, content, context, importance, 
                   created_at, last_accessed, access_count, tags
            FROM memories
            WHERE content LIKE ?
        """
        params: list[Any] = [f"%{query}%"]
        
        if memory_types:
            placeholders = ",".join("?" * len(memory_types))
            sql += f" AND type IN ({placeholders})"
            params.extend(t.value for t in memory_types)
        
        sql += " ORDER BY importance DESC, last_accessed DESC LIMIT ?"
        params.append(n_results)
        
        cursor.execute(sql, params)
        
        memories = []
        for row in cursor.fetchall():
            memory = Memory(
                id=row[0],
                type=MemoryType(row[1]),
                content=row[2],
                context=json.loads(row[3]) if row[3] else {},
                importance=row[4],
                created_at=row[5],
                last_accessed=row[6],
                access_count=row[7],
                tags=json.loads(row[8]) if row[8] else [],
            )
            self._update_access(memory.id)
            memories.append(memory)
        
        return memories
    
    def _update_access(self, memory_id: str) -> None:
        cursor = self._conn.cursor()
        cursor.execute("""
            UPDATE memories 
            SET last_accessed = ?, access_count = access_count + 1
            WHERE id = ?
        """, (time.time(), memory_id))
        self._conn.commit()
    
    def get_recent(
        self,
        n: int = 10,
        memory_types: list[MemoryType] | None = None,
    ) -> list[Memory]:
        cursor = self._conn.cursor()
        
        sql = """
            SELECT id, type, content, context, importance,
                   created_at, last_accessed, access_count, tags
            FROM memories
        """
        params: list[Any] = []
        
        if memory_types:
            placeholders = ",".join("?" * len(memory_types))
            sql += f" WHERE type IN ({placeholders})"
            params.extend(t.value for t in memory_types)
        
        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(n)
        
        cursor.execute(sql, params)
        
        return [
            Memory(
                id=row[0],
                type=MemoryType(row[1]),
                content=row[2],
                context=json.loads(row[3]) if row[3] else {},
                importance=row[4],
                created_at=row[5],
                last_accessed=row[6],
                access_count=row[7],
                tags=json.loads(row[8]) if row[8] else [],
            )
            for row in cursor.fetchall()
        ]
    
    def get_important(self, n: int = 10, min_importance: float = 0.7) -> list[Memory]:
        cursor = self._conn.cursor()
        cursor.execute("""
            SELECT id, type, content, context, importance,
                   created_at, last_accessed, access_count, tags
            FROM memories
            WHERE importance >= ?
            ORDER BY importance DESC, access_count DESC
            LIMIT ?
        """, (min_importance, n))
        
        return [
            Memory(
                id=row[0],
                type=MemoryType(row[1]),
                content=row[2],
                context=json.loads(row[3]) if row[3] else {},
                importance=row[4],
                created_at=row[5],
                last_accessed=row[6],
                access_count=row[7],
                tags=json.loads(row[8]) if row[8] else [],
            )
            for row in cursor.fetchall()
        ]
    
    def forget(self, memory_id: str) -> None:
        cursor = self._conn.cursor()
        cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        self._conn.commit()
        
        try:
            self._vector_store.delete(memory_id)
        except Exception:
            pass
    
    def count(self) -> int:
        cursor = self._conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM memories")
        return cursor.fetchone()[0]
    
    async def consolidate(self) -> list[Memory]:
        if self._llm is None:
            return []
        
        recent = self.get_recent(n=50)
        
        if len(recent) < 10:
            return []
        
        content_summary = "\n".join([
            f"- [{m.type.value}] {m.content[:100]}"
            for m in recent[:20]
        ])
        
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an AI that consolidates memories into insights. "
                    "Find patterns and create higher-level understanding."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Recent memories:\n{content_summary}\n\n"
                    "What patterns or insights can you derive from these memories? "
                    "Provide 2-3 key insights."
                ),
            },
        ]
        
        response = await self._llm.generate(messages)
        
        insights = []
        for line in response.strip().split("\n"):
            if line.strip():
                insight = self.remember_insight(
                    insight=line.strip(),
                    source="consolidation",
                    confidence=0.7,
                )
                insights.append(insight)
        
        return insights
