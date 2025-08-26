"""
Async ServiceNow client with improved performance and error handling
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Union
import asyncio
import aiohttp
import time
from datetime import datetime, timedelta

from .models import MCPResponse
from .error_handler import ServiceNowError, TimeoutError, AuthenticationError
from .logging_config import get_logger, LogContext


class AsyncServiceNowClient:
    """Async ServiceNow client with connection pooling and retry logic"""
    
    def __init__(
        self, 
        instance_url: str, 
        username: str, 
        password: str,
        timeout: int = 30,
        max_connections: int = 10,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        self.base_url = instance_url.rstrip("/")
        self.auth = aiohttp.BasicAuth(username, password)
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.logger = get_logger()
        
        # Connection pool configuration
        self.connector = aiohttp.TCPConnector(
            limit=max_connections,
            limit_per_host=max_connections,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )
        
        self._session: Optional[aiohttp.ClientSession] = None
        self._closed = False
    
    async def __aenter__(self):
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def _ensure_session(self):
        """Ensure session is created and not closed"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                connector=self.connector,
                timeout=self.timeout,
                auth=self.auth,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "User-Agent": "ServiceNow-MCP-Client/0.8.0"
                }
            )
            self._closed = False
    
    async def close(self):
        """Close the client session"""
        if self._session and not self._session.closed:
            await self._session.close()
        if self.connector:
            await self.connector.close()
        self._closed = True
    
    def _url(self, path: str) -> str:
        """Build full URL from path"""
        if path.startswith("http"):
            return path
        return f"{self.base_url}{path}"
    
    async def _request_with_retry(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Make HTTP request with retry logic"""
        await self._ensure_session()
        
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                start_time = time.time()
                
                async with self._session.request(method, url, **kwargs) as response:
                    duration_ms = (time.time() - start_time) * 1000
                    
                    # Log request
                    with LogContext(self.logger, 
                                  operation=f"{method} {url}",
                                  status_code=response.status,
                                  duration_ms=round(duration_ms, 2),
                                  attempt=attempt + 1):
                        
                        if response.status == 401:
                            self.logger.error("Authentication failed")
                            raise AuthenticationError("Invalid credentials or session expired")
                        
                        if response.status >= 500 and attempt < self.max_retries:
                            self.logger.warning(f"Server error {response.status}, retrying...")
                            await asyncio.sleep(self.retry_delay * (2 ** attempt))
                            continue
                        
                        if response.status >= 400:
                            error_text = await response.text()
                            self.logger.error(f"HTTP {response.status}: {error_text}")
                            raise ServiceNowError(
                                f"HTTP {response.status}: {error_text}",
                                status_code=response.status
                            )
                        
                        # Parse JSON response
                        try:
                            data = await response.json()
                            self.logger.debug("Request successful")
                            return data
                        except Exception as e:
                            text = await response.text()
                            self.logger.error(f"Failed to parse JSON response: {e}")
                            return {
                                "error": "invalid_json",
                                "status": response.status,
                                "text": text[:400]
                            }
            
            except asyncio.TimeoutError as e:
                last_exception = TimeoutError(f"Request timeout after {self.timeout.total}s")
                self.logger.error(f"Request timeout on attempt {attempt + 1}")
                
            except aiohttp.ClientError as e:
                last_exception = ServiceNowError(f"Client error: {str(e)}")
                self.logger.error(f"Client error on attempt {attempt + 1}: {e}")
                
            except Exception as e:
                last_exception = e
                self.logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
            
            if attempt < self.max_retries:
                await asyncio.sleep(self.retry_delay * (2 ** attempt))
        
        # All retries failed
        if last_exception:
            raise last_exception
        else:
            raise ServiceNowError("All retry attempts failed")
    
    # Core HTTP methods
    async def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Async GET request"""
        return await self._request_with_retry("GET", self._url(path), params=params)
    
    async def post(self, path: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Async POST request"""
        return await self._request_with_retry("POST", self._url(path), json=data)
    
    async def patch(self, path: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Async PATCH request"""
        return await self._request_with_retry("PATCH", self._url(path), json=data)
    
    async def delete(self, path: str) -> Dict[str, Any]:
        """Async DELETE request"""
        return await self._request_with_retry("DELETE", self._url(path))
    
    # ServiceNow Table API methods
    async def create_record(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a record in ServiceNow table"""
        response = await self.post(f"/api/now/table/{table}", data)
        return response.get("result", response)
    
    async def get_record(
        self, 
        table: str, 
        sys_id: str, 
        fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get a record from ServiceNow table"""
        params = {}
        if fields:
            params["sysparm_fields"] = ",".join(fields)
        
        response = await self.get(f"/api/now/table/{table}/{sys_id}", params)
        return response.get("result", response)
    
    async def update_record(
        self, 
        table: str, 
        sys_id: str, 
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a record in ServiceNow table"""
        response = await self.patch(f"/api/now/table/{table}/{sys_id}", data)
        return response.get("result", response)
    
    async def delete_record(self, table: str, sys_id: str) -> Dict[str, Any]:
        """Delete a record from ServiceNow table"""
        try:
            await self.delete(f"/api/now/table/{table}/{sys_id}")
            return {"deleted": True, "sys_id": sys_id}
        except Exception as e:
            return {"deleted": False, "error": str(e), "sys_id": sys_id}
    
    async def query_table(
        self,
        table: str,
        query: str = "",
        fields: Optional[List[str]] = None,
        limit: int = 100,
        display: bool = False,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Query records from ServiceNow table"""
        params = {
            "sysparm_limit": str(limit),
            "sysparm_offset": str(offset)
        }
        
        if query:
            params["sysparm_query"] = query
        if fields:
            params["sysparm_fields"] = ",".join(fields)
        if display:
            params["sysparm_display_value"] = "all"
        
        response = await self.get(f"/api/now/table/{table}", params)
        return response.get("result", response)
    
    async def stats(
        self,
        table: str,
        query: str = "",
        group_by: Optional[List[str]] = None,
        count: bool = True,
        sum_fields: Optional[List[str]] = None,
        avg_fields: Optional[List[str]] = None,
        min_fields: Optional[List[str]] = None,
        max_fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get statistics from ServiceNow table"""
        params = {}
        
        if query:
            params["sysparm_query"] = query
        if group_by:
            params["sysparm_group_by"] = ",".join(group_by)
        if count:
            params["sysparm_count"] = "true"
        if sum_fields:
            params["sysparm_sum_fields"] = ",".join(sum_fields)
        if avg_fields:
            params["sysparm_avg_fields"] = ",".join(avg_fields)
        if min_fields:
            params["sysparm_min_fields"] = ",".join(min_fields)
        if max_fields:
            params["sysparm_max_fields"] = ",".join(max_fields)
        
        return await self.get(f"/api/now/stats/{table}", params)
    
    # Batch operations
    async def batch_create(
        self, 
        table: str, 
        records: List[Dict[str, Any]],
        batch_size: int = 100
    ) -> List[Dict[str, Any]]:
        """Create multiple records in batches"""
        results = []
        
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            batch_tasks = [
                self.create_record(table, record) 
                for record in batch
            ]
            
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    results.append({"error": str(result)})
                else:
                    results.append(result)
        
        return results
    
    async def batch_query(
        self,
        queries: List[Dict[str, Any]],
        max_concurrent: int = 5
    ) -> List[Dict[str, Any]]:
        """Execute multiple queries concurrently"""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def execute_query(query_params):
            async with semaphore:
                return await self.query_table(**query_params)
        
        tasks = [execute_query(query) for query in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return [
            result if not isinstance(result, Exception) 
            else {"error": str(result)}
            for result in results
        ]
    
    # Health check
    async def health_check(self) -> Dict[str, Any]:
        """Check ServiceNow instance health"""
        try:
            start_time = time.time()
            
            # Simple query to test connectivity
            await self.query_table("sys_user", limit=1)
            
            response_time = (time.time() - start_time) * 1000
            
            return {
                "status": "healthy",
                "response_time_ms": round(response_time, 2),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }