"""
Story-Driven Development Pack - Convert user stories into executable development plans
"""

from typing import Dict, Any, List, Optional, NamedTuple
from ..servicenow_client import ServiceNowClient
import re
import json
import logging
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache

# Configure logger
logger = logging.getLogger(__name__)


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
    APPLICATION_STRUCTURE = "application_structure"
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
    RequirementCategory.APPLICATION_STRUCTURE: {
        "scaffold": ["application", "module", "standalone", "custom app", "scoped app"]
    },
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


def _validate_configuration() -> None:
    """Validate that all required configuration is present."""
    required_categories = list(RequirementCategory)
    for category in required_categories:
        if category not in REQUIREMENT_KEYWORDS:
            raise ValueError(f"Missing configuration for {category}")
    logger.debug("Configuration validation passed")


# Validate configuration on module load
_validate_configuration()

def parse_user_story(story: str) -> Dict[str, Any]:
    """
    Parse user story using standard format: As a [user], I want [goal] so that [benefit]
    
    Args:
        story: The user story text to parse
        
    Returns:
        Dictionary containing parsing results with success status and components
    """
    logger.debug(f"Parsing user story: {story[:100]}...")
    
    if not story or not story.strip():
        logger.warning("Empty story provided for parsing")
        return _create_error_response("Empty story provided", story)
    
    try:
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
            
            logger.info(f"Successfully parsed user story with user: {components.user}")
            
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
        logger.warning(f"Failed to parse user story format: {story[:50]}...")
        return _analyze_partial_story_match(story_lower, story)
        
    except Exception as e:
        logger.error(f"Error parsing user story: {e}")
        return _create_error_response(f"Error parsing story: {str(e)}", story)


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
        
    Raises:
        ValueError: If story_components is invalid
    """
    if not story_components:
        logger.error("No story components provided for requirement extraction")
        return {"error": "No story components provided"}
    
    if not isinstance(story_components, dict):
        logger.error(f"Invalid story_components type: {type(story_components)}")
        return {"error": "Invalid story components format"}
    
    try:
        logger.debug("Extracting technical requirements from story components")
        
        # Combine all story text for analysis
        full_text = _combine_story_text(story_components)
        
        if not full_text.strip():
            logger.warning("Empty text extracted from story components")
            return {"error": "No text content found in story components"}
        
        # Initialize requirements structure
        requirements = {category.value: [] for category in RequirementCategory}
        
        # Extract requirements by category
        for category in RequirementCategory:
            category_requirements = _extract_category_requirements(category, full_text)
            requirements[category.value].extend(category_requirements)
        
        logger.info(f"Extracted requirements for {len([r for r in requirements.values() if r])} categories")
        
        return {
            "technical_requirements": requirements,
            "functional_requirements": _extract_functional_requirements(story_components)
        }
        
    except Exception as e:
        logger.error(f"Error extracting technical requirements: {e}")
        return {"error": f"Failed to extract requirements: {str(e)}"}


def _combine_story_text(story_components: Dict[str, Any]) -> str:
    """Combine story components into searchable text."""
    goal = story_components.get("goal", "")
    user = story_components.get("user", "")
    benefit = story_components.get("benefit", "")
    return f"{goal} {user} {benefit}".lower()


@lru_cache(maxsize=128)
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
        RequirementCategory.APPLICATION_STRUCTURE: {
            "scaffold": "New scoped application structure may be required"
        },
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
    Generate specific implementation tasks from requirements.
    
    Args:
        client: ServiceNow client instance
        requirements: Categorized technical requirements
        story_context: Story context for task generation
        
    Returns:
        List of implementation tasks organized by phase
    """
    task_generator = TaskGenerator(requirements.get("technical_requirements", {}), story_context)
    return task_generator.generate_all_tasks()


