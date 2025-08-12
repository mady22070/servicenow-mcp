"""
Basic unit tests to verify core functionality
"""

import pytest
from servicenow_mcp.packs import story_driven_pack


class TestBasicFunctionality:
    """Basic tests that should always pass"""

    def test_parse_valid_user_story(self):
        """Test parsing a simple valid user story"""
        story = "As a service desk agent, I want to automatically assign incidents based on category so that tickets are routed to the right team faster"
        result = story_driven_pack.parse_user_story(story)
        
        assert result["success"] is True
        assert "components" in result
        assert result["components"]["user"] == "service desk agent"
        assert "automatically assign incidents" in result["components"]["goal"]

    def test_parse_invalid_user_story(self):
        """Test parsing an invalid user story"""
        story = "I want to do something"
        result = story_driven_pack.parse_user_story(story)
        
        assert result["success"] is False
        assert "error" in result

    def test_validate_complete_story(self):
        """Test validation of a complete story"""
        story_analysis = {
            "components": {
                "user": "service desk agent",
                "goal": "automatically assign incidents based on category",
                "benefit": "tickets are routed to the right team faster"
            }
        }
        
        result = story_driven_pack.validate_story_completeness(story_analysis)
        
        assert result["is_complete"] is True
        assert result["score"] > 0.8

    def test_validate_incomplete_story(self):
        """Test validation of an incomplete story"""
        story_analysis = {
            "components": {
                "user": "user",
                "goal": "do something",
                "benefit": ""
            }
        }
        
        result = story_driven_pack.validate_story_completeness(story_analysis)
        
        assert result["is_complete"] is False
        assert len(result["recommendations"]) > 0

    def test_module_imports(self):
        """Test that all required modules can be imported"""
        from servicenow_mcp.packs import story_driven_pack
        from servicenow_mcp import config
        from servicenow_mcp import version
        
        # Basic smoke test
        assert hasattr(story_driven_pack, 'parse_user_story')
        assert hasattr(story_driven_pack, 'validate_story_completeness')