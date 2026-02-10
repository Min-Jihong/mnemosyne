import pytest
from mnemosyne.execute.safety import SafetyGuard, SafetyConfig


class TestSafetyGuard:
    
    def test_default_config(self):
        guard = SafetyGuard()
        
        assert guard.config.enabled is True
        assert guard.config.max_actions_per_minute == 60
    
    def test_blocked_app(self):
        guard = SafetyGuard()
        
        allowed, reason = guard.check_action(
            action_type="click",
            target_app="Terminal",
        )
        
        assert allowed is False
        assert "protected application" in reason
    
    def test_allowed_app(self):
        guard = SafetyGuard()
        
        allowed, reason = guard.check_action(
            action_type="click",
            target_app="Safari",
        )
        
        assert allowed is True
    
    def test_blocked_hotkey(self):
        guard = SafetyGuard()
        
        allowed, reason = guard.check_action(
            action_type="hotkey",
            keys=["cmd", "q"],
        )
        
        assert allowed is False
        assert "protected hotkey" in reason
    
    def test_safe_zone(self):
        config = SafetyConfig(safe_zone=(100, 100, 200, 200))
        guard = SafetyGuard(config=config)
        
        allowed_inside, _ = guard.check_action(
            action_type="click",
            position=(150, 150),
        )
        assert allowed_inside is True
        
        allowed_outside, reason = guard.check_action(
            action_type="click",
            position=(50, 50),
        )
        assert allowed_outside is False
        assert "outside safe zone" in reason
    
    def test_rate_limit(self):
        config = SafetyConfig(max_actions_per_minute=3)
        guard = SafetyGuard(config=config)
        
        for i in range(3):
            allowed, _ = guard.check_action(action_type="click")
            assert allowed is True
        
        allowed, reason = guard.check_action(action_type="click")
        assert allowed is False
        assert "rate limit" in reason
    
    def test_pause_resume(self):
        guard = SafetyGuard()
        
        guard.pause()
        allowed, reason = guard.check_action(action_type="click")
        assert allowed is False
        assert "paused" in reason
        
        guard.resume()
        allowed, _ = guard.check_action(action_type="click")
        assert allowed is True
    
    def test_emergency_stop(self):
        guard = SafetyGuard()
        
        guard.check_action(action_type="click")
        guard.check_action(action_type="click")
        
        guard.emergency_stop()
        
        allowed, _ = guard.check_action(action_type="click")
        assert allowed is False
    
    def test_add_remove_blocked_app(self):
        guard = SafetyGuard()
        
        guard.add_blocked_app("CustomApp")
        allowed, _ = guard.check_action(
            action_type="click",
            target_app="CustomApp",
        )
        assert allowed is False
        
        guard.remove_blocked_app("CustomApp")
        allowed, _ = guard.check_action(
            action_type="click",
            target_app="CustomApp",
        )
        assert allowed is True
    
    def test_disabled_guard(self):
        config = SafetyConfig(enabled=False)
        guard = SafetyGuard(config=config)
        
        allowed, _ = guard.check_action(
            action_type="click",
            target_app="Terminal",
        )
        assert allowed is True
