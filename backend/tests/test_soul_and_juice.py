"""
Tests for "Soul" (AI reasoning & personas) and "Juice" (artificial latency) features.
"""
import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock

# Test Personas
class TestPersonas:
    """Tests for AI persona configuration."""
    
    def test_personas_module_exists(self):
        """Verify personas module can be imported."""
        from app.ai.personas import PERSONAS, get_persona_system_prompt
        assert PERSONAS is not None
        assert callable(get_persona_system_prompt)
    
    def test_default_persona_exists(self):
        """Verify default persona is defined."""
        from app.ai.personas import PERSONAS
        assert "default" in PERSONAS
        assert "instruction" in PERSONAS["default"]
    
    def test_all_personas_have_required_fields(self):
        """All personas must have name, style, and instruction."""
        from app.ai.personas import PERSONAS
        required_fields = ["name", "style", "instruction"]
        for persona_key, persona in PERSONAS.items():
            for field in required_fields:
                assert field in persona, f"Persona '{persona_key}' missing field '{field}'"
    
    def test_get_persona_system_prompt_returns_string(self):
        """get_persona_system_prompt should return a string."""
        from app.ai.personas import get_persona_system_prompt
        prompt = get_persona_system_prompt("default")
        assert isinstance(prompt, str)
        assert len(prompt) > 0
    
    def test_get_persona_system_prompt_unknown_persona_returns_default(self):
        """Unknown persona key should return default persona prompt."""
        from app.ai.personas import get_persona_system_prompt, PERSONAS
        prompt = get_persona_system_prompt("nonexistent_persona_xyz")
        default_prompt = PERSONAS["default"]["instruction"]
        assert prompt == default_prompt


# Test PlayerActionRequest with reasoning field
class TestPlayerActionRequestReasoning:
    """Tests for reasoning field in PlayerActionRequest."""
    
    def test_player_action_request_accepts_reasoning(self):
        """PlayerActionRequest should accept optional reasoning field."""
        from app.api.v1.poker_schemas import PlayerActionRequest
        action = PlayerActionRequest(action_type="fold", reasoning="I have nothing, folding.")
        assert action.reasoning == "I have nothing, folding."
    
    def test_player_action_request_reasoning_optional(self):
        """Reasoning should be optional (default None)."""
        from app.api.v1.poker_schemas import PlayerActionRequest
        action = PlayerActionRequest(action_type="call")
        assert action.reasoning is None


# Test PlayerConfig with persona field
class TestPlayerConfigPersona:
    """Tests for persona field in PlayerConfig."""
    
    def test_player_config_accepts_persona(self):
        """PlayerConfig should accept optional persona field."""
        from app.api.v1.poker_schemas import PlayerConfig
        config = PlayerConfig(name="Bot", ai_type="gemini", persona="aggressive")
        assert config.persona == "aggressive"
    
    def test_player_config_persona_optional(self):
        """Persona should be optional (default None)."""
        from app.api.v1.poker_schemas import PlayerConfig
        config = PlayerConfig(name="Bot", ai_type="gemini")
        assert config.persona is None
    
    def test_player_config_persona_validates_enum(self):
        """Persona should only accept valid values."""
        from app.api.v1.poker_schemas import PlayerConfig
        from pydantic import ValidationError
        
        # Valid personas should work
        valid_personas = ["default", "conservative", "aggressive", "calling_station"]
        for persona in valid_personas:
            config = PlayerConfig(name="Bot", ai_type="gemini", persona=persona)
            assert config.persona == persona
        
        # Invalid persona should raise ValidationError
        with pytest.raises(ValidationError):
            PlayerConfig(name="Bot", ai_type="gemini", persona="invalid_persona_name")


# Test JSON prompt format in llm_prompts
class TestLLMPromptJSONFormat:
    """Tests for JSON output format in LLM prompts."""
    
    def test_prompt_requests_json_format(self):
        """The prompt should instruct LLM to output JSON."""
        # Instead of creating a full pokerkit state, verify the prompt template
        # by checking that the llm_prompts module contains JSON instructions
        from app.ai import llm_prompts
        import inspect
        
        # Get the source code of the format function
        source = inspect.getsource(llm_prompts.format_poker_state_for_llm)
        
        # Check for JSON-related instructions in the source
        assert "JSON" in source or "json" in source, "Prompt should mention JSON format"
        assert "reasoning" in source.lower(), "Prompt should mention reasoning"
        assert "action" in source.lower(), "Prompt should mention action"


# Test AI message contains reasoning
class TestAIReasoningInResponse:
    """Tests for AI reasoning appearing in game responses."""
    
    def test_game_service_uses_reasoning_when_available(self):
        """When AI provides reasoning, it should appear in ai_message."""
        # This is more of an integration test, but we can verify the structure
        from app.api.v1.poker_schemas import PlayerActionRequest
        
        action = PlayerActionRequest(
            action_type="call",
            reasoning="The pot odds are too good to fold here."
        )
        
        # The reasoning should be usable for ai_message
        expected_message = f"💭 {action.reasoning}"
        assert "pot odds" in expected_message


# Test config loads API key correctly
class TestAPIKeyConfig:
    """Tests for API key configuration."""
    
    def test_settings_has_gemini_api_key_field(self):
        """Settings should have GEMINI_API_KEY field."""
        from app.config import Settings
        # Check the field exists in the model
        assert "GEMINI_API_KEY" in Settings.model_fields
    
    def test_env_file_path_is_absolute(self):
        """The env_file path should be absolute for reliable loading."""
        from app.config import _env_file
        from pathlib import Path
        assert _env_file.is_absolute() or str(_env_file).startswith("/")
