"""
Production vector database implementation using ChromaDB.

Provides semantic search capabilities for ServiceNow knowledge and best practices.
Supports multiple embedding models and intelligent knowledge retrieval.
"""

import logging
import os
import asyncio
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import hashlib
import json

try:
    import chromadb
    from chromadb.config import Settings
    from sentence_transformers import SentenceTransformer
    import openai
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False
    chromadb = None
    SentenceTransformer = None
    openai = None

logger = logging.getLogger(__name__)


@dataclass
class VectorDBConfig:
    """Configuration for vector database."""
    embedding_model: str = "all-MiniLM-L6-v2"  # Default to local model
    openai_model: str = "text-embedding-ada-002"
    use_openai: bool = False
    dimension: int = 384  # Default for all-MiniLM-L6-v2
    similarity_threshold: float = 0.7
    max_results: int = 10
    persist_directory: str = ".chroma_db"
    collection_name: str = "servicenow_knowledge"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    cache_embeddings: bool = True
    embedding_cache_ttl: int = 3600  # 1 hour


@dataclass
class Document:
    """Document structure for vector database."""
    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class SearchResult:
    """Search result structure."""
    document: Document
    score: float
    rank: int


class EmbeddingGenerator:
    """Handles embedding generation with multiple model support."""
    
    def __init__(self, config: VectorDBConfig):
        self.config = config
        self._local_model = None
        self._embedding_cache = {}
        
        if config.use_openai:
            openai.api_key = os.getenv("OPENAI_API_KEY")
            if not openai.api_key:
                logger.warning("OpenAI API key not found, falling back to local model")
                self.config.use_openai = False
    
    def _get_local_model(self):
        """Lazy load local embedding model."""
        if self._local_model is None:
            if not DEPENDENCIES_AVAILABLE:
                raise ImportError("sentence-transformers not available")
            self._local_model = SentenceTransformer(self.config.embedding_model)
        return self._local_model
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text."""
        return hashlib.md5(text.encode()).hexdigest()
    
    def _is_cache_valid(self, cache_entry: Dict) -> bool:
        """Check if cache entry is still valid."""
        if not self.config.cache_embeddings:
            return False
        
        created_at = cache_entry.get("created_at")
        if not created_at:
            return False
        
        ttl = timedelta(seconds=self.config.embedding_cache_ttl)
        return datetime.now() - created_at < ttl
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text."""
        if not text.strip():
            return [0.0] * self.config.dimension
        
        # Check cache first
        cache_key = self._get_cache_key(text)
        if cache_key in self._embedding_cache:
            cache_entry = self._embedding_cache[cache_key]
            if self._is_cache_valid(cache_entry):
                return cache_entry["embedding"]
        
        try:
            if self.config.use_openai and openai.api_key:
                embedding = await self._generate_openai_embedding(text)
            else:
                embedding = await self._generate_local_embedding(text)
            
            # Cache the result
            if self.config.cache_embeddings:
                self._embedding_cache[cache_key] = {
                    "embedding": embedding,
                    "created_at": datetime.now()
                }
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return [0.0] * self.config.dimension
    
    async def _generate_openai_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI API."""
        try:
            response = await asyncio.to_thread(
                openai.embeddings.create,
                model=self.config.openai_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}")
            # Fallback to local model
            return await self._generate_local_embedding(text)
    
    async def _generate_local_embedding(self, text: str) -> List[float]:
        """Generate embedding using local model."""
        model = self._get_local_model()
        embedding = await asyncio.to_thread(model.encode, text)
        return embedding.tolist()


class ProductionVectorDB:
    """Production vector database implementation using ChromaDB."""
    
    def __init__(self, config: VectorDBConfig = None):
        if not DEPENDENCIES_AVAILABLE:
            raise ImportError(
                "ChromaDB dependencies not available. "
                "Install with: pip install chromadb sentence-transformers"
            )
        
        self.config = config or VectorDBConfig()
        self.embedding_generator = EmbeddingGenerator(self.config)
        self._client = None
        self._collection = None
        
        logger.info(f"Initializing production vector database with {self.config.embedding_model}")
    
    def _get_client(self):
        """Lazy initialize ChromaDB client."""
        if self._client is None:
            settings = Settings(
                persist_directory=self.config.persist_directory,
                anonymized_telemetry=False
            )
            self._client = chromadb.PersistentClient(settings=settings)
        return self._client
    
    def _get_collection(self):
        """Get or create ChromaDB collection."""
        if self._collection is None:
            client = self._get_client()
            try:
                self._collection = client.get_collection(
                    name=self.config.collection_name
                )
            except Exception:
                # Collection doesn't exist, create it
                self._collection = client.create_collection(
                    name=self.config.collection_name,
                    metadata={"description": "ServiceNow knowledge and best practices"}
                )
        return self._collection
    
    async def add_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Add documents to the vector database."""
        if not documents:
            return {"processed": 0, "added": 0, "errors": 0}
        
        collection = self._get_collection()
        processed = 0
        added = 0
        errors = 0
        
        batch_ids = []
        batch_embeddings = []
        batch_metadatas = []
        batch_documents = []
        
        for doc_data in documents:
            try:
                # Create document object
                doc = Document(
                    id=doc_data.get("id", self._generate_doc_id(doc_data["content"])),
                    content=doc_data["content"],
                    metadata=doc_data.get("metadata", {}),
                    created_at=datetime.now()
                )
                
                # Generate embedding
                embedding = await self.embedding_generator.generate_embedding(doc.content)
                
                # Prepare for batch insert
                batch_ids.append(doc.id)
                batch_embeddings.append(embedding)
                batch_metadatas.append({
                    **doc.metadata,
                    "created_at": doc.created_at.isoformat(),
                    "content_length": len(doc.content)
                })
                batch_documents.append(doc.content)
                
                processed += 1
                
            except Exception as e:
                logger.error(f"Error processing document: {e}")
                errors += 1
        
        # Batch insert to ChromaDB
        if batch_ids:
            try:
                collection.add(
                    ids=batch_ids,
                    embeddings=batch_embeddings,
                    metadatas=batch_metadatas,
                    documents=batch_documents
                )
                added = len(batch_ids)
                logger.info(f"Added {added} documents to vector database")
            except Exception as e:
                logger.error(f"Error adding documents to ChromaDB: {e}")
                errors += processed
                added = 0
        
        return {
            "processed": processed,
            "added": added,
            "errors": errors
        }
    
    async def search_similar(self, query: str, filters: Dict[str, Any] = None,
                           max_results: int = None, threshold: float = None) -> List[SearchResult]:
        """Search for similar documents."""
        if not query.strip():
            return []
        
        max_results = max_results or self.config.max_results
        threshold = threshold or self.config.similarity_threshold
        
        try:
            # Generate query embedding
            query_embedding = await self.embedding_generator.generate_embedding(query)
            
            # Prepare ChromaDB query
            collection = self._get_collection()
            where_clause = self._build_where_clause(filters) if filters else None
            
            # Perform search
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=max_results,
                where=where_clause
            )
            
            # Process results
            search_results = []
            if results["ids"] and results["ids"][0]:
                for i, doc_id in enumerate(results["ids"][0]):
                    # Calculate similarity score (ChromaDB returns distances)
                    distance = results["distances"][0][i]
                    similarity = 1 - distance  # Convert distance to similarity
                    
                    if similarity >= threshold:
                        document = Document(
                            id=doc_id,
                            content=results["documents"][0][i],
                            metadata=results["metadatas"][0][i] or {}
                        )
                        
                        search_results.append(SearchResult(
                            document=document,
                            score=similarity,
                            rank=i + 1
                        ))
            
            logger.info(f"Found {len(search_results)} similar documents for query")
            return search_results
            
        except Exception as e:
            logger.error(f"Error searching vector database: {e}")
            return []
    
    async def update_document(self, doc_id: str, content: str = None, 
                            metadata: Dict[str, Any] = None) -> bool:
        """Update an existing document."""
        try:
            collection = self._get_collection()
            
            # Get existing document
            existing = collection.get(ids=[doc_id])
            if not existing["ids"]:
                logger.warning(f"Document {doc_id} not found for update")
                return False
            
            # Prepare updates
            update_data = {}
            
            if content is not None:
                # Generate new embedding for updated content
                embedding = await self.embedding_generator.generate_embedding(content)
                update_data["embeddings"] = [embedding]
                update_data["documents"] = [content]
            
            if metadata is not None:
                current_metadata = existing["metadatas"][0] or {}
                updated_metadata = {
                    **current_metadata,
                    **metadata,
                    "updated_at": datetime.now().isoformat()
                }
                update_data["metadatas"] = [updated_metadata]
            
            # Update in ChromaDB
            collection.update(
                ids=[doc_id],
                **update_data
            )
            
            logger.info(f"Updated document {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating document {doc_id}: {e}")
            return False
    
    async def delete_document(self, doc_id: str) -> bool:
        """Delete a document from the database."""
        try:
            collection = self._get_collection()
            collection.delete(ids=[doc_id])
            logger.info(f"Deleted document {doc_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting document {doc_id}: {e}")
            return False
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection."""
        try:
            collection = self._get_collection()
            count = collection.count()
            
            return {
                "total_documents": count,
                "collection_name": self.config.collection_name,
                "embedding_model": self.config.embedding_model,
                "dimension": self.config.dimension
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {}
    
    def _generate_doc_id(self, content: str) -> str:
        """Generate a unique document ID based on content."""
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _build_where_clause(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Build ChromaDB where clause from filters."""
        where_clause = {}
        
        for key, value in filters.items():
            if isinstance(value, (str, int, float, bool)):
                where_clause[key] = {"$eq": value}
            elif isinstance(value, list):
                where_clause[key] = {"$in": value}
            elif isinstance(value, dict):
                # Support for range queries, etc.
                where_clause[key] = value
        
        return where_clause


