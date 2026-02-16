from __future__ import annotations

import hashlib
import json
import math
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Sequence

import numpy as np
from pydantic import BaseModel, Field


class ActionEmbedding(BaseModel):
    event_id: str
    vector: list[float] = Field(default_factory=list)
    action_type: str = ""
    app_context: str = ""
    timestamp: float = 0.0

    @property
    def dimension(self) -> int:
        return len(self.vector)

    def similarity(self, other: ActionEmbedding) -> float:
        if not self.vector or not other.vector:
            return 0.0

        v1 = np.array(self.vector)
        v2 = np.array(other.vector)

        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(np.dot(v1, v2) / (norm1 * norm2))


class SequenceEmbedding(BaseModel):
    sequence_id: str
    vector: list[float] = Field(default_factory=list)
    action_count: int = 0
    duration_seconds: float = 0.0
    dominant_app: str = ""
    inferred_goal: str | None = None


@dataclass
class Vocabulary:
    token_to_id: dict[str, int] = field(default_factory=dict)
    id_to_token: dict[int, str] = field(default_factory=dict)
    frequencies: dict[str, int] = field(default_factory=dict)

    SPECIAL_TOKENS = ["<PAD>", "<UNK>", "<BOS>", "<EOS>", "<SEP>"]

    def __post_init__(self) -> None:
        for i, token in enumerate(self.SPECIAL_TOKENS):
            if token not in self.token_to_id:
                self.token_to_id[token] = i
                self.id_to_token[i] = token

    def add_token(self, token: str) -> int:
        if token not in self.token_to_id:
            new_id = len(self.token_to_id)
            self.token_to_id[token] = new_id
            self.id_to_token[new_id] = token

        self.frequencies[token] = self.frequencies.get(token, 0) + 1
        return self.token_to_id[token]

    def get_id(self, token: str) -> int:
        return self.token_to_id.get(token, self.token_to_id["<UNK>"])

    def get_token(self, token_id: int) -> str:
        return self.id_to_token.get(token_id, "<UNK>")

    @property
    def size(self) -> int:
        return len(self.token_to_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "token_to_id": self.token_to_id,
            "id_to_token": {str(k): v for k, v in self.id_to_token.items()},
            "frequencies": self.frequencies,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Vocabulary:
        vocab = cls()
        vocab.token_to_id = data.get("token_to_id", {})
        vocab.id_to_token = {int(k): v for k, v in data.get("id_to_token", {}).items()}
        vocab.frequencies = data.get("frequencies", {})
        return vocab


class BehavioralEncoder:
    EMBEDDING_DIM = 128

    ACTION_FEATURES = [
        "action_type",
        "target_app",
        "time_of_day",
        "day_of_week",
        "time_since_last",
        "typing_burst",
        "mouse_distance",
        "scroll_direction",
    ]

    def __init__(
        self,
        embedding_dim: int = EMBEDDING_DIM,
        max_sequence_length: int = 100,
    ):
        self.embedding_dim = embedding_dim
        self.max_sequence_length = max_sequence_length

        self.action_vocab = Vocabulary()
        self.app_vocab = Vocabulary()
        self.hotkey_vocab = Vocabulary()

        self._action_embeddings: dict[str, np.ndarray] = {}
        self._app_embeddings: dict[str, np.ndarray] = {}

        self._init_base_embeddings()

    def _init_base_embeddings(self) -> None:
        base_actions = [
            "click",
            "double_click",
            "right_click",
            "key_press",
            "key_type",
            "hotkey",
            "scroll_up",
            "scroll_down",
            "mouse_move",
            "drag",
            "window_change",
            "screenshot",
        ]

        for action in base_actions:
            self.action_vocab.add_token(action)
            self._action_embeddings[action] = self._generate_deterministic_embedding(
                f"action:{action}"
            )

    def _generate_deterministic_embedding(self, seed_string: str) -> np.ndarray:
        hash_bytes = hashlib.sha256(seed_string.encode()).digest()

        values = []
        for i in range(0, min(len(hash_bytes), self.embedding_dim * 4), 4):
            val = int.from_bytes(hash_bytes[i : i + 4], "little", signed=True)
            values.append(val / (2**31))

        while len(values) < self.embedding_dim:
            extra_hash = hashlib.sha256(f"{seed_string}:{len(values)}".encode()).digest()
            for i in range(0, min(len(extra_hash), (self.embedding_dim - len(values)) * 4), 4):
                val = int.from_bytes(extra_hash[i : i + 4], "little", signed=True)
                values.append(val / (2**31))

        embedding = np.array(values[: self.embedding_dim], dtype=np.float32)
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding

    def encode_action(self, event: dict[str, Any]) -> ActionEmbedding:
        action_type = event.get("action_type", "unknown")
        app = event.get("window_app", "unknown").lower()
        timestamp = event.get("timestamp", time.time())
        data = event.get("data", {})

        components = []

        if action_type in self._action_embeddings:
            components.append(self._action_embeddings[action_type])
        else:
            self.action_vocab.add_token(action_type)
            embedding = self._generate_deterministic_embedding(f"action:{action_type}")
            self._action_embeddings[action_type] = embedding
            components.append(embedding)

        if app in self._app_embeddings:
            components.append(self._app_embeddings[app])
        else:
            self.app_vocab.add_token(app)
            embedding = self._generate_deterministic_embedding(f"app:{app}")
            self._app_embeddings[app] = embedding
            components.append(embedding)

        time_embedding = self._encode_time(timestamp)
        components.append(time_embedding)

        action_specific = self._encode_action_specific(action_type, data)
        components.append(action_specific)

        combined = np.mean(components, axis=0)
        norm = np.linalg.norm(combined)
        if norm > 0:
            combined = combined / norm

        return ActionEmbedding(
            event_id=event.get("id", str(hash(json.dumps(event, default=str)))),
            vector=combined.tolist(),
            action_type=action_type,
            app_context=app,
            timestamp=timestamp,
        )

    def _encode_time(self, timestamp: float) -> np.ndarray:
        local_time = time.localtime(timestamp)
        hour = local_time.tm_hour
        day_of_week = local_time.tm_wday

        embedding = np.zeros(self.embedding_dim, dtype=np.float32)

        hour_sin = math.sin(2 * math.pi * hour / 24)
        hour_cos = math.cos(2 * math.pi * hour / 24)
        day_sin = math.sin(2 * math.pi * day_of_week / 7)
        day_cos = math.cos(2 * math.pi * day_of_week / 7)

        quarter = self.embedding_dim // 4
        embedding[:quarter] = hour_sin
        embedding[quarter : 2 * quarter] = hour_cos
        embedding[2 * quarter : 3 * quarter] = day_sin
        embedding[3 * quarter :] = day_cos

        return embedding

    def _encode_action_specific(
        self,
        action_type: str,
        data: dict[str, Any],
    ) -> np.ndarray:
        embedding = np.zeros(self.embedding_dim, dtype=np.float32)

        if action_type == "click":
            x = data.get("x", 0)
            y = data.get("y", 0)
            embedding[0] = x / 3000.0
            embedding[1] = y / 2000.0
            embedding[2] = 1.0 if data.get("button") == "left" else -1.0

        elif action_type in ("key_type", "key_press"):
            text = data.get("text", "")
            embedding[0] = len(text) / 100.0
            duration = data.get("duration_ms", 0)
            embedding[1] = min(duration / 10000.0, 1.0)

            if text:
                char_hash = sum(ord(c) for c in text[:20])
                embedding[2] = (char_hash % 1000) / 1000.0

        elif action_type == "hotkey":
            keys = data.get("keys", [])
            embedding[0] = len(keys) / 5.0
            key_hash = hash(tuple(sorted(keys))) % 10000
            embedding[1] = key_hash / 10000.0

        elif action_type in ("scroll_up", "scroll_down"):
            clicks = abs(data.get("clicks", 0))
            embedding[0] = min(clicks / 10.0, 1.0)
            embedding[1] = 1.0 if action_type == "scroll_up" else -1.0

        elif action_type == "mouse_move":
            dx = data.get("dx", 0)
            dy = data.get("dy", 0)
            distance = math.sqrt(dx * dx + dy * dy)
            embedding[0] = min(distance / 1000.0, 1.0)
            embedding[1] = math.atan2(dy, dx) / math.pi

        return embedding

    def encode_sequence(
        self,
        events: Sequence[dict[str, Any]],
        sequence_id: str | None = None,
    ) -> SequenceEmbedding:
        if not events:
            return SequenceEmbedding(
                sequence_id=sequence_id or "empty",
                vector=[0.0] * self.embedding_dim,
            )

        action_embeddings = [self.encode_action(e) for e in events[: self.max_sequence_length]]

        vectors = np.array([ae.vector for ae in action_embeddings])

        mean_vector = np.mean(vectors, axis=0)

        if len(vectors) > 1:
            temporal_weights = np.linspace(0.5, 1.0, len(vectors))
            temporal_weights = temporal_weights / temporal_weights.sum()
            weighted_vector = np.average(vectors, axis=0, weights=temporal_weights)
        else:
            weighted_vector = mean_vector

        combined = (mean_vector + weighted_vector) / 2
        norm = np.linalg.norm(combined)
        if norm > 0:
            combined = combined / norm

        app_counts: dict[str, int] = defaultdict(int)
        for ae in action_embeddings:
            app_counts[ae.app_context] += 1
        dominant_app = max(app_counts, key=app_counts.get) if app_counts else ""

        if len(events) >= 2:
            duration = events[-1].get("timestamp", 0) - events[0].get("timestamp", 0)
        else:
            duration = 0.0

        return SequenceEmbedding(
            sequence_id=sequence_id
            or hashlib.md5(json.dumps([e.get("id", "") for e in events]).encode()).hexdigest()[:16],
            vector=combined.tolist(),
            action_count=len(events),
            duration_seconds=duration,
            dominant_app=dominant_app,
        )

    def encode_batch(
        self,
        event_batches: Sequence[Sequence[dict[str, Any]]],
    ) -> list[SequenceEmbedding]:
        return [
            self.encode_sequence(events, f"batch_{i}") for i, events in enumerate(event_batches)
        ]

    def find_similar_sequences(
        self,
        query_embedding: SequenceEmbedding,
        candidates: Sequence[SequenceEmbedding],
        top_k: int = 5,
    ) -> list[tuple[SequenceEmbedding, float]]:
        query_vec = np.array(query_embedding.vector)

        similarities = []
        for candidate in candidates:
            candidate_vec = np.array(candidate.vector)

            norm_q = np.linalg.norm(query_vec)
            norm_c = np.linalg.norm(candidate_vec)

            if norm_q > 0 and norm_c > 0:
                sim = float(np.dot(query_vec, candidate_vec) / (norm_q * norm_c))
            else:
                sim = 0.0

            similarities.append((candidate, sim))

        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    def get_vocabulary_stats(self) -> dict[str, Any]:
        return {
            "action_vocab_size": self.action_vocab.size,
            "app_vocab_size": self.app_vocab.size,
            "hotkey_vocab_size": self.hotkey_vocab.size,
            "embedding_dim": self.embedding_dim,
            "top_actions": sorted(
                self.action_vocab.frequencies.items(),
                key=lambda x: x[1],
                reverse=True,
            )[:10],
            "top_apps": sorted(
                self.app_vocab.frequencies.items(),
                key=lambda x: x[1],
                reverse=True,
            )[:10],
        }

    def save_vocabularies(self, path: str) -> None:
        data = {
            "action_vocab": self.action_vocab.to_dict(),
            "app_vocab": self.app_vocab.to_dict(),
            "hotkey_vocab": self.hotkey_vocab.to_dict(),
            "embedding_dim": self.embedding_dim,
        }
        with open(path, "w") as f:
            json.dump(data, f)

    def load_vocabularies(self, path: str) -> None:
        with open(path) as f:
            data = json.load(f)

        self.action_vocab = Vocabulary.from_dict(data.get("action_vocab", {}))
        self.app_vocab = Vocabulary.from_dict(data.get("app_vocab", {}))
        self.hotkey_vocab = Vocabulary.from_dict(data.get("hotkey_vocab", {}))

        for token in self.action_vocab.token_to_id:
            if token not in self._action_embeddings:
                self._action_embeddings[token] = self._generate_deterministic_embedding(
                    f"action:{token}"
                )

        for token in self.app_vocab.token_to_id:
            if token not in self._app_embeddings:
                self._app_embeddings[token] = self._generate_deterministic_embedding(f"app:{token}")
