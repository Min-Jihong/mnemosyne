import pytest
from mnemosyne.memory.types import Memory, MemoryType
from mnemosyne.memory.persistent import PersistentMemory


class TestMemoryTypes:
    
    def test_memory_creation(self):
        memory = Memory(
            type=MemoryType.COMMAND,
            content="git commit -m 'test'",
            importance=0.8,
        )
        
        assert memory.type == MemoryType.COMMAND
        assert memory.content == "git commit -m 'test'"
        assert memory.importance == 0.8
        assert memory.id is not None
    
    def test_memory_access(self):
        memory = Memory(content="test", access_count=0)
        initial_time = memory.last_accessed
        
        memory.access()
        
        assert memory.access_count == 1
        assert memory.last_accessed >= initial_time
    
    def test_memory_to_dict(self):
        memory = Memory(
            type=MemoryType.INSIGHT,
            content="User prefers dark mode",
            tags=["preference", "ui"],
        )
        
        d = memory.to_dict()
        
        assert d["type"] == "insight"
        assert d["content"] == "User prefers dark mode"
        assert d["tags"] == ["preference", "ui"]


class TestPersistentMemory:
    
    def test_remember(self, temp_dir):
        mem = PersistentMemory(data_dir=temp_dir)
        
        memory = mem.remember(
            content="Test memory",
            memory_type=MemoryType.OBSERVATION,
            importance=0.5,
        )
        
        assert memory.id is not None
        assert mem.count() == 1
    
    def test_remember_command(self, temp_dir):
        mem = PersistentMemory(data_dir=temp_dir)
        
        memory = mem.remember_command(
            command="ls -la",
            result="file1.txt\nfile2.txt",
        )
        
        assert memory.type == MemoryType.COMMAND
        assert memory.importance == 0.7
    
    def test_remember_conversation(self, temp_dir):
        mem = PersistentMemory(data_dir=temp_dir)
        
        memory = mem.remember_conversation(
            user_message="What's the weather?",
            assistant_response="It's sunny today.",
        )
        
        assert memory.type == MemoryType.CONVERSATION
        assert "User:" in memory.content
        assert "Assistant:" in memory.content
    
    def test_get_recent(self, temp_dir):
        mem = PersistentMemory(data_dir=temp_dir)
        
        for i in range(5):
            mem.remember(content=f"Memory {i}")
        
        recent = mem.get_recent(n=3)
        assert len(recent) == 3
    
    def test_get_important(self, temp_dir):
        mem = PersistentMemory(data_dir=temp_dir)
        
        mem.remember(content="Low importance", importance=0.3)
        mem.remember(content="High importance", importance=0.9)
        mem.remember(content="Medium importance", importance=0.6)
        
        important = mem.get_important(n=2, min_importance=0.7)
        assert len(important) == 1
        assert important[0].content == "High importance"
    
    def test_forget(self, temp_dir):
        mem = PersistentMemory(data_dir=temp_dir)
        
        memory = mem.remember(content="To be forgotten")
        assert mem.count() == 1
        
        mem.forget(memory.id)
        assert mem.count() == 0
