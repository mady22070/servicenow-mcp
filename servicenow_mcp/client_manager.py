"""
ServiceNow Client Manager - Handles client lifecycle and connection pooling
"""

from typing import Dict, Optional
from .config import Config
from .servicenow_client import ServiceNowClient


class ServiceNowClientManager:
    """Manages ServiceNow client instances with connection pooling and lifecycle management"""
    
    def __init__(self):
        self._clients: Dict[str, ServiceNowClient] = {}
    
    def get_client(self, env: Optional[str] = None) -> ServiceNowClient:
        """
        Get or create a ServiceNow client for the specified environment
        
        Args:
            env: Environment name (dev, test, prod). Defaults to 'dev'
            
        Returns:
            ServiceNowClient instance for the environment
            
        Raises:
            ConfigurationError: If environment configuration is invalid
        """
        env_key = (env or "dev").lower()
        
        if env_key not in self._clients:
            try:
                config = Config.for_env(env_key)
                self._clients[env_key] = ServiceNowClient(
                    config.instance_url, 
                    config.username, 
                    config.password
                )
            except Exception as e:
                raise ConfigurationError(f"Failed to create client for environment '{env_key}': {e}")
        
        return self._clients[env_key]
    
    def clear_client(self, env: str) -> bool:
        """
        Clear cached client for environment (useful for credential rotation)
        
        Args:
            env: Environment name to clear
            
        Returns:
            True if client was cleared, False if not found
        """
        env_key = env.lower()
        if env_key in self._clients:
            # Optionally call cleanup on client if it has such method
            client = self._clients.pop(env_key)
            if hasattr(client, 'close'):
                client.close()
            return True
        return False
    
    def clear_all_clients(self) -> int:
        """
        Clear all cached clients
        
        Returns:
            Number of clients cleared
        """
        count = len(self._clients)
        for client in self._clients.values():
            if hasattr(client, 'close'):
                client.close()
        self._clients.clear()
        return count
    
    def get_active_environments(self) -> List[str]:
        """Get list of environments with active clients"""
        return list(self._clients.keys())
    
    def health_check(self, env: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform health check on client(s)
        
        Args:
            env: Specific environment to check, or None for all
            
        Returns:
            Health status information
        """
        if env:
            environments = [env.lower()]
        else:
            environments = list(self._clients.keys())
        
        results = {}
        for env_key in environments:
            if env_key in self._clients:
                try:
                    client = self._clients[env_key]
                    # Simple health check - query sys_properties table
                    response = client.query_table("sys_properties", limit=1)
                    results[env_key] = {
                        "status": "healthy",
                        "response_time": getattr(response, 'elapsed', None),
                        "last_checked": "now"
                    }
                except Exception as e:
                    results[env_key] = {
                        "status": "unhealthy", 
                        "error": str(e),
                        "last_checked": "now"
                    }
            else:
                results[env_key] = {"status": "not_initialized"}
        
        return results


class ConfigurationError(Exception):
    """Raised when there's an issue with ServiceNow configuration"""
    pass


# Global client manager instance
client_manager = ServiceNowClientManager()