"""
Story-Driven Development Pack - Convert user stories into executable development plans
"""

from typing import Dict, Any, List, Optional, NamedTuple
from ..servicenow_client import ServiceNowClient
import re
import json
from dataclasses import dataclass
from enum import Enum


class StoryFormat(Enum):
    """Enumeration of supported user story formats."""
    USER_STORY = "user_story"
    INFORMAL_STORY = "informal_story"
    REQUIREMENT = "requirement"


@dataclass
class StoryComponents:
    """Data class for user story components."""
    user: str
    goal: str
    benefit: str


@dataclass
class ValidationResult:
    """Data class for story validation results."""
    is_complete: bool
    missing_elements: List[str]
    recommendations: List[str]
    confidence_score: float


class RequirementCategory(Enum):
    """Categories of technical requirements."""
    DATA_MODEL = "data_model"
    BUSINESS_LOGIC = "business_logic"
    USER_INTERFACE = "user_interface"
    INTEGRATIONS = "integrations"
    SECURITY = "security"
    PERFORMANCE = "performance"


# Configuration constants
CONFIDENCE_THRESHOLD = 0.75
DEFAULT_ESTIMATED_HOURS = {
    "analysis": 2,
    "development": 4,
    "testing": 3,
    "deployment": 1
}

# Keyword mappings for requirement extraction
REQUIREMENT_KEYWORDS = {
    RequirementCategory.DATA_MODEL: {
        "create_store": ["create", "store", "save", "record", "data"],
        "form_fields": ["form", "field", "input", "capture"]
    },
    RequirementCategory.BUSINESS_LOGIC: {
        "calculations": ["calculate", "compute", "determine", "validate"],
        "workflows": ["workflow", "approval", "process", "route"],
        "notifications": ["notify", "email", "alert", "message"]
    },
    RequirementCategory.USER_INTERFACE: {
        "display": ["view", "display", "show", "interface", "portal"],
        "reporting": ["report", "dashboard", "chart", "analytics"]
    },
    RequirementCategory.INTEGRATIONS: {
        "external": ["integrate", "api", "external", "third-party"]
    },
    RequirementCategory.SECURITY: {
        "access": ["secure", "permission", "access", "role"]
    },
    RequirementCategory.PERFORMANCE: {
        "optimization": ["fast", "quick", "performance", "scale"]
    }
}

def parse_user_story(story: str) -> Dict[str, Any]:
    """
    Parse user story using standard format: As a [user], I want [goal] so that [benefit]
    
    Args:
        story: The user story text to parse
        
    Returns:
        Dictionary containing parsing results with success status and components
    """
    if not story or not story.strip():
        return _create_error_response("Empty story provided", story)
    
    story_lower = story.lower().strip()
    
    # Try to match standard user story format
    user_story_pattern = r"as\s+a\s+(.+?),?\s+i\s+want\s+(.+?)\s+so\s+that\s+(.+)"
    match = re.search(user_story_pattern, story_lower)
    
    if match:
        components = StoryComponents(
            user=match.group(1).strip(),
            goal=match.group(2).strip(),
            benefit=match.group(3).strip()
        )
        
        return {
            "success": True,
            "original": story,
            "format": StoryFormat.USER_STORY.value,
            "components": {
                "user": components.user,
                "goal": components.goal,
                "benefit": components.benefit
            }
        }
    
    # Provide specific error messages for partial matches
    return _analyze_partial_story_match(story_lower, story)


def _create_error_response(error_message: str, original_story: str) -> Dict[str, Any]:
    """Create a standardized error response."""
    return {
        "success": False,
        "error": error_message,
        "original": original_story
    }