class TaskGenerator:
    """Generates implementation tasks based on requirements."""
    
    def __init__(self, requirements: Dict[str, Any], story_context: Dict[str, Any]):
        self.requirements = requirements
        self.story_context = story_context
        self.tasks = []
    
    def generate_all_tasks(self) -> List[Dict[str, Any]]:
        """Generate all implementation tasks."""
        self._add_app_structure_tasks()
        self._add_data_model_tasks()
        self._add_business_logic_tasks()
        self._add_ui_tasks()
        self._add_integration_tasks()
        self._add_testing_tasks()
        self._add_deployment_tasks()
        return self.tasks

    def _add_app_structure_tasks(self) -> None:
        """Add application structure related tasks."""
        if not self.requirements.get("application_structure"):
            return

        self.tasks.append(self._create_task(
            phase="development",
            task_type="implementation",
            title="Scaffold new application",
            description="Create the basic structure for a new scoped application",
            pack="build",
            function="app_scaffold",
            estimated_hours=1,
            dependencies=[]  # This should be one of the first steps
        ))
    
    def _add_data_model_tasks(self) -> None:
        """Add data model related tasks."""
        if not self.requirements.get("data_model"):
            return
            
        self.tasks.extend([
            self._create_task(
                phase="analysis",
                task_type="investigation",
                title="Analyze existing data model",
                description="Review current table structure and identify required changes",
                pack="query",
                function="query_table",
                estimated_hours=2,
                dependencies=[]
            ),
            self._create_task(
                phase="development",
                task_type="implementation",
                title="Implement data model changes",
                description="Create or modify tables, fields, and relationships",
                pack="build",
                function="create_table",
                estimated_hours=4,
                dependencies=["analyze_data_model"]
            )
        ])
    
    def _add_business_logic_tasks(self) -> None:
        """Add business logic related tasks."""
        business_logic = self.requirements.get("business_logic", [])
        if not business_logic:
            return
        
        if self._has_workflow_requirements(business_logic):
            self.tasks.append(self._create_task(
                phase="development",
                task_type="implementation",
                title="Implement workflow logic",
                description="Create flow designer workflows or business processes",
                pack="flow",
                function="flow_create",
                estimated_hours=6,
                dependencies=["data_model_changes"]
            ))
        
        if self._has_business_rule_requirements(business_logic):
            self.tasks.append(self._create_task(
                phase="development",
                task_type="implementation",
                title="Create business rules",
                description="Implement server-side business logic",
                pack="scripts",
                function="create_business_rule",
                estimated_hours=3,
                dependencies=["data_model_changes"]
            ))
    
    def _add_ui_tasks(self) -> None:
        """Add user interface related tasks."""
        if self.requirements.get("user_interface"):
            self.tasks.append(self._create_task(
                phase="development",
                task_type="implementation",
                title="Develop user interface",
                description="Create or modify forms, lists, and UI components",
                pack="ux",
                function="ux_create_page",
                estimated_hours=4,
                dependencies=["business_logic"]
            ))
    
    def _add_integration_tasks(self) -> None:
        """Add integration related tasks."""
        if self.requirements.get("integrations"):
            self.tasks.append(self._create_task(
                phase="development",
                task_type="implementation",
                title="Implement integrations",
                description="Create REST APIs or external system connections",
                pack="integrations",
                function="create_rest_message",
                estimated_hours=5,
                dependencies=["business_logic"]
            ))
    
    def _add_testing_tasks(self) -> None:
        """Add testing related tasks."""
        self.tasks.append(self._create_task(
            phase="testing",
            task_type="validation",
            title="Create automated tests",
            description="Develop ATF test cases for the implementation",
            pack="atf",
            function="atf_create_suite",
            estimated_hours=3,
            dependencies=["ui_development", "business_logic"]
        ))
    
    def _add_deployment_tasks(self) -> None:
        """Add deployment related tasks."""
        self.tasks.append(self._create_task(
            phase="deployment",
            task_type="deployment",
            title="Deploy to target environment",
            description="Create update set and deploy changes",
            pack="update_set",
            function="create_update_set",
            estimated_hours=1,
            dependencies=["testing_complete"]
        ))
    
    def _create_task(self, phase: str, task_type: str, title: str, description: str,
                    pack: str, function: str, estimated_hours: int, 
                    dependencies: List[str]) -> Dict[str, Any]:
        """Create a standardized task dictionary."""
        return {
            "phase": phase,
            "type": task_type,
            "title": title,
            "description": description,
            "pack": pack,
            "function": function,
            "estimated_hours": estimated_hours,
            "dependencies": dependencies
        }
    
    def _has_workflow_requirements(self, business_logic: List[str]) -> bool:
        """Check if workflow requirements exist."""
        return any("workflow" in req.lower() for req in business_logic)
    
    def _has_business_rule_requirements(self, business_logic: List[str]) -> bool:
        """Check if business rule requirements exist."""
        return any("business rule" in req.lower() for req in business_logic)

