"""
GraphQL Schema Generator for NovaStack

This module generates GraphQL schemas dynamically from database table schemas.
It creates GraphQL types, queries, mutations, and subscriptions automatically.
"""

import strawberry
from strawberry.scalars import JSON
from typing import Any, Dict, List, Optional, Type, Union
from datetime import datetime, date
import logging
from dataclasses import dataclass

from app.services.schema_introspector import DatabaseSchema, TableInfo, ColumnInfo

logger = logging.getLogger(__name__)


@dataclass
class GraphQLTypeInfo:
    """Information about a generated GraphQL type"""
    name: str
    strawberry_type: Type
    table_info: TableInfo
    fields: Dict[str, Any]


class GraphQLSchemaGenerator:
    """
    Generates GraphQL schemas from database table schemas
    
    This class takes database schema information and creates:
    - GraphQL types for each table
    - Query resolvers for reading data
    - Mutation resolvers for creating/updating/deleting data
    - Input types for mutations
    """
    
    def __init__(self, database_schema: DatabaseSchema, project_id: str):
        self.database_schema = database_schema
        self.project_id = project_id
        self.generated_types: Dict[str, GraphQLTypeInfo] = {}
        self.generated_input_types: Dict[str, Type] = {}
        
    def _python_type_to_graphql_type(self, column: ColumnInfo) -> Type:
        """Convert database column type to GraphQL/Python type"""
        type_mapping = {
            # String types
            'varchar': str,
            'text': str,
            'char': str,
            'string': str,
            'character': str,
            
            # Integer types
            'integer': int,
            'int': int,
            'bigint': int,
            'smallint': int,
            'serial': int,
            'bigserial': int,
            
            # Float types
            'real': float,
            'double': float,
            'numeric': float,
            'decimal': float,
            'float': float,
            
            # Boolean
            'boolean': bool,
            'bool': bool,
            
            # Date/Time types
            'timestamp': datetime,
            'timestamptz': datetime,
            'datetime': datetime,
            'date': date,
            'time': str,  # Time as string for simplicity
            
            # JSON types
            'json': JSON,
            'jsonb': JSON,
            
            # Binary/Other
            'bytea': str,  # Base64 encoded
            'uuid': str,
            'enum': str,
        }
        
        # Get base type without size/precision info
        base_type = column.type.lower().split('(')[0].strip()
        python_type = type_mapping.get(base_type, str)  # Default to string
        
        # Handle nullable fields
        if column.nullable:
            return Optional[python_type]
        
        return python_type
    
    def _create_graphql_type_for_table(self, table: TableInfo) -> Type:
        """Create a GraphQL type for a database table"""
        
        # Create fields dictionary with proper annotations
        annotations = {}
        defaults = {}
        
        for column in table.columns:
            field_type = self._python_type_to_graphql_type(column)
            annotations[column.name] = field_type
            # Set a default strawberry field
            defaults[column.name] = strawberry.field()
        
        # Create the class dynamically with proper annotations
        class_name = f"{table.name.title()}"
        namespace = {
            '__annotations__': annotations,
            **defaults
        }
        
        DynamicClass = type(class_name, (), namespace)
        
        # Create the GraphQL type using strawberry
        graphql_type = strawberry.type(DynamicClass, name=class_name)
        
        return graphql_type
    
    def _create_input_types_for_table(self, table: TableInfo) -> Dict[str, Type]:
        """Create input types for mutations (Create, Update)"""
        
        # Create annotations and defaults for create input
        create_annotations = {}
        create_defaults = {}
        
        # Create annotations and defaults for update input
        update_annotations = {}
        update_defaults = {}
        
        for column in table.columns:
            field_type = self._python_type_to_graphql_type(column)
            
            # For create input, exclude auto-increment/generated columns
            if not (column.primary_key and 'serial' in column.type.lower()):
                # Make all create fields optional for flexibility
                if hasattr(field_type, '__origin__') and field_type.__origin__ is Union:
                    create_annotations[column.name] = field_type
                else:
                    create_annotations[column.name] = Optional[field_type]
                create_defaults[column.name] = strawberry.field()
            
            # For update input, all fields are optional
            if hasattr(field_type, '__origin__') and field_type.__origin__ is Union:
                update_annotations[column.name] = field_type
            else:
                update_annotations[column.name] = Optional[field_type]
            update_defaults[column.name] = strawberry.field()
        
        # Create input classes dynamically
        create_class_name = f"Create{table.name.title()}Input"
        update_class_name = f"Update{table.name.title()}Input"
        
        CreateInputClass = type(create_class_name, (), {
            '__annotations__': create_annotations,
            **create_defaults
        })
        
        UpdateInputClass = type(update_class_name, (), {
            '__annotations__': update_annotations,
            **update_defaults
        })
        
        # Create Strawberry input types
        create_input_type = strawberry.input(CreateInputClass, name=create_class_name)
        update_input_type = strawberry.input(UpdateInputClass, name=update_class_name)
        
        return {
            'create': create_input_type,
            'update': update_input_type
        }
    
    def generate_types(self) -> Dict[str, GraphQLTypeInfo]:
        """Generate GraphQL types for all tables in the schema"""
        
        logger.info(f"Generating GraphQL types for {len(self.database_schema.tables)} tables")
        
        for table in self.database_schema.tables:
            try:
                # Create main GraphQL type
                graphql_type = self._create_graphql_type_for_table(table)
                
                # Create input types for mutations
                input_types = self._create_input_types_for_table(table)
                
                # Store type information
                type_info = GraphQLTypeInfo(
                    name=table.name.title(),
                    strawberry_type=graphql_type,
                    table_info=table,
                    fields={col.name: self._python_type_to_graphql_type(col) 
                            for col in table.columns}
                )
                
                self.generated_types[table.name] = type_info
                self.generated_input_types[f"{table.name}_create"] = input_types['create']
                self.generated_input_types[f"{table.name}_update"] = input_types['update']
                
                logger.info(f"✅ Generated GraphQL type for table: {table.name}")
                
            except Exception as e:
                logger.error(f"❌ Failed to generate GraphQL type for table {table.name}: {e}")
                continue
        
        logger.info(f"✅ Generated {len(self.generated_types)} GraphQL types")
        return self.generated_types
    
    def create_query_class(self) -> Type:
        """Create the main Query class with resolvers for all tables"""
        
        query_methods = {}
        
        for table_name, type_info in self.generated_types.items():
            # Create list query (e.g., users, posts)
            list_method_name = table_name.lower() + 's'  # Simple pluralization
            query_methods[list_method_name] = self._create_list_resolver(type_info)
            
            # Create single item query (e.g., user, post)  
            single_method_name = table_name.lower()
            query_methods[single_method_name] = self._create_single_resolver(type_info)
        
        # Create Query class dynamically
        Query = type('Query', (), query_methods)
        return strawberry.type(Query)
    
    def create_mutation_class(self) -> Type:
        """Create the main Mutation class with resolvers for all tables"""
        
        mutation_methods = {}
        
        for table_name, type_info in self.generated_types.items():
            table_title = table_name.title()
            
            # Create mutation methods
            mutation_methods[f'create{table_title}'] = self._create_create_resolver(type_info)
            mutation_methods[f'update{table_title}'] = self._create_update_resolver(type_info)
            mutation_methods[f'delete{table_title}'] = self._create_delete_resolver(type_info)
        
        # Create Mutation class dynamically
        Mutation = type('Mutation', (), mutation_methods)
        return strawberry.type(Mutation)
    
    def _create_list_resolver(self, type_info: GraphQLTypeInfo):
        """Create a resolver for listing all records of a type"""
        
        @strawberry.field
        async def resolver(
            self,
            limit: Optional[int] = 50,
            offset: Optional[int] = 0
        ) -> List[type_info.strawberry_type]:
            # This would connect to the actual database
            # For now, return empty list as placeholder
            logger.info(f"GraphQL Query: {type_info.name} list (limit={limit}, offset={offset})")
            return []
        
        return resolver
    
    def _create_single_resolver(self, type_info: GraphQLTypeInfo):
        """Create a resolver for getting a single record by ID"""
        
        # Find the primary key column
        pk_column = next((col for col in type_info.table_info.columns if col.primary_key), None)
        pk_type = int if pk_column and 'int' in pk_column.type.lower() else str
        
        @strawberry.field
        async def resolver(self, id: pk_type) -> Optional[type_info.strawberry_type]:
            # This would connect to the actual database
            logger.info(f"GraphQL Query: {type_info.name} single (id={id})")
            return None
        
        return resolver
    
    def _create_create_resolver(self, type_info: GraphQLTypeInfo):
        """Create a resolver for creating new records"""
        
        input_type = self.generated_input_types[f"{type_info.table_info.name}_create"]
        
        @strawberry.field
        async def resolver(self, input: input_type) -> type_info.strawberry_type:
            # This would connect to the actual database
            logger.info(f"GraphQL Mutation: Create {type_info.name}")
            # Return a mock object for now
            return None
        
        return resolver
    
    def _create_update_resolver(self, type_info: GraphQLTypeInfo):
        """Create a resolver for updating records"""
        
        input_type = self.generated_input_types[f"{type_info.table_info.name}_update"]
        pk_column = next((col for col in type_info.table_info.columns if col.primary_key), None)
        pk_type = int if pk_column and 'int' in pk_column.type.lower() else str
        
        @strawberry.field
        async def resolver(self, id: pk_type, input: input_type) -> type_info.strawberry_type:
            # This would connect to the actual database
            logger.info(f"GraphQL Mutation: Update {type_info.name} (id={id})")
            return None
        
        return resolver
    
    def _create_delete_resolver(self, type_info: GraphQLTypeInfo):
        """Create a resolver for deleting records"""
        
        pk_column = next((col for col in type_info.table_info.columns if col.primary_key), None)
        pk_type = int if pk_column and 'int' in pk_column.type.lower() else str
        
        @strawberry.field
        async def resolver(self, id: pk_type) -> bool:
            # This would connect to the actual database
            logger.info(f"GraphQL Mutation: Delete {type_info.name} (id={id})")
            return True
        
        return resolver
    
    def generate_schema(self) -> strawberry.Schema:
        """Generate the complete GraphQL schema"""
        
        logger.info("🚀 Generating complete GraphQL schema...")
        
        # Generate all types first
        self.generate_types()
        
        # Create Query and Mutation classes
        Query = self.create_query_class()
        Mutation = self.create_mutation_class()
        
        # Create the schema
        schema = strawberry.Schema(
            query=Query,
            mutation=Mutation
        )
        
        logger.info("✅ GraphQL schema generated successfully!")
        return schema
    
    def get_schema_sdl(self) -> str:
        """Get the Schema Definition Language (SDL) representation"""
        schema = self.generate_schema()
        return str(schema)


def create_graphql_schema_for_project(database_schema: DatabaseSchema, project_id: str) -> strawberry.Schema:
    """
    Create a GraphQL schema for a specific project's database
    
    Args:
        database_schema: The database schema information
        project_id: The project identifier
        
    Returns:
        A Strawberry GraphQL schema
    """
    generator = GraphQLSchemaGenerator(database_schema, project_id)
    return generator.generate_schema()


# Example usage:
if __name__ == "__main__":
    # This would be used with real database schema
    # schema = create_graphql_schema_for_project(db_schema, "project_123")
    # print(schema)
    pass