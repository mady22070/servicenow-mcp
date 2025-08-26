"""
Client factory for managing ServiceNow client instances
"""

from __future__ import annotations
from typing import Dict, Optional, Union
from .config import Config
from .servicenow_client import ServiceNowClient
from .async_client import AsyncServiceNowClient
from .logging_config import get_logger


class ServiceNowClientFactory:
    """Factory for creating and managing ServiceNow client instances"""
    
    def __init__(self):
        self.logger = get_logger()
        self._sync_clients: Dict[str, ServiceNowClient] = {}
        self._async_clients: Dict[str, AsyncServiceNowClient] = {}
    
    def get_sync_client(self, env: Optional[str] = None) -> ServiceNowClient:
        """Get or create synchronous ServiceNow client for environment"""
        key = (env or "dev").lower()
        
        if key not in self._sync_clients:
            cfg = Config.for_env(key)
            self._sync_clients[key] = ServiceNowClient(
                cfg.instance_url, 
                cfg.username, 
                cfg.password
            )
            self.logger.info(f"Created sync ServiceNow client for environment: {key}")
        
        return self._sync_clients[key]
    
    async def get_async_client(self, env: Optional[str] = None) -> AsyncServiceNowClient:
        """Get or create async ServiceNow client for environment"""
        key = (env or "dev").lower()
        
        if key not in self._async_clients:
            cfg = Config.for_env(key)
            self._async_clients[key] = AsyncServiceNowClient(
                cfg.instance_url, 
                cfg.username, 
                cfg.password
            )
            self.logger.info(f"Created async ServiceNow client for environment: {key}")
        
        return self._async_clients[key]
    
    def clear_clients(self, env: Optional[str] = None):
        """Clear client cache for environment or all environments"""
        if env:
            key = env.lower()
            self._sync_clients.pop(key, None)
            self._async_clients.pop(key, None)
            self.logger.info(f"Cleared clients for environment: {key}")
        else:
            self._sync_clients.clear()
            self._async_clients.clear()
            self.logger.info("Cleared all client caches")
    
    async def close_all_async_clients(self):
        """Close all async client connections"""
        for client in self._async_clients.values():
            await client.close()
        self._async_clients.clear()
        self.logger.info("Closed all async client connections")


# Global factory instance
_client_factory: Optional[ServiceNowClientFactory] = None

def get_client_factory() -> ServiceNowClientFactory:
    """Get the global client factory instance"""
    global _client_factory
    if _client_factory is None:
        _client_factory = ServiceNowClientFactory()
    return _client_factory