def create_executable_plan(client: ServiceNowClient, tasks: List[Dict[str, Any]],
                         story_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create an executable plan with specific ServiceNow operations.

    Args:
        client: ServiceNow client instance
        tasks: List of implementation tasks
        story_context: Original story context and metadata

    Returns:
        Dictionary containing executable plan with phases, steps, and criteria

    Raises:
        ValueError: If tasks or story_context is invalid
    """
    plan = {
        "story_reference": story_context.get("original", ""),
        "total_estimated_hours": sum(task.get("estimated_hours", 0) for task in tasks),
        "phases": {},
        "execution_steps": [],
        "prerequisites": [],
        "success_criteria": []
    }

    # Determine table name context once for the entire plan
    goal = story_context.get("components", {}).get("goal", "")
    table_name = extract_table_name_from_goal(goal)
    plan_context = {"table_name": table_name}

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
                    "args": generate_step_args(task, story_context, plan_context),
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

def generate_scope_name(app_name: str, prefix: str = "x_mcp") -> str:
    """Generates a ServiceNow-compliant scope name from an application name."""
    sanitized_name = re.sub(r'[^a-zA-Z0-9_]+', '', app_name.lower().replace(" ", "_"))
    return f"{prefix}_{sanitized_name[:30]}"


def generate_step_args(task: Dict[str, Any], story_context: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate specific arguments for ServiceNow operations based on task context
    """
    args = {"dry_run": True}  # Default to dry run for safety

    pack = task.get("pack")
    function = task.get("function")

    if pack == "build" and function == "app_scaffold":
        goal = story_context.get("components", {}).get("goal", "")
        app_name_base = extract_table_name_from_goal(goal)
        app_name = f"{app_name_base.title()} Application"
        scope_name = generate_scope_name(app_name_base)
        args.update({
            "app_name": app_name,
            "scope_name": scope_name,
            "description": f"A new application for: {goal}"
        })

    elif pack == "build" and function == "create_table":
        # Use table name from context
        table_name = context.get("table_name", "custom_table")
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
        # Use table name from context, which is now consistent
        table_name = context.get("table_name", "custom_table")
        args.update({
            "table_name": f"u_{table_name}",
            "name": f"Business Rule for {table_name.title()}",
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
    Extract a reasonable table name from the goal description using more robust logic.
    """
    # Expanded stop words and common verbs/adjectives to exclude
    stop_words = [
        "a", "an", "the", "to", "for", "in", "on", "of", "with", "as", "i",
        "want", "need", "like", "to", "be", "able", "have", "a", "new", "all",
        "create", "update", "delete", "manage", "store", "record", "view", "make",
        "assign", "route", "notify", "send", "get", "set", "track", "log",
        "from", "based", "so", "that", "can", "and", "or", "very", "table"
    ]

    words = re.findall(r'\b\w+\b', goal.lower())

    # Common ServiceNow entities (singular form)
    entities = ["incident", "request", "change", "problem", "task", "user", "group", "asset", "configuration", "item", "record", "service", "catalog"]
    contextual_entities = ["user", "group"] # Entities that are often contextual rather than primary

    found_entities = []
    # 1. Find all known entities (and handle simple plurals)
    for word in words:
        if word in entities:
            found_entities.append(word)
        elif len(word) > 1 and word.endswith('s') and word[:-1] in entities:
            found_entities.append(word[:-1])

    if found_entities:
        # If we have multiple entities, and some are non-contextual, prefer those.
        non_contextual_entities = [e for e in found_entities if e not in contextual_entities]
        if non_contextual_entities:
            # Return the last non-contextual entity
            return non_contextual_entities[-1]
        else:
            # Otherwise, just return the last contextual entity found
            return found_entities[-1]

    # 2. Fallback: find the most likely noun (last non-stopword)
    meaningful_words = [w for w in words if w not in stop_words and len(w) > 3]
    if meaningful_words:
        # Return the singular form of the last meaningful word, avoiding words like "process"
        candidate = meaningful_words[-1]
        if len(candidate) > 1 and candidate.endswith('s') and not candidate.endswith('ss'):
            return candidate[:-1]
        return candidate

    # 3. Last resort: generate a name from the goal
    sanitized_goal = re.sub(r'[^a-zA-Z0-9_]', '', goal.replace(" ", "_")).lower()
    return f"custom_{sanitized_goal[:20]}" if sanitized_goal else "custom_table"

def validate_story_completeness(story_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate that a user story has sufficient detail for implementation.
    
    Args:
        story_analysis: Parsed story analysis containing components
        
    Returns:
        ValidationResult as dictionary with completeness assessment
    """
    import time
    start_time = time.time()
    
    try:
        components = story_analysis.get("components", {})
        
        validation_checks = [
            _validate_user_persona(components),
            _validate_goal_definition(components),
            _validate_business_value(components),
            _validate_action_clarity(components)
        ]
        
        # Collect results
        missing_elements = []
        recommendations = []
        
        for check in validation_checks:
            if not check["passed"]:
                missing_elements.append(check["element"])
                recommendations.append(check["recommendation"])
        
        # Calculate confidence score
        passed_checks = len([check for check in validation_checks if check["passed"]])
        confidence_score = passed_checks / len(validation_checks)
        
        validation_result = ValidationResult(
            is_complete=confidence_score >= CONFIDENCE_THRESHOLD,
            missing_elements=missing_elements,
            recommendations=recommendations,
            confidence_score=confidence_score
        )
        
        processing_time = time.time() - start_time
        logger.info(f"Story validation completed in {processing_time:.3f}s, score: {confidence_score:.2f}")
        
        return {
            "is_complete": validation_result.is_complete,
            "missing_elements": validation_result.missing_elements,
            "recommendations": validation_result.recommendations,
            "score": validation_result.confidence_score,  # Keep 'score' for backward compatibility
            "_meta": {
                "processing_time_ms": round(processing_time * 1000, 2),
                "validation_checks_count": len(validation_checks),
                "passed_checks_count": passed_checks
            }
        }
        
    except Exception as e:
        logger.error(f"Error during story validation: {e}")
        return {
            "is_complete": False,
            "missing_elements": ["validation_error"],
            "recommendations": ["Fix validation error and try again"],
            "score": 0.0,
            "error": str(e)
        }


def _validate_user_persona(components: Dict[str, Any]) -> Dict[str, Any]:
    """Validate user persona component."""
    user = components.get("user", "").strip()
    return {
        "passed": bool(user and len(user) > 2),
        "element": "user_persona",
        "recommendation": "Specify who will use this feature (e.g., 'service desk agent', 'manager')"
    }


def _validate_goal_definition(components: Dict[str, Any]) -> Dict[str, Any]:
    """Validate goal definition component."""
    goal = components.get("goal", "").strip()
    return {
        "passed": bool(goal and len(goal) > 5),
        "element": "goal_definition", 
        "recommendation": "Clearly define what the user wants to accomplish"
    }


def _validate_business_value(components: Dict[str, Any]) -> Dict[str, Any]:
    """Validate business value component."""
    benefit = components.get("benefit", "").strip()
    return {
        "passed": bool(benefit and len(benefit) > 5),
        "element": "business_value",
        "recommendation": "Explain the business value or benefit this feature provides"
    }


def _validate_action_clarity(components: Dict[str, Any]) -> Dict[str, Any]:
    """Validate that the goal contains clear action verbs."""
    goal = components.get("goal", "").lower()
    action_verbs = ["create", "update", "delete", "view", "manage", "process", "assign", "route", "notify", "automatically"]
    
    has_clear_action = any(verb in goal for verb in action_verbs)
    
    return {
        "passed": has_clear_action,
        "element": "action_clarity",
        "recommendation": f"Use clear action verbs in the goal: {', '.join(action_verbs[:5])}, etc."
    }


def story_to_implementation(client: ServiceNowClient, story: str, 
                          validate_first: bool = True) -> Dict[str, Any]:
    """
    Complete story-to-implementation pipeline.
    
    This is the main entry point that orchestrates the entire process from
    user story parsing to executable implementation plan generation.
    
    Args:
        client: ServiceNow client instance
        story: User story text to process
        validate_first: Whether to validate story completeness before processing
        
    Returns:
        Dictionary containing complete analysis and implementation plan
    """
    import time
    start_time = time.time()
    
    try:
        logger.info(f"Starting story-to-implementation pipeline for: {story[:50]}...")
        
        # Step 1: Parse the user story
        parsed_story = parse_user_story(story)
        if not parsed_story.get("success"):
            return {
                "status": "error",
                "stage": "parsing",
                "error": parsed_story.get("error"),
                "original_story": story
            }
        
        # Step 2: Validate story completeness (optional)
        if validate_first:
            validation = validate_story_completeness(parsed_story)
            if not validation.get("is_complete"):
                return {
                    "status": "incomplete",
                    "stage": "validation",
                    "parsed_story": parsed_story,
                    "validation": validation,
                    "recommendations": validation.get("recommendations", [])
                }
        
        # Step 3: Extract technical requirements
        requirements = extract_technical_requirements(client, parsed_story["components"])
        if "error" in requirements:
            return {
                "status": "error",
                "stage": "requirements",
                "error": requirements["error"],
                "parsed_story": parsed_story
            }
        
        # Step 4: Generate implementation tasks
        tasks = generate_implementation_tasks(client, requirements, parsed_story)
        
        # Step 5: Create executable plan
        executable_plan = create_executable_plan(client, tasks, parsed_story)
        
        processing_time = time.time() - start_time
        logger.info(f"Story-to-implementation pipeline completed in {processing_time:.3f}s")
        
        return {
            "status": "success",
            "parsed_story": parsed_story,
            "validation": validate_story_completeness(parsed_story) if validate_first else None,
            "requirements": requirements,
            "tasks": tasks,
            "executable_plan": executable_plan,
            "_meta": {
                "processing_time_ms": round(processing_time * 1000, 2),
                "total_estimated_hours": executable_plan.get("total_estimated_hours", 0),
                "phases_count": len(executable_plan.get("phases", {})),
                "tasks_count": len(tasks)
            }
        }
        
    except Exception as e:
        logger.error(f"Error in story-to-implementation pipeline: {e}")
        return {
            "status": "error",
            "stage": "pipeline",
            "error": str(e),
            "original_story": story
        }