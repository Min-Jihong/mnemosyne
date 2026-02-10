import json
from pathlib import Path
from typing import Any

from mnemosyne.memory.types import Memory, MemoryType


class VectorStore:
    
    def __init__(self, persist_dir: Path | str):
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self._collection = None
        self._client = None
    
    def _ensure_client(self) -> None:
        if self._client is None:
            try:
                import chromadb
                self._client = chromadb.PersistentClient(
                    path=str(self.persist_dir / "chroma")
                )
                self._collection = self._client.get_or_create_collection(
                    name="mnemosyne_memories",
                    metadata={"hnsw:space": "cosine"},
                )
            except ImportError:
                raise ImportError(
                    "chromadb is required for vector storage. "
                    "Install with: pip install chromadb"
                )
    
    def add(self, memory: Memory, embedding: list[float] | None = None) -> None:
        self._ensure_client()
        
        self._collection.add(
            ids=[memory.id],
            documents=[memory.content],
            metadatas=[{
                "type": memory.type.value,
                "importance": memory.importance,
                "created_at": memory.created_at,
                "tags": json.dumps(memory.tags),
                "context": json.dumps(memory.context),
            }],
            embeddings=[embedding] if embedding else None,
        )
    
    def search(
        self,
        query: str,
        n_results: int = 10,
        memory_types: list[MemoryType] | None = None,
    ) -> list[tuple[Memory, float]]:
        self._ensure_client()
        
        where = None
        if memory_types:
            where = {"type": {"$in": [t.value for t in memory_types]}}
        
        results = self._collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        
        memories = []
        if results["ids"] and results["ids"][0]:
            for i, id_ in enumerate(results["ids"][0]):
                metadata = results["metadatas"][0][i]
                memory = Memory(
                    id=id_,
                    type=MemoryType(metadata["type"]),
                    content=results["documents"][0][i],
                    importance=metadata.get("importance", 0.5),
                    created_at=metadata.get("created_at", 0),
                    context=json.loads(metadata.get("context", "{}")),
                    tags=json.loads(metadata.get("tags", "[]")),
                )
                distance = results["distances"][0][i] if results["distances"] else 0
                similarity = 1 - distance
                memories.append((memory, similarity))
        
        return memories
    
    def get(self, memory_id: str) -> Memory | None:
        self._ensure_client()
        
        results = self._collection.get(
            ids=[memory_id],
            include=["documents", "metadatas"],
        )
        
        if not results["ids"]:
            return None
        
        metadata = results["metadatas"][0]
        return Memory(
            id=memory_id,
            type=MemoryType(metadata["type"]),
            content=results["documents"][0],
            importance=metadata.get("importance", 0.5),
            created_at=metadata.get("created_at", 0),
            context=json.loads(metadata.get("context", "{}")),
            tags=json.loads(metadata.get("tags", "[]")),
        )
    
    def delete(self, memory_id: str) -> None:
        self._ensure_client()
        self._collection.delete(ids=[memory_id])
    
    def count(self) -> int:
        self._ensure_client()
        return self._collection.count()
