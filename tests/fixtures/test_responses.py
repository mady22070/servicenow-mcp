"""
Test response fixtures for mocking ServiceNow API responses.
"""

# Sample ServiceNow API responses for testing
SAMPLE_INCIDENT_RESPONSE = {
    "result": {
        "sys_id": "test123",
        "number": "INC0000001",
        "short_description": "Test incident",
        "state": "1",
        "urgency": "3",
        "impact": "3"
    }
}

SAMPLE_QUERY_RESPONSE = {
    "result": [
        {
            "sys_id": "test123",
            "number": "INC0000001", 
            "short_description": "Test incident 1",
            "state": "1"
        },
        {
            "sys_id": "test456",
            "number": "INC0000002",
            "short_description": "Test incident 2", 
            "state": "2"
        }
    ]
}

SAMPLE_ERROR_RESPONSE = {
    "error": {
        "message": "Invalid table",
        "detail": "Table 'invalid_table' does not exist"
    },
    "status": "failure"
}

SAMPLE_HEALTH_CHECK_RESPONSE = {
    "dev": {
        "status": "healthy",
        "response_time": "0.234s",
        "last_checked": "2024-01-15T10:30:00Z"
    }
}

SAMPLE_STORY_ANALYSIS_RESPONSE = {
    "status": "success",
    "parsed_story": {
        "components": {
            "user": "service desk agent",
            "goal": "automatically assign incidents based on category",
            "benefit": "tickets are routed to the right team faster"
        }
    },
    "validation": {
        "is_complete": True,
        "score": 0.95
    },
    "requirements": {
        "technical_requirements": [
            "Business rule on incident table",
            "Assignment logic based on category field",
            "Group mapping configuration"
        ],
        "functional_requirements": [
            "Automatic assignment on incident creation",
            "Category-based routing rules",
            "Fallback assignment for unknown categories"
        ]
    }
}