def _analyze_partial_story_match(story_lower: str, original_story: str) -> Dict[str, Any]:
    """Analyze partial story matches and provide specific error messages."""
    has_as_a = "as a" in story_lower
    has_i_want = "i want" in story_lower
    has_so_that = "so that" in story_lower
    
    if has_as_a and has_i_want and not has_so_that:
        return _create_error_response(
            "Missing 'so that' benefit clause in user story", 
            original_story
        )
    elif has_i_want and not has_as_a:
        return _create_error_response(
            "Missing user persona - story should start with 'As a [user]'", 
            original_story
        )
    elif has_as_a and not has_i_want:
        return _create_error_response(
            "Missing goal statement - include 'I want [goal]'", 
            original_story
        )
    else:
        return _create_error_response(
            "Invalid user story format. Expected: 'As a [user], I want [goal] so that [benefit]'", 
            original_story
        )

def extract_technical_requirements(client: ServiceNowClient, story_components: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract technical requirements from story components using keyword analysis.
    
    Args:
        client: ServiceNow client instance
        story_components: Parsed story components
        
    Returns:
        Dictionary of categorized technical requirements
    """
    if not story_components:
        return {"error": "No story components provided"}
    
    # Combine all story text for analysis
    full_text = _combine_story_text(story_components)
    
    # Initialize requirements structure
    requirements = {category.value: [] for category in RequirementCategory}
    
    # Extract requirements by category
    for category in RequirementCategory:
        category_requirements = _extract_category_requirements(category, full_text)
        requirements[category.value].extend(category_requirements)
    
    return {
        "technical_requirements": requirements,
        "functional_requirements": _extract_functional_requirements(story_components)
    }


def _combine_story_text(story_components: Dict[str, Any]) -> str:
    """Combine story components into searchable text."""
    goal = story_components.get("goal", "")
    user = story_components.get("user", "")
    benefit = story_components.get("benefit", "")
    return f"{goal} {user} {benefit}".lower()


def _extract_category_requirements(category: RequirementCategory, full_text: str) -> List[str]:
    """Extract requirements for a specific category."""
    requirements = []
    category_keywords = REQUIREMENT_KEYWORDS.get(category, {})
    
    for requirement_type, keywords in category_keywords.items():
        if any(keyword in full_text for keyword in keywords):
            requirement_text = _get_requirement_text(category, requirement_type)
            if requirement_text:
                requirements.append(requirement_text)
    
    return requirements


def _get_requirement_text(category: RequirementCategory, requirement_type: str) -> str:
    """Get descriptive text for a requirement type."""
    requirement_descriptions = {
        RequirementCategory.DATA_MODEL: {
            "create_store": "New table or fields may be required",
            "form_fields": "Form modifications needed"
        },
        RequirementCategory.BUSINESS_LOGIC: {
            "calculations": "Business rules or script includes needed",
            "workflows": "Workflow or flow designer implementation",
            "notifications": "Notification system integration"
        },
        RequirementCategory.USER_INTERFACE: {
            "display": "UI modifications or new interfaces",
            "reporting": "Reporting or analytics components"
        },
        RequirementCategory.INTEGRATIONS: {
            "external": "External system integration"
        },
        RequirementCategory.SECURITY: {
            "access": "Access control and security considerations"
        },
        RequirementCategory.PERFORMANCE: {
            "optimization": "Performance optimization needed"
        }
    }
    
    return requirement_descriptions.get(category, {}).get(requirement_type, "")


def _extract_functional_requirements(story_components: Dict[str, Any]) -> List[str]:
    """Extract functional requirements from story components."""
    functional_requirements = []
    
    goal = story_components.get("goal", "")
    benefit = story_components.get("benefit", "")
    
    if goal:
        functional_requirements.append(f"System must: {goal}")
    
    if benefit:
        functional_requirements.append(f"Expected outcome: {benefit}")
    
    return functional_requirements

def generate_implementation_tasks(client: ServiceNowClient, requirements: Dict[str, Any], 
                                story_context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate specific implementation tasks from requirements
    """
    tasks = []
    
    # Data model tasks
    if requirements.get("data_model"):
        tasks.append({
            "phase": "analysis",
            "type": "investigation",
            "title": "Analyze existing data model",
            "description": "Review current table structure and identify required changes",
            "pack": "query",
            "function": "query_table",
            "estimated_hours": 2,
            "dependencies": []
        })
        
        tasks.append({
            "phase": "development", 
            "type": "implementation",
            "title": "Implement data model changes",
            "description": "Create or modify tables, fields, and relationships",
            "pack": "build",
            "function": "create_table",
            "estimated_hours": 4,
            "dependencies": ["analyze_data_model"]
        })
    
    # Business logic tasks
    if requirements.get("business_logic"):
        if any("workflow" in req.lower() for req in requirements["business_logic"]):
            tasks.append({
                "phase": "development",
                "type": "implementation", 
                "title": "Implement workflow logic",
                "description": "Create flow designer workflows or business processes",
                "pack": "flow",
                "function": "flow_create",
                "estimated_hours": 6,
                "dependencies": ["data_model_changes"]
            })
        
        if any("business rule" in req.lower() for req in requirements["business_logic"]):
            tasks.append({
                "phase": "development",
                "type": "implementation",
                "title": "Create business rules",
                "description": "Implement server-side business logic",
                "pack": "scripts",
                "function": "create_business_rule", 
                "estimated_hours": 3,
                "dependencies": ["data_model_changes"]
            })
    
    # UI tasks
    if requirements.get("user_interface"):
        tasks.append({
            "phase": "development",
            "type": "implementation",
            "title": "Develop user interface",
            "description": "Create or modify forms, lists, and UI components",
            "pack": "ux",
            "function": "ux_create_page",
            "estimated_hours": 4,
            "dependencies": ["business_logic"]
        })
    
    # Integration tasks
    if requirements.get("integrations"):
        tasks.append({
            "phase": "development", 
            "type": "implementation",
            "title": "Implement integrations",
            "description": "Create REST APIs or external system connections",
            "pack": "integrations",
            "function": "create_rest_message",
            "estimated_hours": 5,
            "dependencies": ["business_logic"]
        })
    
    # Testing tasks
    tasks.append({
        "phase": "testing",
        "type": "validation",
        "title": "Create automated tests",
        "description": "Develop ATF test cases for the implementation",
        "pack": "atf", 
        "function": "atf_create_suite",
        "estimated_hours": 3,
        "dependencies": ["ui_development", "business_logic"]
    })
    
    # Deployment tasks
    tasks.append({
        "phase": "deployment",
        "type": "deployment",
        "title": "Deploy to target environment", 
        "description": "Create update set and deploy changes",
        "pack": "update_set",
        "function": "create_update_set",
        "estimated_hours": 1,
        "dependencies": ["testing_complete"]
    })
    
    return tasks

def create_executable_plan(client: ServiceNowClient, tasks: List[Dict[str, Any]], 
                         story_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create an executable plan with specific ServiceNow operations
    """
    plan = {
        "story_reference": story_context.get("original", ""),
        "total_estimated_hours": sum(task.get("estimated_hours", 0) for task in tasks),
        "phases": {},
        "execution_steps": [],
        "prerequisites": [],
        "success_criteria": []
    }
    
    # Group tasks by phase
    for task in tasks:
        phase = task.get("phase", "unknown")
        if phase not in plan["phases"]:
            plan["phases"][phase] = []
        plan["phases"][phase].append(task)
    
    # Create execution steps with actual ServiceNow operations
    step_counter = 1
    
    for phase_name in ["analysis", "development", "testing", "deployment"]:
        if phase_name in plan["phases"]:
            for task in plan["phases"][phase_name]:
                execution_step = {
                    "step": step_counter,
                    "phase": phase_name,
                    "pack": task.get("pack"),
                    "func": task.get("function"),
                    "args": generate_step_args(task, story_context),
                    "description": task.get("description"),
                    "estimated_hours": task.get("estimated_hours", 1)
                }
                plan["execution_steps"].append(execution_step)
                step_counter += 1
    
    # Define success criteria
    plan["success_criteria"] = [
        "All automated tests pass",
        "User acceptance criteria met", 
        "No critical security vulnerabilities",
        "Performance requirements satisfied",
        "Documentation updated"
    ]
    
    return plan

def generate_step_args(task: Dict[str, Any], story_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate specific arguments for ServiceNow operations based on task context
    """
    args = {"dry_run": True}  # Default to dry run for safety
    
    pack = task.get("pack")
    function = task.get("function")
    
    if pack == "build" and function == "create_table":
        # Extract table name from story context
        goal = story_context.get("components", {}).get("goal", "")
        table_name = extract_table_name_from_goal(goal)
        args.update({
            "table_label": f"{table_name.title()} Management",
            "table_name": f"u_{table_name}",
            "scope": "x_cloudorch_aiops"
        })
    
    elif pack == "flow" and function == "flow_create":
        goal = story_context.get("components", {}).get("goal", "")
        args.update({
            "name": f"Process {goal[:50]}",
            "description": f"Automated workflow for: {goal}"
        })
    
    elif pack == "scripts" and function == "create_business_rule":
        args.update({
            "table_name": "u_custom_table",  # This would be determined from context
            "name": "Custom Business Logic",
            "when": "before",
            "actions": {"insert": True, "update": True}
        })
    
    elif pack == "atf" and function == "atf_create_suite":
        args.update({
            "name": "Story Implementation Test Suite",
            "description": "Automated tests for user story implementation"
        })
    
    elif pack == "update_set" and function == "create_update_set":
        args.update({
            "name": f"Story Implementation - {story_context.get('original', '')[:50]}",
            "description": "Implementation of user story requirements"
        })
    
    return args

def extract_table_name_from_goal(goal: str) -> str:
    """
    Extract a reasonable table name from the goal description
    """
    # Simple extraction - look for nouns that could be table names
    words = re.findall(r'\b\w+\b', goal.lower())
    
    # Common ServiceNow entities
    entities = ["incident", "request", "change", "problem", "task", "user", "group", "asset", "configuration"]
    
    for word in words:
        if word in entities:
            return word
    
    # If no standard entity found, use first meaningful noun
    meaningful_words = [w for w in words if len(w) > 3 and w not in ["want", "need", "able", "create", "manage"]]
    
    return meaningful_words[0] if meaningful_words else "custom_item"

def validate_story_completeness(story_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate that a user story has sufficient detail for implementation
    """
    validation = {
        "is_complete": True,
        "missing_elements": [],
        "recommendations": [],
        "score": 0.0
    }
    
    components = story_analysis.get("components", {})
    
    # Check for essential components
    if not components.get("user") or len(components.get("user", "").strip()) < 3:
        validation["missing_elements"].append("user_persona")
        validation["recommendations"].append("Specify who will use this feature")
    
    if not components.get("goal") or len(components.get("goal", "").strip()) < 5:
        validation["missing_elements"].append("goal_definition")
        validation["recommendations"].append("Clearly define what the user wants to accomplish")
    
    if not components.get("benefit") or len(components.get("benefit", "").strip()) < 5:
        validation["missing_elements"].append("business_value")
        validation["recommendations"].append("Explain the business value or benefit")
    
    # Check for technical clarity
    goal = components.get("goal", "").lower()
    if not any(word in goal for word in ["create", "update", "delete", "view", "manage", "process", "assign", "route", "automatically"]):
        validation["missing_elements"].append("action_clarity")
        validation["recommendations"].append("Use clear action verbs (create, update, view, etc.)")
    
    # Calculate confidence score
    total_checks = 4
    passed_checks = total_checks - len(validation["missing_elements"])
    validation["score"] = passed_checks / total_checks
    
    validation["is_complete"] = validation["score"] >= 0.75
    
    return validation