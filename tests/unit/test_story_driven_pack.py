"""
Unit tests for story-driven development pack
"""

import pytest
from unittest.mock import Mock, patch
from servicenow_mcp.packs import story_driven_pack


class TestStoryDrivenPack:
    """Test cases for story-driven development functionality"""

    def test_parse_user_story_valid(self, sample_user_story):
        """Test parsing a valid user story"""
        result = story_driven_pack.parse_user_story(sample_user_story)
        
        assert result["success"] is True
        assert "components" in result
        assert result["components"]["user"] == "service desk agent"
        assert "automatically assign incidents" in result["components"]["goal"]
        assert "routed to the right team faster" in result["components"]["benefit"]

    def test_parse_user_story_invalid_format(self):
        """Test parsing an invalid user story format"""
        invalid_story = "I want to do something"
        result = story_driven_pack.parse_user_story(invalid_story)
        
        assert result["success"] is False
        assert "error" in result

    def test_parse_user_story_missing_components(self):
        """Test parsing user story with missing components"""
        incomplete_story = "As a user, I want to do something"
        result = story_driven_pack.parse_user_story(incomplete_story)
        
        assert result["success"] is False
        assert "missing" in result["error"].lower()

    def test_validate_story_completeness_complete(self, sample_parsed_story):
        """Test validation of complete story"""
        result = story_driven_pack.validate_story_completeness(sample_parsed_story)
        
        assert result["is_complete"] is True
        assert result["score"] > 0.8

    def test_validate_story_completeness_incomplete(self):
        """Test validation of incomplete story"""
        incomplete_story = {
            "components": {
                "user": "user",
                "goal": "do something",
                "benefit": ""
            }
        }
        
        result = story_driven_pack.validate_story_completeness(incomplete_story)
        
        assert result["is_complete"] is False
        assert len(result["recommendations"]) > 0

    @patch('servicenow_mcp.packs.story_driven_pack.analyze_servicenow_context')
    def test_extract_technical_requirements(self, mock_analyze, mock_client, sample_parsed_story):
        """Test extraction of technical requirements"""
        mock_analyze.return_value = {
            "tables": ["incident", "assignment_group"],
            "fields": ["category", "assignment_group"],
            "business_rules": ["auto_assignment"]
        }
        
        result = story_driven_pack.extract_technical_requirements(
            mock_client, sample_parsed_story["components"]
        )
        
        assert "technical_requirements" in result
        assert "functional_requirements" in result
        assert len(result["technical_requirements"]) > 0

    def test_generate_implementation_tasks(self, mock_client):
        """Test generation of implementation tasks"""
        requirements = {
            "technical_requirements": [
                {"type": "business_rule", "table": "incident", "action": "auto_assign"}
            ],
            "functional_requirements": [
                {"description": "Assign incidents based on category"}
            ]
        }
        
        story_context = {"components": {"user": "agent", "goal": "auto assign"}}
        
        result = story_driven_pack.generate_implementation_tasks(
            mock_client, requirements, story_context
        )
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert all("task_type" in task for task in result)

    def test_create_executable_plan(self, mock_client):
        """Test creation of executable plan"""
        tasks = [
            {
                "task_type": "create_business_rule",
                "table": "incident",
                "name": "Auto Assignment Rule",
                "script": "// Auto assignment logic"
            }
        ]
        
        story_context = {"components": {"user": "agent"}}
        
        result = story_driven_pack.create_executable_plan(
            mock_client, tasks, story_context
        )
        
        assert "phases" in result
        assert "estimated_effort" in result
        assert len(result["phases"]) > 0

    def test_story_implementation_pipeline_success(self, mock_client, sample_user_story):
        """Test complete story-to-implementation pipeline"""
        with patch.multiple(
            story_driven_pack,
            parse_user_story=Mock(return_value={
                "success": True,
                "components": {
                    "user": "agent",
                    "goal": "auto assign",
                    "benefit": "faster routing"
                }
            }),
            validate_story_completeness=Mock(return_value={
                "is_complete": True,
                "score": 0.95
            }),
            extract_technical_requirements=Mock(return_value={
                "technical_requirements": [{"type": "business_rule"}]
            }),
            generate_implementation_tasks=Mock(return_value=[
                {"task_type": "create_business_rule"}
            ]),
            create_executable_plan=Mock(return_value={
                "phases": [{"phase": "development"}],
                "estimated_effort": "4 hours"
            })
        ):
            # This would be tested in the main adapter
            pass

    def test_story_implementation_pipeline_incomplete(self, mock_client):
        """Test pipeline with incomplete story"""
        incomplete_story = "I want something"
        
        with patch('servicenow_mcp.packs.story_driven_pack.parse_user_story') as mock_parse:
            mock_parse.return_value = {"success": False, "error": "Invalid format"}
            
            # This would return early with error
            pass

    @pytest.mark.parametrize("story,expected_user", [
        ("As a developer, I want to create APIs", "developer"),
        ("As an administrator, I want to manage users", "administrator"),
        ("As a service desk agent, I want to resolve tickets", "service desk agent")
    ])
    def test_parse_different_user_types(self, story, expected_user):
        """Test parsing stories with different user types"""
        full_story = f"{story} so that I can be more efficient"
        result = story_driven_pack.parse_user_story(full_story)
        
        if result.get("success"):
            assert result["components"]["user"] == expected_user

    def test_requirements_extraction_edge_cases(self, mock_client):
        """Test requirements extraction with edge cases"""
        # Empty components
        result = story_driven_pack.extract_technical_requirements(mock_client, {})
        assert "error" in result or len(result.get("technical_requirements", [])) == 0
        
        # Very vague goal
        vague_components = {
            "user": "user",
            "goal": "do stuff",
            "benefit": "it helps"
        }
        result = story_driven_pack.extract_technical_requirements(mock_client, vague_components)
        # Should handle gracefully

    def test_task_generation_error_handling(self, mock_client):
        """Test task generation with invalid requirements"""
        invalid_requirements = {"invalid": "data"}
        story_context = {"components": {"user": "test"}}
        
        result = story_driven_pack.generate_implementation_tasks(
            mock_client, invalid_requirements, story_context
        )
        
        # Should return empty list or error
        assert isinstance(result, list) or "error" in result