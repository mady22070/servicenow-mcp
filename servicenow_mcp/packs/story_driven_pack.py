"""
Story-Driven Development Pack - Convert user stories into executable development plans
"""

from typing import Dict, Any, List, Optional
from ..servicenow_client import ServiceNowClient
import re
import json

def parse_user_story(story: str) -> Dict[str, Any]:
    """
    Parse user story using standard format: As a [user], I want [goal] so that [benefit]
    """
    parsed = {
        "original": story,
        "format": "unknown",
        "components": {},
        "valid": False
    }
    
    # Try to match standard user story format
    user_story_pattern = r"as\s+a\s+(.+?),?\s+i\s+want\s+(.+?)\s+so\s+that\s+(.+)"
    match = re.search(user_story_pattern, story.lower())
    
    if match:
        parsed["format"] = "user_story"
        parsed["components"] = {
            "user": match.group(1).strip(),
            "goal": match.group(2).strip(), 
            "benefit": match.group(3).strip()
        }
        parsed["valid"] = True
    else:
        # Try alternative formats
        if "i want" in story.lower() or "i need" in story.lower():
            parsed["format"] = "informal_story"
            parsed["components"]["goal"] = story
            parsed["valid"] = True
        else:
            parsed["format"] = "requirement"
            parsed["components"]["requirement"] = story
    
    return parsed

def extract_technical_requirements(client: ServiceNowClient, story_components: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract technical requirements from story components
    """
    requirements = {
        "data_model": [],
        "business_logic": [],
        "user_interface": [],
        "integrations": [],
        "security": [],
        "performance": []
    }
    
    goal = story_components.get("goal", "").lower()
    user = story_components.get("user", "").lower()
    benefit = story_components.get("benefit", "").lower()
    
    full_text = f"{goal} {user} {benefit}".lower()
    
    # Data model requirements
    if any(word in full_text for word in ["create", "store", "save", "record", "data"]):
        requirements["data_model"].append("New table or fields may be required")
    
    if any(word in full_text for word in ["form", "field", "input", "capture"]):
        requirements["data_model"].append("Form modifications needed")
    
    # Business logic requirements  
    if any(word in full_text for word in ["calculate", "compute", "determine", "validate"]):
        requirements["business_logic"].append("Business rules or script includes needed")
    
    if any(word in full_text for word in ["workflow", "approval", "process", "route"]):
        requirements["business_logic"].append("Workflow or flow designer implementation")
    
    if any(word in full_text for word in ["notify", "email", "alert", "message"]):
        requirements["business_logic"].append("Notification system integration")
    
    # UI requirements
    if any(word in full_text for word in ["view", "display", "show", "interface", "portal"]):
        requirements["user_interface"].append("UI modifications or new interfaces")
    
    if any(word in full_text for word in ["report", "dashboard", "chart", "analytics"]):
        requirements["user_interface"].append("Reporting or analytics components")
    
    # Integration requirements
    if any(word in full_text for word in ["integrate", "api", "external", "third-party"]):
        requirements["integrations"].append("External system integration")
    
    # Security requirements
    if any(word in full_text for word in ["secure", "permission", "access", "role"]):
        requirements["security"].append("Access control and security considerations")
    
    # Performance requirements
    if any(word in full_text for word in ["fast", "quick", "performance", "scale"]):
        requirements["performance"].append("Performance optimization needed")
    
    return requirements

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
        "confidence_score": 0.0
    }
    
    components = story_analysis.get("components", {})
    
    # Check for essential components
    if not components.get("user"):
        validation["missing_elements"].append("user_persona")
        validation["recommendations"].append("Specify who will use this feature")
    
    if not components.get("goal"):
        validation["missing_elements"].append("goal_definition")
        validation["recommendations"].append("Clearly define what the user wants to accomplish")
    
    if not components.get("benefit"):
        validation["missing_elements"].append("business_value")
        validation["recommendations"].append("Explain the business value or benefit")
    
    # Check for technical clarity
    goal = components.get("goal", "").lower()
    if not any(word in goal for word in ["create", "update", "delete", "view", "manage", "process"]):
        validation["missing_elements"].append("action_clarity")
        validation["recommendations"].append("Use clear action verbs (create, update, view, etc.)")
    
    # Calculate confidence score
    total_checks = 4
    passed_checks = total_checks - len(validation["missing_elements"])
    validation["confidence_score"] = passed_checks / total_checks
    
    validation["is_complete"] = validation["confidence_score"] >= 0.75
    
    return validation