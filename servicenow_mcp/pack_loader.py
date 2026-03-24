"""
Dynamic Pack Loader for ServiceNow MCP Server

This module provides dynamic loading capabilities for packs,
allowing for more flexible pack management and conditional loading.
"""

import importlib
import sys
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass
from .pack_registry import get_pack_registry, PackInfo, PackCategory
from .logging_config import get_logger


@dataclass
class LoadResult:
    """Result of pack loading operation"""
    success: bool
    pack_name: str
    error: Optional[str] = None
    module: Optional[Any] = None


class PackLoader:
    """Dynamic pack loader with dependency resolution"""
    
    def __init__(self):
        self.logger = get_logger()
        self.registry = get_pack_registry()
        self.loaded_packs: Dict[str, Any] = {}
        self.failed_packs: Set[str] = set()
    
    def load_pack(self, pack_name: str, force_reload: bool = False) -> LoadResult:
        """
        Load a single pack by name
        
        Args:
            pack_name: Name of the pack to load
            force_reload: Force reload even if already loaded
            
        Returns:
            LoadResult with success status and details
        """
        # Check if already loaded
        if pack_name in self.loaded_packs and not force_reload:
            return LoadResult(
                success=True,
                pack_name=pack_name,
                module=self.loaded_packs[pack_name]
            )
        
        # Check if previously failed
        if pack_name in self.failed_packs and not force_reload:
            return LoadResult(
                success=False,
                pack_name=pack_name,
                error="Previously failed to load"
            )
        
        # Get pack info from registry
        pack_info = self.registry.get_pack(pack_name)
        if not pack_info:
            error = f"Pack '{pack_name}' not found in registry"
            self.logger.error(error)
            return LoadResult(success=False, pack_name=pack_name, error=error)
        
        # Load dependencies first
        for dep in pack_info.dependencies:
            dep_result = self.load_pack(dep)
            if not dep_result.success:
                error = f"Failed to load dependency '{dep}' for pack '{pack_name}'"
                self.logger.error(error)
                return LoadResult(success=False, pack_name=pack_name, error=error)
        
        # Attempt to load the pack
        try:
            module_name = f"servicenow_mcp.packs.{pack_name}"
            
            if force_reload and module_name in sys.modules:
                # Reload existing module
                module = importlib.reload(sys.modules[module_name])
            else:
                # Import new module
                module = importlib.import_module(module_name)
            
            self.loaded_packs[pack_name] = module
            self.failed_packs.discard(pack_name)  # Remove from failed set if present
            
            self.logger.info(f"Successfully loaded pack: {pack_name}")
            return LoadResult(success=True, pack_name=pack_name, module=module)
            
        except ImportError as e:
            error = f"Import error loading pack '{pack_name}': {str(e)}"
            self.logger.error(error)
            self.failed_packs.add(pack_name)
            return LoadResult(success=False, pack_name=pack_name, error=error)
            
        except Exception as e:
            error = f"Unexpected error loading pack '{pack_name}': {str(e)}"
            self.logger.error(error)
            self.failed_packs.add(pack_name)
            return LoadResult(success=False, pack_name=pack_name, error=error)
    
    def load_packs_by_category(self, category: PackCategory) -> Dict[str, LoadResult]:
        """Load all packs in a specific category"""
        results = {}
        pack_names = self.registry.get_pack_names_by_category(category)
        
        for pack_name in pack_names:
            results[pack_name] = self.load_pack(pack_name)
        
        return results
    
    def load_all_packs(self) -> Dict[str, LoadResult]:
        """Load all registered packs"""
        results = {}
        
        for pack_name in self.registry.get_pack_names():
            results[pack_name] = self.load_pack(pack_name)
        
        return results
    
    def get_loaded_packs(self) -> List[str]:
        """Get list of successfully loaded pack names"""
        return list(self.loaded_packs.keys())
    
    def get_failed_packs(self) -> List[str]:
        """Get list of packs that failed to load"""
        return list(self.failed_packs)
    
    def get_pack_module(self, pack_name: str) -> Optional[Any]:
        """Get loaded pack module by name"""
        return self.loaded_packs.get(pack_name)
    
    def unload_pack(self, pack_name: str) -> bool:
        """
        Unload a pack (remove from loaded packs)
        Note: This doesn't actually unload the Python module from memory
        """
        if pack_name in self.loaded_packs:
            del self.loaded_packs[pack_name]
            self.logger.info(f"Unloaded pack: {pack_name}")
            return True
        return False
    
    def reload_pack(self, pack_name: str) -> LoadResult:
        """Reload a pack (force reload)"""
        return self.load_pack(pack_name, force_reload=True)
    
    def get_loading_summary(self) -> Dict[str, Any]:
        """Get summary of pack loading status"""
        total_packs = len(self.registry.get_pack_names())
        loaded_count = len(self.loaded_packs)
        failed_count = len(self.failed_packs)
        
        return {
            "total_registered": total_packs,
            "loaded": loaded_count,
            "failed": failed_count,
            "not_attempted": total_packs - loaded_count - failed_count,
            "success_rate": (loaded_count / total_packs * 100) if total_packs > 0 else 0,
            "loaded_packs": list(self.loaded_packs.keys()),
            "failed_packs": list(self.failed_packs),
            "by_category": self._get_category_summary()
        }
    
    def _get_category_summary(self) -> Dict[str, Dict[str, int]]:
        """Get loading summary by category"""
        summary = {}
        
        for category in self.registry.get_categories():
            pack_names = self.registry.get_pack_names_by_category(category)
            loaded = sum(1 for name in pack_names if name in self.loaded_packs)
            failed = sum(1 for name in pack_names if name in self.failed_packs)
            total = len(pack_names)
            
            summary[category.value] = {
                "total": total,
                "loaded": loaded,
                "failed": failed,
                "not_attempted": total - loaded - failed
            }
        
        return summary
    
    def validate_pack_health(self) -> Dict[str, Any]:
        """Validate health of loaded packs"""
        health_report = {
            "healthy_packs": [],
            "unhealthy_packs": [],
            "missing_functions": {},
            "validation_errors": []
        }
        
        for pack_name, module in self.loaded_packs.items():
            try:
                # Basic health check - ensure module has expected attributes
                if hasattr(module, '__name__'):
                    health_report["healthy_packs"].append(pack_name)
                else:
                    health_report["unhealthy_packs"].append(pack_name)
                    health_report["validation_errors"].append(
                        f"Pack '{pack_name}' missing __name__ attribute"
                    )
                
                # Check for common pack functions (this could be expanded)
                expected_functions = []  # Could be defined per pack type
                missing = []
                for func_name in expected_functions:
                    if not hasattr(module, func_name):
                        missing.append(func_name)
                
                if missing:
                    health_report["missing_functions"][pack_name] = missing
                    
            except Exception as e:
                health_report["unhealthy_packs"].append(pack_name)
                health_report["validation_errors"].append(
                    f"Error validating pack '{pack_name}': {str(e)}"
                )
        
        return health_report


# Global pack loader instance
_pack_loader: Optional[PackLoader] = None

def get_pack_loader() -> PackLoader:
    """Get the global pack loader instance"""
    global _pack_loader
    if _pack_loader is None:
        _pack_loader = PackLoader()
    return _pack_loader