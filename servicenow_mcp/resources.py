"""
MCP Resources implementation for ServiceNow data exposure
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, AsyncGenerator
import asyncio
from datetime import datetime

from .models import TableResource, FieldResource, RecordResource, ScriptResource
from .async_client import AsyncServiceNowClient
from .config import Config
from .logging_config import get_logger
from .error_handler import ResourceNotFoundError, handle_errors


class ServiceNowResourceProvider:
    """Provides MCP resources for ServiceNow data"""
    
    def __init__(self):
        self.logger = get_logger()
        self._clients: Dict[str, AsyncServiceNowClient] = {}
    
    async def _get_client(self, env: str = "dev") -> AsyncServiceNowClient:
        """Get or create async client for environment"""
        if env not in self._clients:
            config = Config.for_env(env)
            self._clients[env] = AsyncServiceNowClient(
                config.instance_url,
                config.username,
                config.password
            )
        return self._clients[env]
    
    async def close_all_clients(self):
        """Close all client connections"""
        for client in self._clients.values():
            await client.close()
        self._clients.clear()
    
    # Table Resources
    @handle_errors("list_tables")
    async def list_tables(
        self, 
        env: str = "dev",
        limit: int = 100,
        name_filter: Optional[str] = None
    ) -> List[TableResource]:
        """List available ServiceNow tables"""
        client = await self._get_client(env)
        
        query = "sys_class_name=sys_db_object"
        if name_filter:
            query += f"^nameLIKE{name_filter}"
        
        async with client:
            response = await client.query_table(
                "sys_db_object",
                query=query,
                fields=["name", "label", "sys_id", "super_class", "number_ref", "is_extendable", "access"],
                limit=limit
            )
        
        tables = []
        for record in response.get("result", []):
            tables.append(TableResource(
                name=record.get("name", ""),
                label=record.get("label", ""),
                sys_id=record.get("sys_id", ""),
                super_class=record.get("super_class", {}).get("value") if record.get("super_class") else None,
                number_ref=record.get("number_ref", ""),
                is_extendable=record.get("is_extendable") == "true",
                access=record.get("access", "public"),
                read_access=True,  # Default permissions
                create_access=True,
                update_access=True,
                delete_access=True
            ))
        
        return tables
    
    @handle_errors("get_table")
    async def get_table(self, table_name: str, env: str = "dev") -> TableResource:
        """Get specific table information"""
        client = await self._get_client(env)
        
        async with client:
            response = await client.query_table(
                "sys_db_object",
                query=f"name={table_name}",
                fields=["name", "label", "sys_id", "super_class", "number_ref", "is_extendable", "access"],
                limit=1
            )
        
        records = response.get("result", [])
        if not records:
            raise ResourceNotFoundError(f"Table '{table_name}' not found", "table", table_name)
        
        record = records[0]
        return TableResource(
            name=record.get("name", ""),
            label=record.get("label", ""),
            sys_id=record.get("sys_id", ""),
            super_class=record.get("super_class", {}).get("value") if record.get("super_class") else None,
            number_ref=record.get("number_ref", ""),
            is_extendable=record.get("is_extendable") == "true",
            access=record.get("access", "public"),
            read_access=True,
            create_access=True,
            update_access=True,
            delete_access=True
        )
    
    # Field Resources
    @handle_errors("list_fields")
    async def list_fields(
        self, 
        table_name: str, 
        env: str = "dev",
        limit: int = 200
    ) -> List[FieldResource]:
        """List fields for a specific table"""
        client = await self._get_client(env)
        
        async with client:
            response = await client.query_table(
                "sys_dictionary",
                query=f"name={table_name}",
                fields=[
                    "element", "column_label", "name", "internal_type", 
                    "max_length", "mandatory", "read_only", "default_value", "reference"
                ],
                limit=limit
            )
        
        fields = []
        for record in response.get("result", []):
            # Get choices if it's a choice field
            choices = None
            if record.get("internal_type") == "choice":
                choices_response = await client.query_table(
                    "sys_choice",
                    query=f"name={table_name}^element={record.get('element')}",
                    fields=["label", "value"],
                    limit=50
                )
                choices = [choice.get("label", "") for choice in choices_response.get("result", [])]
            
            fields.append(FieldResource(
                name=record.get("element", ""),
                label=record.get("column_label", ""),
                table=record.get("name", ""),
                type=record.get("internal_type", ""),
                max_length=int(record.get("max_length", 0)) if record.get("max_length") else None,
                mandatory=record.get("mandatory") == "true",
                read_only=record.get("read_only") == "true",
                default_value=record.get("default_value"),
                reference=record.get("reference", {}).get("value") if record.get("reference") else None,
                choices=choices
            ))
        
        return fields
    
    @handle_errors("get_field")
    async def get_field(
        self, 
        table_name: str, 
        field_name: str, 
        env: str = "dev"
    ) -> FieldResource:
        """Get specific field information"""
        client = await self._get_client(env)
        
        async with client:
            response = await client.query_table(
                "sys_dictionary",
                query=f"name={table_name}^element={field_name}",
                fields=[
                    "element", "column_label", "name", "internal_type", 
                    "max_length", "mandatory", "read_only", "default_value", "reference"
                ],
                limit=1
            )
        
        records = response.get("result", [])
        if not records:
            raise ResourceNotFoundError(
                f"Field '{field_name}' not found in table '{table_name}'", 
                "field", 
                f"{table_name}.{field_name}"
            )
        
        record = records[0]
        
        # Get choices if it's a choice field
        choices = None
        if record.get("internal_type") == "choice":
            choices_response = await client.query_table(
                "sys_choice",
                query=f"name={table_name}^element={field_name}",
                fields=["label", "value"],
                limit=50
            )
            choices = [choice.get("label", "") for choice in choices_response.get("result", [])]
        
        return FieldResource(
            name=record.get("element", ""),
            label=record.get("column_label", ""),
            table=record.get("name", ""),
            type=record.get("internal_type", ""),
            max_length=int(record.get("max_length", 0)) if record.get("max_length") else None,
            mandatory=record.get("mandatory") == "true",
            read_only=record.get("read_only") == "true",
            default_value=record.get("default_value"),
            reference=record.get("reference", {}).get("value") if record.get("reference") else None,
            choices=choices
        )
    
    # Record Resources
    @handle_errors("list_records")
    async def list_records(
        self,
        table_name: str,
        query: str = "",
        fields: Optional[List[str]] = None,
        limit: int = 100,
        env: str = "dev"
    ) -> List[RecordResource]:
        """List records from a table"""
        client = await self._get_client(env)
        
        async with client:
            response = await client.query_table(
                table_name,
                query=query,
                fields=fields,
                limit=limit,
                display=True
            )
        
        records = []
        for record in response.get("result", []):
            # Extract display value (usually from number field or name field)
            display_value = (
                record.get("number", "") or 
                record.get("name", "") or 
                record.get("short_description", "") or
                record.get("sys_id", "")[:8]
            )
            
            records.append(RecordResource(
                sys_id=record.get("sys_id", ""),
                table=table_name,
                number=record.get("number"),
                display_value=str(display_value),
                sys_created_on=datetime.fromisoformat(
                    record.get("sys_created_on", "").replace("Z", "+00:00")
                ) if record.get("sys_created_on") else datetime.utcnow(),
                sys_updated_on=datetime.fromisoformat(
                    record.get("sys_updated_on", "").replace("Z", "+00:00")
                ) if record.get("sys_updated_on") else datetime.utcnow(),
                fields=record
            ))
        
        return records
    
    @handle_errors("get_record")
    async def get_record(
        self, 
        table_name: str, 
        sys_id: str, 
        fields: Optional[List[str]] = None,
        env: str = "dev"
    ) -> RecordResource:
        """Get specific record"""
        client = await self._get_client(env)
        
        async with client:
            record = await client.get_record(table_name, sys_id, fields)
        
        if not record or record.get("error"):
            raise ResourceNotFoundError(
                f"Record '{sys_id}' not found in table '{table_name}'",
                "record",
                f"{table_name}:{sys_id}"
            )
        
        # Extract display value
        display_value = (
            record.get("number", "") or 
            record.get("name", "") or 
            record.get("short_description", "") or
            sys_id[:8]
        )
        
        return RecordResource(
            sys_id=record.get("sys_id", sys_id),
            table=table_name,
            number=record.get("number"),
            display_value=str(display_value),
            sys_created_on=datetime.fromisoformat(
                record.get("sys_created_on", "").replace("Z", "+00:00")
            ) if record.get("sys_created_on") else datetime.utcnow(),
            sys_updated_on=datetime.fromisoformat(
                record.get("sys_updated_on", "").replace("Z", "+00:00")
            ) if record.get("sys_updated_on") else datetime.utcnow(),
            fields=record
        )
    
    # Script Resources
    @handle_errors("list_scripts")
    async def list_scripts(
        self,
        script_type: str = "business_rule",
        table_filter: Optional[str] = None,
        active_only: bool = True,
        limit: int = 100,
        env: str = "dev"
    ) -> List[ScriptResource]:
        """List scripts by type"""
        client = await self._get_client(env)
        
        # Map script types to tables
        script_tables = {
            "business_rule": "sys_script",
            "script_include": "sys_script_include", 
            "ui_script": "sys_ui_script",
            "client_script": "sys_script_client"
        }
        
        table = script_tables.get(script_type, "sys_script")
        
        query_parts = []
        if active_only:
            query_parts.append("active=true")
        if table_filter and script_type == "business_rule":
            query_parts.append(f"collection={table_filter}")
        
        query = "^".join(query_parts)
        
        fields = ["sys_id", "name", "active", "script"]
        if script_type == "business_rule":
            fields.extend(["collection", "when"])
        elif script_type == "script_include":
            fields.append("api_name")
        
        async with client:
            response = await client.query_table(table, query=query, fields=fields, limit=limit)
        
        scripts = []
        for record in response.get("result", []):
            scripts.append(ScriptResource(
                sys_id=record.get("sys_id", ""),
                name=record.get("name", ""),
                type=script_type,
                table=record.get("collection") if script_type == "business_rule" else None,
                active=record.get("active") == "true",
                script=record.get("script", ""),
                api_name=record.get("api_name") if script_type == "script_include" else None,
                when=record.get("when") if script_type == "business_rule" else None
            ))
        
        return scripts
    
    @handle_errors("get_script")
    async def get_script(
        self, 
        script_id: str, 
        script_type: str = "business_rule",
        env: str = "dev"
    ) -> ScriptResource:
        """Get specific script"""
        client = await self._get_client(env)
        
        # Map script types to tables
        script_tables = {
            "business_rule": "sys_script",
            "script_include": "sys_script_include",
            "ui_script": "sys_ui_script", 
            "client_script": "sys_script_client"
        }
        
        table = script_tables.get(script_type, "sys_script")
        
        fields = ["sys_id", "name", "active", "script"]
        if script_type == "business_rule":
            fields.extend(["collection", "when"])
        elif script_type == "script_include":
            fields.append("api_name")
        
        async with client:
            record = await client.get_record(table, script_id, fields)
        
        if not record or record.get("error"):
            raise ResourceNotFoundError(
                f"Script '{script_id}' not found",
                "script",
                script_id
            )
        
        return ScriptResource(
            sys_id=record.get("sys_id", script_id),
            name=record.get("name", ""),
            type=script_type,
            table=record.get("collection") if script_type == "business_rule" else None,
            active=record.get("active") == "true",
            script=record.get("script", ""),
            api_name=record.get("api_name") if script_type == "script_include" else None,
            when=record.get("when") if script_type == "business_rule" else None
        )
    
    # Resource streaming for large datasets
    async def stream_records(
        self,
        table_name: str,
        query: str = "",
        fields: Optional[List[str]] = None,
        batch_size: int = 100,
        env: str = "dev"
    ) -> AsyncGenerator[RecordResource, None]:
        """Stream records from a table in batches"""
        client = await self._get_client(env)
        offset = 0
        
        async with client:
            while True:
                response = await client.query_table(
                    table_name,
                    query=query,
                    fields=fields,
                    limit=batch_size,
                    offset=offset,
                    display=True
                )
                
                records = response.get("result", [])
                if not records:
                    break
                
                for record in records:
                    display_value = (
                        record.get("number", "") or 
                        record.get("name", "") or 
                        record.get("short_description", "") or
                        record.get("sys_id", "")[:8]
                    )
                    
                    yield RecordResource(
                        sys_id=record.get("sys_id", ""),
                        table=table_name,
                        number=record.get("number"),
                        display_value=str(display_value),
                        sys_created_on=datetime.fromisoformat(
                            record.get("sys_created_on", "").replace("Z", "+00:00")
                        ) if record.get("sys_created_on") else datetime.utcnow(),
                        sys_updated_on=datetime.fromisoformat(
                            record.get("sys_updated_on", "").replace("Z", "+00:00")
                        ) if record.get("sys_updated_on") else datetime.utcnow(),
                        fields=record
                    )
                
                offset += batch_size
                
                # If we got fewer records than requested, we're done
                if len(records) < batch_size:
                    break


# Global resource provider instance
_resource_provider: Optional[ServiceNowResourceProvider] = None

def get_resource_provider() -> ServiceNowResourceProvider:
    """Get the global resource provider instance"""
    global _resource_provider
    if _resource_provider is None:
        _resource_provider = ServiceNowResourceProvider()
    return _resource_provider