"""
Dynamic REST API Generator

This service automatically generates REST API endpoints based on database schemas.
For each table in a user's database, it creates full CRUD operations:
- GET /table - List all records (with filtering, sorting, pagination)
- GET /table/{id} - Get single record
- POST /table - Create new record
- PUT /table/{id} - Update record
- DELETE /table/{id} - Delete record

This is the core feature that makes NovaStack competitive with Supabase!
"""

import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from dataclasses import dataclass

from fastapi import APIRouter, HTTPException, Query, Depends, Path, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, create_model
from sqlalchemy import text
import asyncpg
# import aiomysql  # TODO: Install for MySQL support

from app.services.schema_introspector import (
    DatabaseSchema, 
    TableInfo, 
    ColumnInfo, 
    DatabaseType,
    schema_introspector
)

logger = logging.getLogger(__name__)


@dataclass
class APIConfig:
    """Configuration for generated APIs"""
    max_page_size: int = 1000
    default_page_size: int = 20
    enable_bulk_operations: bool = True
    enable_file_uploads: bool = True
    rate_limit_per_minute: int = 1000


class QueryFilter:
    """Query filtering and sorting utilities"""
    
    @staticmethod
    def parse_filter_params(params: Dict[str, Any]) -> Dict[str, Any]:
        """Parse query parameters into database filters"""
        filters = {}
        
        for key, value in params.items():
            if key.startswith('_'):
                continue  # Skip internal parameters
            
            # Handle different filter operators
            if '.' in key:
                field, operator = key.split('.', 1)
                if operator == 'eq':
                    filters[field] = {'op': '=', 'value': value}
                elif operator == 'neq':
                    filters[field] = {'op': '!=', 'value': value}
                elif operator == 'gt':
                    filters[field] = {'op': '>', 'value': value}
                elif operator == 'gte':
                    filters[field] = {'op': '>=', 'value': value}
                elif operator == 'lt':
                    filters[field] = {'op': '<', 'value': value}
                elif operator == 'lte':
                    filters[field] = {'op': '<=', 'value': value}
                elif operator == 'like':
                    filters[field] = {'op': 'LIKE', 'value': f'%{value}%'}
                elif operator == 'in':
                    # Handle comma-separated values
                    values = value.split(',') if isinstance(value, str) else value
                    filters[field] = {'op': 'IN', 'value': values}
            else:
                # Default to equality
                filters[key] = {'op': '=', 'value': value}
        
        return filters
    
    @staticmethod
    def build_where_clause(filters: Dict[str, Any], database_type: DatabaseType) -> tuple:
        """Build SQL WHERE clause from filters"""
        if not filters:
            return "", []
        
        conditions = []
        params = []
        param_index = 1
        
        for field, filter_info in filters.items():
            op = filter_info['op']
            value = filter_info['value']
            
            if database_type == DatabaseType.POSTGRESQL:
                placeholder = f"${param_index}"
            else:  # MySQL
                placeholder = "%s"
            
            if op == 'IN':
                placeholders = ', '.join([placeholder] * len(value))
                conditions.append(f'"{field}" {op} ({placeholders})')
                params.extend(value)
                param_index += len(value)
            else:
                conditions.append(f'"{field}" {op} {placeholder}')
                params.append(value)
                param_index += 1
        
        where_clause = " WHERE " + " AND ".join(conditions)
        return where_clause, params


