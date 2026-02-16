"""Tests for the Digital Twin core module."""

import pytest
import tempfile
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from mnemosyne.twin.core import DigitalTwin, TwinConfig, TwinState, ReplicationMetrics
from mnemosyne.twin.profile import UserProfile, UserPreferences, WorkPattern
from mnemosyne.twin.encoder import BehavioralEncoder, ActionEmbedding
from mnemosyne.twin.predictor import IntentPredictor, PredictionResult
from mnemosyne.twin.active_learner import ActiveLearner, LearningQuestion


class TestTwinConfig:
    def test_default_config(self):
        config = TwinConfig()
        assert config.learning_enabled is True
        assert config.active_questioning_enabled is True
        assert config.max_questions_per_hour == 5
        assert config.uncertainty_threshold == 0.6

    def test_custom_config(self):
        config = TwinConfig(
            max_questions_per_hour=10,
            uncertainty_threshold=0.8,
            learning_enabled=False,
        )
        assert config.max_questions_per_hour == 10
        assert config.uncertainty_threshold == 0.8
        assert config.learning_enabled is False


class TestReplicationMetrics:
    def test_default_metrics(self):
        metrics = ReplicationMetrics()
        assert metrics.action_prediction_accuracy == 0.0
        assert metrics.total_predictions == 0
        assert metrics.overall_replication_score == 0.0

    def test_replication_score_calculation(self):
        metrics = ReplicationMetrics(
            action_prediction_accuracy=0.8,
            intent_prediction_accuracy=0.7,
            pattern_recognition_rate=0.6,
            timing_accuracy=0.5,
        )
        score = metrics.overall_replication_score
        expected = 0.8 * 0.35 + 0.7 * 0.25 + 0.6 * 0.25 + 0.5 * 0.15
        assert abs(score - expected) < 0.001


class TestBehavioralEncoder:
    def test_encoder_initialization(self):
        encoder = BehavioralEncoder(embedding_dim=64)
        assert encoder.embedding_dim == 64

    def test_vocabulary_stats(self):
        encoder = BehavioralEncoder(embedding_dim=64)
        stats = encoder.get_vocabulary_stats()
        assert "action_vocab_size" in stats
        assert "app_vocab_size" in stats

    def test_action_encoding(self):
        encoder = BehavioralEncoder(embedding_dim=64)
        event = {"action_type": "click", "window_app": "VS Code", "timestamp": 1.0}
        embedding = encoder.encode_action(event)
        assert isinstance(embedding, ActionEmbedding)
        assert len(embedding.vector) == 64


class TestIntentPredictor:
    def test_predictor_initialization(self):
        encoder = BehavioralEncoder(embedding_dim=64)
        predictor = IntentPredictor(encoder=encoder)
        stats = predictor.get_prediction_stats()
        assert stats["sequence_patterns"] == 0

    def test_pattern_learning(self):
        encoder = BehavioralEncoder(embedding_dim=64)
        predictor = IntentPredictor(encoder=encoder)

        context = [
            {"action_type": "click", "window_app": "VS Code"},
            {"action_type": "type", "window_app": "VS Code"},
        ]
        next_action = "scroll"

        predictor.learn_pattern(context, next_action)
        stats = predictor.get_prediction_stats()
        assert stats["sequence_patterns"] >= 1

    def test_prediction(self):
        encoder = BehavioralEncoder(embedding_dim=64)
        predictor = IntentPredictor(encoder=encoder)

        context = [
            {"action_type": "click", "window_app": "VS Code"},
        ]

        result = predictor.predict_next_action(context, {}, None)
        assert isinstance(result, PredictionResult)
        assert result.predicted_action is not None


class TestActiveLearner:
    def test_learner_initialization(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            learner = ActiveLearner(data_dir=Path(tmpdir))
            stats = learner.get_learning_stats()
            assert stats["pending_questions"] == 0

    def test_uncertainty_detection(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            learner = ActiveLearner(data_dir=Path(tmpdir))

            events = [
                {"action_type": "click", "window_app": "App1", "timestamp": 1.0},
                {"action_type": "click", "window_app": "App2", "timestamp": 2.0},
                {"action_type": "click", "window_app": "App3", "timestamp": 3.0},
            ]

            uncertainties = learner.detect_uncertainty(events)
            assert isinstance(uncertainties, list)


class TestUserProfile:
    def test_profile_creation(self):
        profile = UserProfile()
        assert profile.preferences is not None
        assert profile.profile_completeness == 0.0

    def test_preferences(self):
        prefs = UserPreferences(
            preferred_apps_by_task={"coding": ["VS Code", "Terminal"]},
        )
        assert len(prefs.preferred_apps_by_task["coding"]) == 2


class TestDigitalTwin:
    @pytest.fixture
    def mock_database(self):
        db = MagicMock()
        db.list_sessions.return_value = []
        db.iter_events.return_value = iter([])
        return db

    @pytest.fixture
    def mock_memory(self):
        return MagicMock()

    def test_twin_initialization(self, mock_database, mock_memory):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = TwinConfig(data_dir=Path(tmpdir) / "twin")
            twin = DigitalTwin(
                database=mock_database,
                memory=mock_memory,
                config=config,
            )
            assert twin.state == TwinState.INITIALIZING

    @pytest.mark.asyncio
    async def test_twin_initialize(self, mock_database, mock_memory):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = TwinConfig(data_dir=Path(tmpdir) / "twin")
            twin = DigitalTwin(
                database=mock_database,
                memory=mock_memory,
                config=config,
            )
            await twin.initialize()
            assert twin.state == TwinState.READY

    @pytest.mark.asyncio
    async def test_observe_event(self, mock_database, mock_memory):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = TwinConfig(data_dir=Path(tmpdir) / "twin")
            twin = DigitalTwin(
                database=mock_database,
                memory=mock_memory,
                config=config,
            )
            await twin.initialize()

            for i in range(6):
                event = {
                    "id": f"evt_{i}",
                    "action_type": "click",
                    "window_app": "VS Code",
                    "timestamp": time.time() + i,
                }
                result = await twin.observe_event(event)

            assert len(twin._event_buffer) >= 5

    def test_get_status(self, mock_database, mock_memory):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = TwinConfig(data_dir=Path(tmpdir) / "twin")
            twin = DigitalTwin(
                database=mock_database,
                memory=mock_memory,
                config=config,
            )

            status = twin.get_status()
            assert "state" in status
            assert "replication_score" in status
            assert "metrics" in status

    def test_get_improvement_suggestions(self, mock_database, mock_memory):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = TwinConfig(data_dir=Path(tmpdir) / "twin")
            twin = DigitalTwin(
                database=mock_database,
                memory=mock_memory,
                config=config,
            )

            suggestions = twin.get_improvement_suggestions()
            assert isinstance(suggestions, list)
            assert len(suggestions) > 0
