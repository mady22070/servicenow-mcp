"""
RAG (Retrieval-Augmented Generation) Knowledge Pack for ServiceNow MCP.

Provides intelligent knowledge retrieval, automated ingestion, and contextual recommendations
based on the continuous learning RAG system.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from ..knowledge import (
    KnowledgeIngestionPipeline, RecommendationEngine, ConflictResolver,
    SourceManager, KnowledgeProcessor
)
from ..knowledge.realtime_updater import RealtimeKnowledgeUpdater
from ..knowledge.maintenance_system import KnowledgeMaintenanceSystem
from ..knowledge.models import (
    RecommendationContext, KnowledgeSource, KnowledgeSourceType,
    AuthorityLevel, IngestionResult
)
from ..vector_db import VectorDBConfig

logger = logging.getLogger(__name__)


class RAGKnowledgePack:
    """RAG Knowledge Pack for intelligent ServiceNow knowledge management."""
    
    def __init__(self):
        self.name = "RAG Knowledge Pack"
        self.description = "Intelligent knowledge retrieval and continuous learning system"
        
        # Initialize components
        vector_config = VectorDBConfig(
            collection_name="servicenow_rag_knowledge",
            embedding_model="all-MiniLM-L6-v2",
            use_openai=False,  # Start with local model
            max_results=20
        )
        
        self.ingestion_pipeline = KnowledgeIngestionPipeline(vector_config)
        self.recommendation_engine = RecommendationEngine(vector_config)
        self.conflict_resolver = ConflictResolver(vector_config)
        self.source_manager = SourceManager()
        self.realtime_updater = RealtimeKnowledgeUpdater(vector_config)
        self.maintenance_system = KnowledgeMaintenanceSystem(vector_config)
        
        # Initialize default sources
        self._initialized = False
    
    async def get_tools(self) -> List[Dict[str, Any]]:
        """Get available RAG knowledge tools."""
        if not self._initialized:
            await self._initialize()
        
        return [
            {
                "name": "search_knowledge",
                "description": "Search ServiceNow knowledge base with intelligent recommendations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for ServiceNow knowledge"
                        },
                        "context": {
                            "type": "object",
                            "description": "Additional context for better recommendations",
                            "properties": {
                                "user_intent": {"type": "string"},
                                "servicenow_version": {"type": "string"},
                                "environment_type": {"type": "string"},
                                "user_role": {"type": "string"},
                                "current_task": {"type": "string"}
                            }
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results to return",
                            "default": 10
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_trending_knowledge",
                "description": "Get trending ServiceNow knowledge and best practices",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "time_period_days": {
                            "type": "integer",
                            "description": "Time period in days to consider for trending",
                            "default": 7
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results to return",
                            "default": 10
                        }
                    }
                }
            },
            {
                "name": "ingest_knowledge_sources",
                "description": "Manually trigger knowledge ingestion from configured sources",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "source_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Specific source IDs to ingest (empty for all sources)"
                        },
                        "force_update": {
                            "type": "boolean",
                            "description": "Force update even if sources are up to date",
                            "default": False
                        }
                    }
                }
            },
            {
                "name": "get_knowledge_stats",
                "description": "Get statistics about the knowledge base and ingestion process",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "manage_knowledge_sources",
                "description": "Manage knowledge sources configuration",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["list", "add", "update", "remove", "enable", "disable"],
                            "description": "Action to perform on knowledge sources"
                        },
                        "source_config": {
                            "type": "object",
                            "description": "Source configuration for add/update actions",
                            "properties": {
                                "id": {"type": "string"},
                                "name": {"type": "string"},
                                "source_type": {"type": "string"},
                                "authority_level": {"type": "string"},
                                "base_url": {"type": "string"},
                                "update_frequency": {"type": "integer"}
                            }
                        },
                        "source_id": {
                            "type": "string",
                            "description": "Source ID for update/remove/enable/disable actions"
                        }
                    },
                    "required": ["action"]
                }
            },
            {
                "name": "detect_knowledge_conflicts",
                "description": "Detect and analyze conflicts in the knowledge base",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "auto_resolve": {
                            "type": "boolean",
                            "description": "Automatically resolve conflicts where possible",
                            "default": False
                        }
                    }
                }
            },
            {
                "name": "get_contextual_recommendations",
                "description": "Get intelligent recommendations based on current development context",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "development_context": {
                            "type": "object",
                            "description": "Current development context",
                            "properties": {
                                "task_description": {"type": "string"},
                                "technologies": {"type": "array", "items": {"type": "string"}},
                                "challenges": {"type": "array", "items": {"type": "string"}},
                                "environment": {"type": "string"},
                                "timeline": {"type": "string"}
                            },
                            "required": ["task_description"]
                        },
                        "max_recommendations": {
                            "type": "integer",
                            "description": "Maximum number of recommendations",
                            "default": 5
                        }
                    },
                    "required": ["development_context"]
                }
            },
            {
                "name": "get_realtime_recommendations",
                "description": "Get recommendations enhanced with real-time learning",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for recommendations"
                        },
                        "context": {
                            "type": "object",
                            "description": "Context for enhanced recommendations",
                            "properties": {
                                "user_intent": {"type": "string"},
                                "servicenow_version": {"type": "string"},
                                "environment_type": {"type": "string"},
                                "user_role": {"type": "string"},
                                "current_task": {"type": "string"}
                            }
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "default": 10
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "register_recommendation_feedback",
                "description": "Register feedback on recommendation quality for learning",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "knowledge_item_id": {
                            "type": "string",
                            "description": "ID of the knowledge item"
                        },
                        "feedback": {
                            "type": "object",
                            "description": "Feedback data",
                            "properties": {
                                "rating": {"type": "number", "minimum": 0, "maximum": 1},
                                "helpful": {"type": "boolean"},
                                "comments": {"type": "string"},
                                "context_match": {"type": "boolean"}
                            },
                            "required": ["rating"]
                        },
                        "context": {
                            "type": "object",
                            "description": "Context when feedback was given",
                            "properties": {
                                "query": {"type": "string"},
                                "user_intent": {"type": "string"},
                                "task": {"type": "string"}
                            },
                            "required": ["query"]
                        }
                    },
                    "required": ["knowledge_item_id", "feedback", "context"]
                }
            },
            {
                "name": "detect_knowledge_drift",
                "description": "Detect if knowledge recommendations are drifting from user needs",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "context": {
                            "type": "object",
                            "description": "Context to analyze for drift",
                            "properties": {
                                "user_intent": {"type": "string"},
                                "environment_type": {"type": "string"},
                                "user_role": {"type": "string"}
                            }
                        }
                    }
                }
            },
            {
                "name": "get_knowledge_freshness_report",
                "description": "Generate a comprehensive knowledge freshness report",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "detect_deprecated_knowledge",
                "description": "Detect potentially deprecated knowledge items",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "submit_knowledge_improvement",
                "description": "Submit feedback for knowledge improvement",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "knowledge_item_id": {
                            "type": "string",
                            "description": "ID of the knowledge item to improve"
                        },
                        "improvement_feedback": {
                            "type": "object",
                            "description": "Improvement feedback",
                            "properties": {
                                "content_outdated": {"type": "boolean"},
                                "missing_information": {"type": "boolean"},
                                "incorrect_information": {"type": "boolean"},
                                "suggestions": {"type": "string"},
                                "additional_context": {"type": "string"}
                            }
                        }
                    },
                    "required": ["knowledge_item_id", "improvement_feedback"]
                }
            },
            {
                "name": "get_maintenance_status",
                "description": "Get knowledge base maintenance system status and statistics",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a RAG knowledge tool."""
        try:
            if not self._initialized:
                await self._initialize()
            
            if tool_name == "search_knowledge":
                return await self._search_knowledge(parameters)
            elif tool_name == "get_trending_knowledge":
                return await self._get_trending_knowledge(parameters)
            elif tool_name == "ingest_knowledge_sources":
                return await self._ingest_knowledge_sources(parameters)
            elif tool_name == "get_knowledge_stats":
                return await self._get_knowledge_stats(parameters)
            elif tool_name == "manage_knowledge_sources":
                return await self._manage_knowledge_sources(parameters)
            elif tool_name == "detect_knowledge_conflicts":
                return await self._detect_knowledge_conflicts(parameters)
            elif tool_name == "get_contextual_recommendations":
                return await self._get_contextual_recommendations(parameters)
            elif tool_name == "get_realtime_recommendations":
                return await self._get_realtime_recommendations(parameters)
            elif tool_name == "register_recommendation_feedback":
                return await self._register_recommendation_feedback(parameters)
            elif tool_name == "detect_knowledge_drift":
                return await self._detect_knowledge_drift(parameters)
            elif tool_name == "get_knowledge_freshness_report":
                return await self._get_knowledge_freshness_report(parameters)
            elif tool_name == "detect_deprecated_knowledge":
                return await self._detect_deprecated_knowledge(parameters)
            elif tool_name == "submit_knowledge_improvement":
                return await self._submit_knowledge_improvement(parameters)
            elif tool_name == "get_maintenance_status":
                return await self._get_maintenance_status(parameters)
            else:
                return {"error": f"Unknown tool: {tool_name}"}
                
        except Exception as e:
            logger.error(f"Error executing RAG tool {tool_name}: {e}")
            return {"error": str(e)}
    
    async def _initialize(self):
        """Initialize the RAG system with default sources."""
        try:
            await self.ingestion_pipeline.initialize_sources()
            self._initialized = True
            logger.info("RAG Knowledge Pack initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing RAG Knowledge Pack: {e}")
    
    async def _search_knowledge(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Search knowledge base with intelligent recommendations."""
        query = parameters["query"]
        context_data = parameters.get("context", {})
        max_results = parameters.get("max_results", 10)
        
        # Create recommendation context
        context = RecommendationContext(
            query=query,
            user_intent=context_data.get("user_intent"),
            servicenow_version=context_data.get("servicenow_version"),
            environment_type=context_data.get("environment_type"),
            user_role=context_data.get("user_role"),
            current_task=context_data.get("current_task")
        )
        
        # Get recommendations
        recommendations = await self.recommendation_engine.get_recommendations(
            context, max_results
        )
        
        # Format results
        results = []
        for rec in recommendations:
            results.append({
                "title": rec.knowledge_item.title,
                "content": rec.knowledge_item.content[:500] + "..." if len(rec.knowledge_item.content) > 500 else rec.knowledge_item.content,
                "url": rec.knowledge_item.url,
                "source": rec.knowledge_item.source_id,
                "authority_level": rec.knowledge_item.authority_level.value,
                "tags": rec.knowledge_item.tags,
                "categories": rec.knowledge_item.categories,
                "relevance_score": round(rec.relevance_score, 3),
                "confidence_score": round(rec.confidence_score, 3),
                "reasoning": rec.reasoning,
                "suggested_actions": rec.suggested_actions
            })
        
        return {
            "query": query,
            "results_count": len(results),
            "results": results,
            "search_context": {
                "user_intent": context.user_intent,
                "environment": context.environment_type,
                "role": context.user_role
            }
        }
    
    async def _get_trending_knowledge(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get trending knowledge and best practices."""
        time_period_days = parameters.get("time_period_days", 7)
        max_results = parameters.get("max_results", 10)
        
        time_period = timedelta(days=time_period_days)
        recommendations = await self.recommendation_engine.get_trending_knowledge(
            time_period, max_results
        )
        
        # Format results
        trending_items = []
        for rec in recommendations:
            trending_items.append({
                "title": rec.knowledge_item.title,
                "content": rec.knowledge_item.content[:300] + "..." if len(rec.knowledge_item.content) > 300 else rec.knowledge_item.content,
                "source": rec.knowledge_item.source_id,
                "authority_level": rec.knowledge_item.authority_level.value,
                "tags": rec.knowledge_item.tags,
                "categories": rec.knowledge_item.categories,
                "confidence_score": round(rec.confidence_score, 3),
                "created_at": rec.knowledge_item.created_at.isoformat() if rec.knowledge_item.created_at else None
            })
        
        return {
            "time_period_days": time_period_days,
            "trending_count": len(trending_items),
            "trending_knowledge": trending_items
        }
    
    async def _ingest_knowledge_sources(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Manually trigger knowledge ingestion."""
        source_ids = parameters.get("source_ids", [])
        force_update = parameters.get("force_update", False)
        
        if source_ids:
            # Ingest specific sources
            results = {}
            for source_id in source_ids:
                result = await self.ingestion_pipeline.ingest_from_source(
                    source_id, force_update
                )
                results[source_id] = {
                    "items_processed": result.items_processed,
                    "items_added": result.items_added,
                    "items_updated": result.items_updated,
                    "errors": result.errors,
                    "processing_time": result.processing_time
                }
        else:
            # Ingest all sources
            all_results = await self.ingestion_pipeline.ingest_all_sources(force_update)
            results = {
                source_id: {
                    "items_processed": result.items_processed,
                    "items_added": result.items_added,
                    "items_updated": result.items_updated,
                    "errors": result.errors,
                    "processing_time": result.processing_time
                }
                for source_id, result in all_results.items()
            }
        
        # Calculate totals
        total_processed = sum(r["items_processed"] for r in results.values())
        total_added = sum(r["items_added"] for r in results.values())
        total_errors = sum(len(r["errors"]) for r in results.values())
        
        return {
            "ingestion_summary": {
                "sources_processed": len(results),
                "total_items_processed": total_processed,
                "total_items_added": total_added,
                "total_errors": total_errors
            },
            "source_results": results
        }
    
    async def _get_knowledge_stats(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get knowledge base statistics."""
        stats = await self.ingestion_pipeline.get_ingestion_stats()
        
        # Get source information
        sources = await self.source_manager.get_all_sources()
        source_info = []
        for source in sources:
            source_info.append({
                "id": source.id,
                "name": source.name,
                "type": source.source_type.value,
                "authority": source.authority_level.value,
                "enabled": source.enabled,
                "last_updated": source.last_updated.isoformat() if source.last_updated else None,
                "update_frequency": source.update_frequency
            })
        
        return {
            "knowledge_base_stats": stats,
            "sources": source_info,
            "system_status": {
                "initialized": self._initialized,
                "total_sources": len(sources),
                "enabled_sources": len([s for s in sources if s.enabled])
            }
        }
    
    async def _manage_knowledge_sources(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Manage knowledge sources configuration."""
        action = parameters["action"]
        
        if action == "list":
            sources = await self.source_manager.get_all_sources()
            return {
                "action": "list",
                "sources": [
                    {
                        "id": s.id,
                        "name": s.name,
                        "type": s.source_type.value,
                        "authority": s.authority_level.value,
                        "enabled": s.enabled,
                        "base_url": s.base_url,
                        "update_frequency": s.update_frequency
                    }
                    for s in sources
                ]
            }
        
        elif action == "add":
            source_config = parameters["source_config"]
            source = KnowledgeSource(
                id=source_config["id"],
                name=source_config["name"],
                source_type=KnowledgeSourceType(source_config["source_type"]),
                authority_level=AuthorityLevel(source_config["authority_level"]),
                base_url=source_config["base_url"],
                update_frequency=source_config.get("update_frequency", 3600)
            )
            
            success = await self.source_manager.add_source(source)
            return {
                "action": "add",
                "success": success,
                "source_id": source.id
            }
        
        elif action in ["enable", "disable"]:
            source_id = parameters["source_id"]
            if action == "enable":
                success = await self.source_manager.enable_source(source_id)
            else:
                success = await self.source_manager.disable_source(source_id)
            
            return {
                "action": action,
                "success": success,
                "source_id": source_id
            }
        
        else:
            return {"error": f"Unsupported action: {action}"}
    
    async def _detect_knowledge_conflicts(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Detect and analyze knowledge conflicts."""
        auto_resolve = parameters.get("auto_resolve", False)
        
        # For now, return a placeholder response
        # In a full implementation, this would analyze the knowledge base
        return {
            "conflicts_detected": 0,
            "conflicts_resolved": 0,
            "auto_resolve_enabled": auto_resolve,
            "message": "Conflict detection system ready - full implementation requires knowledge base analysis"
        }
    
    async def _get_contextual_recommendations(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get contextual recommendations for development tasks."""
        dev_context = parameters["development_context"]
        max_recommendations = parameters.get("max_recommendations", 5)
        
        # Build context from development information
        task_description = dev_context["task_description"]
        technologies = dev_context.get("technologies", [])
        challenges = dev_context.get("challenges", [])
        environment = dev_context.get("environment", "development")
        
        # Create enhanced query
        query_parts = [task_description]
        if technologies:
            query_parts.append(f"technologies: {', '.join(technologies)}")
        if challenges:
            query_parts.append(f"challenges: {', '.join(challenges)}")
        
        enhanced_query = " ".join(query_parts)
        
        # Create recommendation context
        context = RecommendationContext(
            query=enhanced_query,
            user_intent="development_guidance",
            environment_type=environment,
            current_task=task_description,
            metadata={
                "technologies": technologies,
                "challenges": challenges
            }
        )
        
        # Get recommendations
        recommendations = await self.recommendation_engine.get_recommendations(
            context, max_recommendations
        )
        
        # Format contextual recommendations
        contextual_recs = []
        for rec in recommendations:
            contextual_recs.append({
                "title": rec.knowledge_item.title,
                "summary": rec.knowledge_item.content[:200] + "..." if len(rec.knowledge_item.content) > 200 else rec.knowledge_item.content,
                "relevance_to_task": rec.reasoning,
                "recommended_actions": rec.suggested_actions,
                "confidence": round(rec.confidence_score, 3),
                "source": rec.knowledge_item.source_id,
                "authority": rec.knowledge_item.authority_level.value,
                "tags": rec.knowledge_item.tags
            })
        
        return {
            "development_context": dev_context,
            "recommendations_count": len(contextual_recs),
            "contextual_recommendations": contextual_recs
        }
    
    async def _get_realtime_recommendations(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get recommendations enhanced with real-time learning."""
        query = parameters["query"]
        context_data = parameters.get("context", {})
        max_results = parameters.get("max_results", 10)
        
        # Create recommendation context
        context = RecommendationContext(
            query=query,
            user_intent=context_data.get("user_intent"),
            servicenow_version=context_data.get("servicenow_version"),
            environment_type=context_data.get("environment_type"),
            user_role=context_data.get("user_role"),
            current_task=context_data.get("current_task")
        )
        
        # Get real-time enhanced recommendations
        recommendations = await self.realtime_updater.get_realtime_recommendations(
            context, max_results
        )
        
        # Format results
        results = []
        for rec in recommendations:
            results.append({
                "title": rec["knowledge_item"].title,
                "content": rec["knowledge_item"].content[:500] + "..." if len(rec["knowledge_item"].content) > 500 else rec["knowledge_item"].content,
                "url": rec["knowledge_item"].url,
                "source": rec["knowledge_item"].source_id,
                "authority_level": rec["knowledge_item"].authority_level.value,
                "tags": rec["knowledge_item"].tags,
                "categories": rec["knowledge_item"].categories,
                "relevance_score": round(rec["relevance_score"], 3),
                "confidence_score": round(rec["confidence_score"], 3),
                "reasoning": rec["reasoning"],
                "suggested_actions": rec["suggested_actions"],
                "learning_applied": rec.get("learning_applied", False),
                "original_scores": rec.get("original_scores", {})
            })
        
        # Detect conflicts in recommendations
        conflict_analysis = await self.recommendation_engine.detect_recommendation_conflicts(
            [rec for rec in recommendations if "knowledge_item" in rec]
        )
        
        return {
            "query": query,
            "results_count": len(results),
            "results": results,
            "realtime_enhancements": {
                "learning_applied": any(r.get("learning_applied", False) for r in recommendations),
                "conflict_analysis": conflict_analysis
            },
            "search_context": {
                "user_intent": context.user_intent,
                "environment": context.environment_type,
                "role": context.user_role
            }
        }
    
    async def _register_recommendation_feedback(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Register feedback on recommendation quality."""
        knowledge_item_id = parameters["knowledge_item_id"]
        feedback = parameters["feedback"]
        context_data = parameters["context"]
        
        # Create recommendation context
        context = RecommendationContext(
            query=context_data["query"],
            user_intent=context_data.get("user_intent"),
            current_task=context_data.get("task")
        )
        
        # Register feedback with real-time updater
        await self.realtime_updater.register_usage_feedback(
            knowledge_item_id, context, feedback
        )
        
        # If feedback indicates success, register that too
        if feedback.get("helpful", False) or feedback.get("rating", 0) > 0.7:
            success_metrics = {
                "successful": True,
                "rating": feedback.get("rating", 0.8),
                "context_match": feedback.get("context_match", True)
            }
            
            await self.realtime_updater.register_recommendation_success(
                knowledge_item_id, context, success_metrics
            )
        
        return {
            "feedback_registered": True,
            "knowledge_item_id": knowledge_item_id,
            "feedback_summary": {
                "rating": feedback.get("rating"),
                "helpful": feedback.get("helpful"),
                "has_comments": bool(feedback.get("comments"))
            }
        }
    
    async def _detect_knowledge_drift(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Detect knowledge drift for given context."""
        context_data = parameters.get("context", {})
        
        # Create recommendation context for drift analysis
        context = RecommendationContext(
            query="drift_analysis",
            user_intent=context_data.get("user_intent", "general"),
            environment_type=context_data.get("environment_type"),
            user_role=context_data.get("user_role")
        )
        
        # Detect drift
        drift_analysis = await self.realtime_updater.detect_knowledge_drift(context)
        
        return {
            "drift_analysis": drift_analysis,
            "context_analyzed": {
                "user_intent": context.user_intent,
                "environment": context.environment_type,
                "role": context.user_role
            },
            "recommendations": drift_analysis.get("recommendations", [])
        }
    
    async def _get_knowledge_freshness_report(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate knowledge freshness report."""
        freshness_report = await self.maintenance_system.generate_freshness_report()
        
        return {
            "freshness_report": {
                "total_items": freshness_report.total_items,
                "fresh_items": freshness_report.fresh_items,
                "aging_items": freshness_report.aging_items,
                "stale_items": freshness_report.stale_items,
                "deprecated_items": freshness_report.deprecated_items,
                "freshness_score": round(freshness_report.freshness_score, 3),
                "recommendations": freshness_report.recommendations,
                "generated_at": freshness_report.generated_at.isoformat()
            },
            "freshness_breakdown": {
                "fresh_percentage": round((freshness_report.fresh_items / max(freshness_report.total_items, 1)) * 100, 1),
                "aging_percentage": round((freshness_report.aging_items / max(freshness_report.total_items, 1)) * 100, 1),
                "stale_percentage": round((freshness_report.stale_items / max(freshness_report.total_items, 1)) * 100, 1),
                "deprecated_percentage": round((freshness_report.deprecated_items / max(freshness_report.total_items, 1)) * 100, 1)
            }
        }
    
    async def _detect_deprecated_knowledge(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Detect deprecated knowledge items."""
        deprecated_items = await self.maintenance_system.detect_deprecated_knowledge()
        
        # Categorize by confidence level
        high_confidence = [item for item in deprecated_items if item['confidence'] >= 0.8]
        medium_confidence = [item for item in deprecated_items if 0.5 <= item['confidence'] < 0.8]
        low_confidence = [item for item in deprecated_items if item['confidence'] < 0.5]
        
        return {
            "deprecated_items_detected": len(deprecated_items),
            "high_confidence_deprecated": {
                "count": len(high_confidence),
                "items": high_confidence
            },
            "medium_confidence_deprecated": {
                "count": len(medium_confidence),
                "items": medium_confidence
            },
            "low_confidence_deprecated": {
                "count": len(low_confidence),
                "items": low_confidence
            },
            "recommendations": [
                "Review high confidence items first",
                "Verify medium confidence items manually",
                "Consider updating or removing deprecated content"
            ]
        }
    
    async def _submit_knowledge_improvement(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Submit knowledge improvement feedback."""
        knowledge_item_id = parameters["knowledge_item_id"]
        improvement_feedback = parameters["improvement_feedback"]
        
        # Process the improvement feedback
        result = await self.maintenance_system.process_user_improvement_feedback(
            knowledge_item_id, improvement_feedback
        )
        
        return {
            "improvement_submitted": result.get("feedback_processed", False),
            "knowledge_item_id": knowledge_item_id,
            "tasks_created": result.get("tasks_created", 0),
            "task_types": result.get("task_types", []),
            "feedback_summary": {
                "content_outdated": improvement_feedback.get("content_outdated", False),
                "missing_information": improvement_feedback.get("missing_information", False),
                "incorrect_information": improvement_feedback.get("incorrect_information", False),
                "has_suggestions": bool(improvement_feedback.get("suggestions")),
                "has_additional_context": bool(improvement_feedback.get("additional_context"))
            },
            "next_steps": [
                "Improvement tasks have been scheduled",
                "Tasks will be processed by the maintenance system",
                "You will be notified when improvements are completed"
            ] if result.get("feedback_processed") else [
                "There was an issue processing your feedback",
                "Please try again or contact support"
            ]
        }
    
    async def _get_maintenance_status(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get maintenance system status."""
        maintenance_stats = await self.maintenance_system.get_maintenance_statistics()
        
        return {
            "maintenance_system": maintenance_stats,
            "system_health": {
                "overall_status": "healthy" if maintenance_stats.get("system_status", {}).get("running", False) else "stopped",
                "freshness_score": maintenance_stats.get("freshness_report", {}).get("freshness_score", 0.0),
                "pending_tasks": maintenance_stats.get("pending_tasks", {}).get("total_pending", 0),
                "items_processed_today": maintenance_stats.get("system_status", {}).get("items_updated", 0)
            },
            "recommendations": maintenance_stats.get("freshness_report", {}).get("recommendations", [])
        }