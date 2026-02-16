"""
Digital Twin Core Module.

This module provides the core functionality for creating a digital twin
that can learn and replicate user behavior with high fidelity.

Key components:
- UserProfile: Personalized model of user preferences and habits
- BehavioralEncoder: Action sequence encoding for pattern recognition
- IntentPredictor: Context-aware intent prediction
- ActiveLearner: Smart questioning system for rapid learning
- DigitalTwin: Main orchestrator for the digital twin system
"""

from mnemosyne.twin.profile import UserProfile, UserPreferences, WorkPattern
from mnemosyne.twin.encoder import BehavioralEncoder, ActionEmbedding
from mnemosyne.twin.predictor import IntentPredictor, PredictionResult
from mnemosyne.twin.active_learner import ActiveLearner, LearningQuestion
from mnemosyne.twin.core import DigitalTwin, TwinConfig

__all__ = [
    "UserProfile",
    "UserPreferences",
    "WorkPattern",
    "BehavioralEncoder",
    "ActionEmbedding",
    "IntentPredictor",
    "PredictionResult",
    "ActiveLearner",
    "LearningQuestion",
    "DigitalTwin",
    "TwinConfig",
]
