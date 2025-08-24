"""
Unit tests for story-driven development pack
"""

import pytest
from unittest.mock import Mock, patch
from servicenow_mcp.packs import story_driven_pack

@pytest.fixture
def sample_parsed_story(sample_user_story):
    """Provide a parsed version of the sample user story."""
    return story_driven_pack.parse_user_story(sample_user_story)


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

    def test_extract_technical_requirements(self, mock_servicenow_client, sample_parsed_story):
        """Test extraction of technical requirements"""
        result = story_driven_pack.extract_technical_requirements(
            mock_servicenow_client, sample_parsed_story["components"]
        )
        
        assert isinstance(result, dict)
        # The function returns a dict with requirement categories
        assert "technical_requirements" in result
        assert "functional_requirements" in result


    def test_generate_implementation_tasks(self, mock_servicenow_client):
        """Test generation of implementation tasks"""
        requirements = {
            "data_model": ["New table or fields may be required"],
            "business_logic": ["Business rules or script includes needed"]
        }
        
        story_context = {"components": {"user": "agent", "goal": "auto assign"}}
        
        result = story_driven_pack.generate_implementation_tasks(
            mock_servicenow_client, requirements, story_context
        )
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert all("phase" in task for task in result)

    def test_create_executable_plan(self, mock_servicenow_client):
        """Test creation of executable plan"""
        tasks = [
            {
                "phase": "development",
                "type": "implementation",
                "title": "Create business rules",
                "description": "Implement server-side business logic",
                "pack": "scripts",
                "function": "create_business_rule",
                "estimated_hours": 3,
                "dependencies": ["data_model_changes"]
            }
        ]
        
        story_context = {"components": {"user": "agent", "goal": "create a new incident table"}}
        
        result = story_driven_pack.create_executable_plan(
            mock_servicenow_client, tasks, story_context
        )
        
        assert "phases" in result
        assert "total_estimated_hours" in result
        assert len(result["execution_steps"]) > 0

    def test_story_implementation_pipeline_success(self, mock_servicenow_client, sample_user_story):
        """Test complete story-to-implementation pipeline"""
        # This is a complex integration test, for now we just check it doesn't crash
        # A more detailed test would involve mocking each step and checking the output
        result = story_driven_pack.story_to_implementation(mock_servicenow_client, sample_user_story)
        assert result['status'] == 'success'
        assert 'executable_plan' in result

    def test_story_implementation_pipeline_incomplete(self, mock_servicenow_client):
        """Test pipeline with incomplete story"""
        incomplete_story = "I want something"
        result = story_driven_pack.story_to_implementation(mock_servicenow_client, incomplete_story)
        assert result['status'] == 'error'
        assert result['stage'] == 'parsing'


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

    def test_requirements_extraction_edge_cases(self, mock_servicenow_client):
        """Test requirements extraction with edge cases"""
        # Empty components
        result = story_driven_pack.extract_technical_requirements(mock_servicenow_client, {})
        assert "error" in result
        
        # Very vague goal
        vague_components = {
            "user": "user",
            "goal": "do stuff",
            "benefit": "it helps"
        }
        result = story_driven_pack.extract_technical_requirements(mock_servicenow_client, vague_components)
        assert isinstance(result, dict)  # Should handle gracefully

    def test_task_generation_error_handling(self, mock_servicenow_client):
        """Test task generation with invalid requirements"""
        invalid_requirements = {"invalid": "data"}
        story_context = {"components": {"user": "test"}}
        
        result = story_driven_pack.generate_implementation_tasks(
            mock_servicenow_client, invalid_requirements, story_context
        )
        
        # Should return empty list or error
        assert isinstance(result, list)

    @pytest.mark.parametrize("goal, expected_name", [
        ("to create a new table for tracking widgets", "widget"),
        ("to manage service requests from users", "request"),
        ("I want to store all the new incidents", "incident"),
        ("be able to log all security problems", "problem"),
        ("a form to submit change requests", "request"),
        ("track all the company assets", "asset"),
        ("manage configuration items", "item"),
        ("create a new doodad", "doodad"),
        ("track all the foobars", "foobar"),
        ("I want to make a thing", "thing"),
        ("a very complex process", "process"),
        ("", "custom_table"),
        ("a goal with no nouns", "noun"),
    ])
    def test_extract_table_name_from_goal(self, goal, expected_name):
        """Test the improved logic for extracting table names from goals"""
        result = story_driven_pack.extract_table_name_from_goal(goal)
        assert result == expected_name

    def test_plan_generation_uses_consistent_table_name(self, mock_servicenow_client):
        """Test that generated plan uses the same dynamic table name for all relevant steps"""
        # This story should result in a 'widget' table
        story = "As a user, I want to create a table for widgets so that I can track them"
        parsed_story = story_driven_pack.parse_user_story(story)

        # Manually create the requirements and tasks that would be generated
        requirements = {
            "data_model": ["New table or fields may be required"],
            "business_logic": ["Business rules or script includes needed"]
        }

        # We need a TaskGenerator to create the tasks in the same way the real code does
        task_generator = story_driven_pack.TaskGenerator(requirements, parsed_story)
        tasks = task_generator.generate_all_tasks()

        # Generate the plan
        plan = story_driven_pack.create_executable_plan(mock_servicenow_client, tasks, parsed_story)

        # Find the create_table and create_business_rule steps
        create_table_step = next((s for s in plan["execution_steps"] if s["func"] == "create_table"), None)
        create_br_step = next((s for s in plan["execution_steps"] if s["func"] == "create_business_rule"), None)

        assert create_table_step is not None, "Plan should have a create_table step"
        assert create_br_step is not None, "Plan should have a create_business_rule step"

        # Assert that both steps use the same, correctly-prefixed table name
        expected_table_name = "u_widget"
        assert create_table_step["args"]["table_name"] == expected_table_name
        assert create_br_step["args"]["table_name"] == expected_table_name