class DynamicAPIGenerator:
    """
    Main service for generating REST APIs from database schemas
    
    This creates FastAPI routers with full CRUD operations for each table.
    """
    
    def __init__(self, config: APIConfig = None):
        self.config = config or APIConfig()
        self.generated_apis = {}  # Cache for generated APIs
    
    async def generate_api_for_project(
        self, 
        project_id: str,
        connection_string: str,
        database_type: DatabaseType
    ) -> APIRouter:
        """
        Generate complete REST API for a database project
        
        Args:
            project_id: Unique project identifier
            connection_string: Database connection string
            database_type: Type of database (PostgreSQL/MySQL)
            
        Returns:
            FastAPI router with all CRUD endpoints
        """
        try:
            logger.info(f"Generating REST API for project {project_id}")
            
            # Introspect database schema
            schema = await schema_introspector.introspect_database(
                connection_string, database_type
            )
            
            # Generate API router
            router = APIRouter(
                prefix=f"/api/data/{project_id}",
                tags=[f"Data API - {schema.database_name}"]
            )
            
            # Generate endpoints for each table
            for table in schema.tables:
                await self._generate_table_endpoints(
                    router, table, connection_string, database_type
                )
            
            # Add metadata endpoints
            self._add_metadata_endpoints(router, schema)
            
            # Cache the generated API
            self.generated_apis[project_id] = {
                'router': router,
                'schema': schema,
                'connection_string': connection_string,
                'database_type': database_type,
                'generated_at': datetime.utcnow()
            }
            
            logger.info(f"Generated API with {len(schema.tables)} table endpoints")
            return router
            
        except Exception as e:
            logger.error(f"API generation failed: {str(e)}")
            raise
    
    async def _generate_table_endpoints(
        self,
        router: APIRouter,
        table: TableInfo,
        connection_string: str,
        database_type: DatabaseType
    ):
        """Generate CRUD endpoints for a single table"""
        
        table_name = table.name
        
        # Create Pydantic models for the table
        table_model = self._create_pydantic_model(table)
        create_model_class = self._create_insert_model(table)
        update_model_class = self._create_update_model(table)
        
        # LIST endpoint - GET /table
        @router.get(f"/{table_name}", response_model=Dict[str, Any])
        async def list_records(
            request: Request,
            offset: int = Query(0, ge=0),
            limit: int = Query(20, ge=1, le=1000),
            order: Optional[str] = Query(None),
            order_direction: str = Query("asc", regex="^(asc|desc)$")
        ):
            """List all records from table with filtering and pagination"""
            try:
                # Parse query parameters for filtering
                query_params = dict(request.query_params)
                filters = QueryFilter.parse_filter_params(query_params)
                
                # Build SQL query
                base_query = f'SELECT * FROM "{table_name}"'
                count_query = f'SELECT COUNT(*) FROM "{table_name}"'
                
                where_clause, params = QueryFilter.build_where_clause(filters, database_type)
                
                # Add WHERE clause if filters exist
                if where_clause:
                    base_query += where_clause
                    count_query += where_clause
                
                # Add ORDER BY
                if order and order in [col.name for col in table.columns]:
                    base_query += f' ORDER BY "{order}" {order_direction.upper()}'
                
                # Add LIMIT and OFFSET
                if database_type == DatabaseType.POSTGRESQL:
                    base_query += f' LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}'
                    params.extend([limit, offset])
                else:  # MySQL
                    base_query += f' LIMIT %s OFFSET %s'
                    params.extend([limit, offset])
                
                # Execute queries
                if database_type == DatabaseType.POSTGRESQL:
                    conn = await asyncpg.connect(connection_string)
                    try:
                        # Get data
                        rows = await conn.fetch(base_query, *params)
                        data = [dict(row) for row in rows]
                        
                        # Get total count
                        count_params = params[:-2]  # Remove limit and offset
                        count_result = await conn.fetchval(count_query, *count_params)
                        total = count_result or 0
                        
                    finally:
                        await conn.close()
                else:
                    # MySQL implementation would go here
                    data = []
                    total = 0
                
                return {
                    "data": data,
                    "count": len(data),
                    "total": total,
                    "offset": offset,
                    "limit": limit
                }
                
            except Exception as e:
                logger.error(f"List {table_name} failed: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Failed to list {table_name}")
        
        # GET endpoint - GET /table/{id}
        @router.get(f"/{table_name}/{{record_id}}", response_model=Dict[str, Any])
        async def get_record(record_id: str = Path(...)):
            """Get a single record by ID"""
            try:
                # Find primary key column
                pk_columns = table.primary_key
                if not pk_columns:
                    raise HTTPException(status_code=400, detail="Table has no primary key")
                
                pk_column = pk_columns[0]  # Use first primary key column
                
                if database_type == DatabaseType.POSTGRESQL:
                    conn = await asyncpg.connect(connection_string)
                    try:
                        query = f'SELECT * FROM "{table_name}" WHERE "{pk_column}" = $1'
                        row = await conn.fetchrow(query, record_id)
                        
                        if not row:
                            raise HTTPException(status_code=404, detail="Record not found")
                        
                        return dict(row)
                        
                    finally:
                        await conn.close()
                else:
                    # MySQL implementation
                    raise HTTPException(status_code=501, detail="MySQL not yet supported")
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Get {table_name} record failed: {str(e)}")
                raise HTTPException(status_code=500, detail="Failed to get record")
        
        # CREATE endpoint - POST /table
        @router.post(f"/{table_name}", response_model=Dict[str, Any])
        async def create_record(record_data: create_model_class):
            """Create a new record"""
            try:
                data = record_data.dict(exclude_unset=True)
                
                if not data:
                    raise HTTPException(status_code=400, detail="No data provided")
                
                columns = list(data.keys())
                values = list(data.values())
                
                if database_type == DatabaseType.POSTGRESQL:
                    conn = await asyncpg.connect(connection_string)
                    try:
                        # Build INSERT query
                        columns_str = ', '.join([f'"{col}"' for col in columns])
                        placeholders = ', '.join([f'${i+1}' for i in range(len(values))])
                        
                        query = f'INSERT INTO "{table_name}" ({columns_str}) VALUES ({placeholders}) RETURNING *'
                        row = await conn.fetchrow(query, *values)
                        
                        return dict(row)
                        
                    finally:
                        await conn.close()
                else:
                    # MySQL implementation
                    raise HTTPException(status_code=501, detail="MySQL not yet supported")
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Create {table_name} record failed: {str(e)}")
                raise HTTPException(status_code=500, detail="Failed to create record")
        
        # UPDATE endpoint - PUT /table/{id}
        @router.put(f"/{table_name}/{{record_id}}", response_model=Dict[str, Any])
        async def update_record(record_id: str, record_data: update_model_class):
            """Update an existing record"""
            try:
                data = record_data.dict(exclude_unset=True)
                
                if not data:
                    raise HTTPException(status_code=400, detail="No data provided")
                
                # Find primary key column
                pk_columns = table.primary_key
                if not pk_columns:
                    raise HTTPException(status_code=400, detail="Table has no primary key")
                
                pk_column = pk_columns[0]
                
                if database_type == DatabaseType.POSTGRESQL:
                    conn = await asyncpg.connect(connection_string)
                    try:
                        # Build UPDATE query
                        set_clauses = [f'"{col}" = ${i+1}' for i, col in enumerate(data.keys())]
                        set_clause = ', '.join(set_clauses)
                        
                        query = f'UPDATE "{table_name}" SET {set_clause} WHERE "{pk_column}" = ${len(data)+1} RETURNING *'
                        values = list(data.values()) + [record_id]
                        
                        row = await conn.fetchrow(query, *values)
                        
                        if not row:
                            raise HTTPException(status_code=404, detail="Record not found")
                        
                        return dict(row)
                        
                    finally:
                        await conn.close()
                else:
                    # MySQL implementation
                    raise HTTPException(status_code=501, detail="MySQL not yet supported")
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Update {table_name} record failed: {str(e)}")
                raise HTTPException(status_code=500, detail="Failed to update record")
        
        # DELETE endpoint - DELETE /table/{id}
        @router.delete(f"/{table_name}/{{record_id}}")
        async def delete_record(record_id: str):
            """Delete a record"""
            try:
                # Find primary key column
                pk_columns = table.primary_key
                if not pk_columns:
                    raise HTTPException(status_code=400, detail="Table has no primary key")
                
                pk_column = pk_columns[0]
                
                if database_type == DatabaseType.POSTGRESQL:
                    conn = await asyncpg.connect(connection_string)
                    try:
                        query = f'DELETE FROM "{table_name}" WHERE "{pk_column}" = $1 RETURNING *'
                        row = await conn.fetchrow(query, record_id)
                        
                        if not row:
                            raise HTTPException(status_code=404, detail="Record not found")
                        
                        return {"message": "Record deleted successfully", "deleted_record": dict(row)}
                        
                    finally:
                        await conn.close()
                else:
                    # MySQL implementation
                    raise HTTPException(status_code=501, detail="MySQL not yet supported")
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Delete {table_name} record failed: {str(e)}")
                raise HTTPException(status_code=500, detail="Failed to delete record")
    
    def _create_pydantic_model(self, table: TableInfo) -> type:
        """Create Pydantic model for table structure"""
        fields = {}
        
        for column in table.columns:
            # Map database types to Python types
            python_type = self._map_db_type_to_python(column.type)
            
            # Handle nullable fields
            if column.nullable:
                python_type = Optional[python_type]
            
            # Set default value
            default_value = ... if not column.nullable else None
            
            fields[column.name] = (python_type, default_value)
        
        # Create dynamic Pydantic model
        model_name = f"{table.name.title()}Model"
        return create_model(model_name, **fields)
    
    def _create_insert_model(self, table: TableInfo) -> type:
        """Create Pydantic model for INSERT operations"""
        fields = {}
        
        for column in table.columns:
            # Skip auto-increment columns for inserts
            if column.auto_increment:
                continue
            
            python_type = self._map_db_type_to_python(column.type)
            
            # Make nullable or has default
            if column.nullable or column.default_value:
                python_type = Optional[python_type]
                default_value = None
            else:
                default_value = ...
            
            fields[column.name] = (python_type, default_value)
        
        model_name = f"{table.name.title()}CreateModel"
        return create_model(model_name, **fields)
    
    def _create_update_model(self, table: TableInfo) -> type:
        """Create Pydantic model for UPDATE operations"""
        fields = {}
        
        for column in table.columns:
            # All fields optional for updates
            python_type = self._map_db_type_to_python(column.type)
            fields[column.name] = (Optional[python_type], None)
        
        model_name = f"{table.name.title()}UpdateModel"
        return create_model(model_name, **fields)
    
    def _map_db_type_to_python(self, db_type: str) -> type:
        """Map database types to Python types"""
        type_mapping = {
            'int': int,
            'integer': int,
            'bigint': int,
            'smallint': int,
            'varchar': str,
            'char': str,
            'text': str,
            'boolean': bool,
            'bool': bool,
            'float': float,
            'double': float,
            'decimal': float,
            'numeric': float,
            'datetime': datetime,
            'timestamp': datetime,
            'timestamptz': datetime,
            'date': datetime,
            'time': datetime,
            'json': dict,
            'jsonb': dict,
            'uuid': str
        }
        
        return type_mapping.get(db_type.lower(), str)
    
    def _add_metadata_endpoints(self, router: APIRouter, schema: DatabaseSchema):
        """Add metadata endpoints for schema information"""
        
        @router.get("/meta/schema")
        async def get_schema():
            """Get complete database schema"""
            return {
                "database_name": schema.database_name,
                "database_type": schema.database_type.value,
                "version": schema.version,
                "tables": [
                    {
                        "name": table.name,
                        "columns": [
                            {
                                "name": col.name,
                                "type": col.type,
                                "nullable": col.nullable,
                                "primary_key": col.primary_key
                            }
                            for col in table.columns
                        ],
                        "primary_key": table.primary_key
                    }
                    for table in schema.tables
                ]
            }
        
        @router.get("/meta/tables")
        async def get_tables():
            """Get list of all tables"""
            return {
                "tables": [
                    {
                        "name": table.name,
                        "column_count": len(table.columns),
                        "has_primary_key": bool(table.primary_key),
                        "comment": table.comment
                    }
                    for table in schema.tables
                ]
            }


# Global API generator instance
api_generator = DynamicAPIGenerator()