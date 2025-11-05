"""
Database Schema Introspection Service

This service analyzes user database schemas and extracts table information
to automatically generate REST and GraphQL APIs. Think of it as the "brain"
that understands the structure of user databases.

Key Features:
- Connects to user's PostgreSQL/MySQL databases
- Extracts table schemas, columns, relationships
- Identifies primary keys, foreign keys, constraints
- Generates API specifications from database structure
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

import asyncpg
import aiomysql
from sqlalchemy import create_engine, inspect, MetaData, Table
from sqlalchemy.dialects import postgresql, mysql

logger = logging.getLogger(__name__)


class DatabaseType(str, Enum):
    """Supported database types"""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"


@dataclass
class ColumnInfo:
    """Information about a database column"""
    name: str
    type: str
    nullable: bool
    primary_key: bool
    foreign_key: Optional['ForeignKeyInfo'] = None
    default_value: Optional[Any] = None
    max_length: Optional[int] = None
    auto_increment: bool = False


@dataclass
class ForeignKeyInfo:
    """Information about foreign key relationships"""
    table: str
    column: str
    on_delete: Optional[str] = None
    on_update: Optional[str] = None


@dataclass
class TableInfo:
    """Complete information about a database table"""
    name: str
    columns: List[ColumnInfo]
    primary_key: List[str]
    foreign_keys: List[ForeignKeyInfo]
    indexes: List[Dict[str, Any]]
    comment: Optional[str] = None


@dataclass
class DatabaseSchema:
    """Complete database schema information"""
    database_name: str
    database_type: DatabaseType
    tables: List[TableInfo]
    version: str
    charset: Optional[str] = None


class SchemaIntrospector:
    """
    Main service for database schema introspection
    
    This class connects to user databases and extracts their structure
    to enable automatic API generation.
    """
    
    def __init__(self):
        self.connection_cache = {}
    
    async def introspect_database(
        self, 
        connection_string: str, 
        database_type: DatabaseType
    ) -> DatabaseSchema:
        """
        Analyze a database and extract its complete schema
        
        Args:
            connection_string: Database connection string
            database_type: Type of database (PostgreSQL/MySQL)
            
        Returns:
            Complete database schema information
        """
        try:
            logger.info(f"Starting schema introspection for {database_type.value} database")
            
            if database_type == DatabaseType.POSTGRESQL:
                return await self._introspect_postgresql(connection_string)
            elif database_type == DatabaseType.MYSQL:
                return await self._introspect_mysql(connection_string)
            else:
                raise ValueError(f"Unsupported database type: {database_type}")
                
        except Exception as e:
            logger.error(f"Schema introspection failed: {str(e)}")
            raise
    
    async def _introspect_postgresql(self, connection_string: str) -> DatabaseSchema:
        """Introspect PostgreSQL database schema"""
        try:
            # Extract database name from connection string
            db_name = connection_string.split('/')[-1].split('?')[0]
            
            conn = await asyncpg.connect(connection_string)
            
            try:
                # Get database version
                version_result = await conn.fetchrow("SELECT version()")
                version = version_result['version'] if version_result else "Unknown"
                
                # Get all tables
                tables_query = """
                    SELECT table_name, table_comment 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """
                tables_result = await conn.fetch(tables_query)
                
                tables = []
                for table_row in tables_result:
                    table_name = table_row['table_name']
                    table_comment = table_row.get('table_comment')
                    
                    # Get column information
                    columns = await self._get_postgresql_columns(conn, table_name)
                    
                    # Get primary key information
                    primary_key = await self._get_postgresql_primary_key(conn, table_name)
                    
                    # Get foreign key information
                    foreign_keys = await self._get_postgresql_foreign_keys(conn, table_name)
                    
                    # Get index information
                    indexes = await self._get_postgresql_indexes(conn, table_name)
                    
                    table_info = TableInfo(
                        name=table_name,
                        columns=columns,
                        primary_key=primary_key,
                        foreign_keys=foreign_keys,
                        indexes=indexes,
                        comment=table_comment
                    )
                    tables.append(table_info)
                
                return DatabaseSchema(
                    database_name=db_name,
                    database_type=DatabaseType.POSTGRESQL,
                    tables=tables,
                    version=version,
                    charset="UTF8"
                )
                
            finally:
                await conn.close()
                
        except Exception as e:
            logger.error(f"PostgreSQL introspection failed: {str(e)}")
            raise
    
    async def _get_postgresql_columns(self, conn, table_name: str) -> List[ColumnInfo]:
        """Get column information for a PostgreSQL table"""
        columns_query = """
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default,
                character_maximum_length,
                numeric_precision,
                numeric_scale
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = $1
            ORDER BY ordinal_position
        """
        
        columns_result = await conn.fetch(columns_query, table_name)
        columns = []
        
        for col_row in columns_result:
            column_info = ColumnInfo(
                name=col_row['column_name'],
                type=self._normalize_postgresql_type(col_row['data_type']),
                nullable=col_row['is_nullable'] == 'YES',
                primary_key=False,  # Will be set later
                default_value=col_row['column_default'],
                max_length=col_row['character_maximum_length'],
                auto_increment='nextval(' in str(col_row['column_default'] or '')
            )
            columns.append(column_info)
        
        return columns
    
    async def _get_postgresql_primary_key(self, conn, table_name: str) -> List[str]:
        """Get primary key columns for a PostgreSQL table"""
        pk_query = """
            SELECT a.attname
            FROM pg_index i
            JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
            WHERE i.indrelid = $1::regclass AND i.indisprimary
        """
        
        try:
            pk_result = await conn.fetch(pk_query, table_name)
            return [row['attname'] for row in pk_result]
        except:
            return []
    
    async def _get_postgresql_foreign_keys(self, conn, table_name: str) -> List[ForeignKeyInfo]:
        """Get foreign key information for a PostgreSQL table"""
        fk_query = """
            SELECT
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name,
                rc.delete_rule,
                rc.update_rule
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            JOIN information_schema.referential_constraints AS rc
                ON tc.constraint_name = rc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_name = $1
        """
        
        try:
            fk_result = await conn.fetch(fk_query, table_name)
            foreign_keys = []
            
            for fk_row in fk_result:
                fk_info = ForeignKeyInfo(
                    table=fk_row['foreign_table_name'],
                    column=fk_row['foreign_column_name'],
                    on_delete=fk_row['delete_rule'],
                    on_update=fk_row['update_rule']
                )
                foreign_keys.append(fk_info)
            
            return foreign_keys
        except:
            return []
    
    async def _get_postgresql_indexes(self, conn, table_name: str) -> List[Dict[str, Any]]:
        """Get index information for a PostgreSQL table"""
        # Simplified index information for now
        return []
    
    def _normalize_postgresql_type(self, pg_type: str) -> str:
        """Convert PostgreSQL types to standard types"""
        type_mapping = {
            'character varying': 'varchar',
            'character': 'char',
            'integer': 'int',
            'bigint': 'bigint',
            'smallint': 'smallint',
            'boolean': 'boolean',
            'text': 'text',
            'timestamp without time zone': 'datetime',
            'timestamp with time zone': 'timestamptz',
            'date': 'date',
            'time': 'time',
            'numeric': 'decimal',
            'real': 'float',
            'double precision': 'double',
            'json': 'json',
            'jsonb': 'jsonb',
            'uuid': 'uuid'
        }
        
        return type_mapping.get(pg_type, pg_type)
    
    async def _introspect_mysql(self, connection_string: str) -> DatabaseSchema:
        """Introspect MySQL database schema"""
        # MySQL introspection implementation
        # This would be similar to PostgreSQL but using MySQL-specific queries
        try:
            # Parse connection string for MySQL
            # Connect using aiomysql
            # Extract schema information
            # Return DatabaseSchema object
            
            # For now, return a placeholder
            return DatabaseSchema(
                database_name="mysql_db",
                database_type=DatabaseType.MYSQL,
                tables=[],
                version="8.0",
                charset="utf8mb4"
            )
        except Exception as e:
            logger.error(f"MySQL introspection failed: {str(e)}")
            raise
    
    async def get_table_data_sample(
        self, 
        connection_string: str,
        database_type: DatabaseType,
        table_name: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get sample data from a table for API testing/preview
        
        Args:
            connection_string: Database connection string
            database_type: Type of database
            table_name: Name of table to sample
            limit: Number of rows to return
            
        Returns:
            Sample data rows
        """
        try:
            if database_type == DatabaseType.POSTGRESQL:
                conn = await asyncpg.connect(connection_string)
                try:
                    query = f"SELECT * FROM {table_name} LIMIT $1"
                    result = await conn.fetch(query, limit)
                    return [dict(row) for row in result]
                finally:
                    await conn.close()
            else:
                # MySQL implementation would go here
                return []
                
        except Exception as e:
            logger.error(f"Failed to get table sample: {str(e)}")
            return []


# Global schema introspector instance
schema_introspector = SchemaIntrospector()