class VectorDBStub:
    """Fallback stub implementation when dependencies are not available."""
    
    def __init__(self, config: VectorDBConfig = None):
        self.config = config or VectorDBConfig()
        logger.warning("Using vector database stub - ChromaDB dependencies not available")
    
    async def search_similar(self, query: str, filters: Dict[str, Any] = None,
                           max_results: int = None, threshold: float = None) -> List[SearchResult]:
        """Stub search method - returns empty results."""
        logger.warning("Vector search called on stub implementation - returning empty results")
        return []
    
    async def add_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Stub add documents method."""
        logger.warning("Add documents called on stub implementation - no action taken")
        return {"processed": 0, "added": 0, "errors": 0}
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Stub embedding generation - returns zeros."""
        logger.warning("Embedding generation called on stub implementation - returning zeros")
        return [0.0] * self.config.dimension
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Stub collection stats - returns empty stats."""
        logger.warning("Collection stats called on stub implementation - returning empty stats")
        return {
            "total_documents": 0,
            "collection_name": self.config.collection_name,
            "embedding_model": self.config.embedding_model,
            "dimension": self.config.dimension
        }


# Global instance
_vector_db_instance = None


def get_vector_db(config: VectorDBConfig = None) -> Union[ProductionVectorDB, VectorDBStub]:
    """Get vector database instance."""
    global _vector_db_instance
    if _vector_db_instance is None:
        try:
            if DEPENDENCIES_AVAILABLE:
                _vector_db_instance = ProductionVectorDB(config)
            else:
                _vector_db_instance = VectorDBStub(config)
        except Exception as e:
            logger.error(f"Error initializing vector database: {e}")
            _vector_db_instance = VectorDBStub(config)
    
    return _vector_db_instance