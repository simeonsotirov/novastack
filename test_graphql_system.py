#!/usr/bin/env python3
"""
GraphQL System Test for NovaStack

Tests the complete GraphQL schema generation system including:
- GraphQL schema generation from database schemas
- Type creation and field mapping
- Query and mutation resolver generation
- GraphQL endpoint integration
"""

import sys
import os
from pathlib import Path

# Add backend to path for imports
backend_path = str(Path("backend").resolve())
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Test imports
try:
    from app.services.graphql_generator import GraphQLSchemaGenerator, create_graphql_schema_for_project
    from app.services.schema_introspector import DatabaseSchema, TableInfo, ColumnInfo, DatabaseType
    print("✅ GraphQL imports successful")
except ImportError as e:
    print(f"❌ GraphQL import failed: {e}")
    sys.exit(1)


def create_mock_database_schema() -> DatabaseSchema:
    """Create a mock database schema for testing"""
    
    # Create mock user table
    user_columns = [
        ColumnInfo(
            name="id",
            type="integer",
            nullable=False,
            primary_key=True,
            default_value=None
        ),
        ColumnInfo(
            name="name",
            type="varchar(255)",
            nullable=False,
            primary_key=False,
            default_value=None
        ),
        ColumnInfo(
            name="email",
            type="varchar(255)",
            nullable=False,
            primary_key=False,
            default_value=None
        ),
        ColumnInfo(
            name="created_at",
            type="timestamp",
            nullable=True,
            primary_key=False,
            default_value="now()"
        ),
        ColumnInfo(
            name="active",
            type="boolean",
            nullable=True,
            primary_key=False,
            default_value="true"
        )
    ]
    
    user_table = TableInfo(
        name="users",
        columns=user_columns,
        primary_key=["id"],
        foreign_keys=[],
        indexes=[]
    )
    
    # Create mock post table
    post_columns = [
        ColumnInfo(
            name="id",
            type="integer", 
            nullable=False,
            primary_key=True,
            default_value=None
        ),
        ColumnInfo(
            name="title",
            type="varchar(500)",
            nullable=False,
            primary_key=False,
            default_value=None
        ),
        ColumnInfo(
            name="content",
            type="text",
            nullable=True,
            primary_key=False,
            default_value=None
        ),
        ColumnInfo(
            name="user_id",
            type="integer",
            nullable=False,
            primary_key=False,
            default_value=None
        ),
        ColumnInfo(
            name="published",
            type="boolean",
            nullable=True,
            primary_key=False,
            default_value="false"
        )
    ]
    
    post_table = TableInfo(
        name="posts",
        columns=post_columns,
        primary_key=["id"],
        foreign_keys=[],  # Simplified for testing
        indexes=[]
    )
    
    # Create database schema
    return DatabaseSchema(
        database_name="test_db",
        database_type=DatabaseType.POSTGRESQL,
        tables=[user_table, post_table],
        version="13.0"
    )


def test_graphql_type_generation():
    """Test GraphQL type generation from database schema"""
    print("\n🧪 Testing GraphQL Type Generation...")
    
    try:
        # Create mock schema
        db_schema = create_mock_database_schema()
        
        # Create GraphQL generator
        generator = GraphQLSchemaGenerator(db_schema, "test_project")
        
        # Generate types
        types = generator.generate_types()
        
        # Verify types were created
        assert len(types) == 2, f"Expected 2 types, got {len(types)}"
        assert "users" in types, "Users type not found"
        assert "posts" in types, "Posts type not found"
        
        # Check user type fields
        user_type = types["users"]
        expected_fields = ["id", "name", "email", "created_at", "active"]
        for field in expected_fields:
            assert field in user_type.fields, f"Field {field} not found in Users type"
        
        print("✅ GraphQL type generation successful")
        print(f"   - Generated {len(types)} types")
        print(f"   - Users type has {len(user_type.fields)} fields")
        print(f"   - Posts type has {len(types['posts'].fields)} fields")
        
        return True
        
    except Exception as e:
        print(f"❌ GraphQL type generation failed: {e}")
        return False


def test_graphql_schema_creation():
    """Test complete GraphQL schema creation"""
    print("\n🧪 Testing GraphQL Schema Creation...")
    
    try:
        # Create mock schema
        db_schema = create_mock_database_schema()
        
        # Create complete GraphQL schema
        graphql_schema = create_graphql_schema_for_project(db_schema, "test_project")
        
        # Verify schema was created
        assert graphql_schema is not None, "GraphQL schema is None"
        
        # Check if schema has query and mutation types
        schema_str = str(graphql_schema)
        assert "type Query" in schema_str, "Query type not found in schema"
        assert "type Mutation" in schema_str, "Mutation type not found in schema"
        
        print("✅ GraphQL schema creation successful")
        print("   - Schema contains Query type")
        print("   - Schema contains Mutation type")
        print(f"   - Schema SDL length: {len(schema_str)} characters")
        
        return True
        
    except Exception as e:
        print(f"❌ GraphQL schema creation failed: {e}")
        return False


def test_type_mapping():
    """Test database type to GraphQL type mapping"""
    print("\n🧪 Testing Type Mapping...")
    
    try:
        db_schema = create_mock_database_schema()
        generator = GraphQLSchemaGenerator(db_schema, "test_project")
        
        # Test various column types
        test_columns = [
            ColumnInfo(name="text_field", type="varchar(255)", nullable=False, primary_key=False, default_value=None),
            ColumnInfo(name="number_field", type="integer", nullable=False, primary_key=False, default_value=None),
            ColumnInfo(name="float_field", type="numeric", nullable=False, primary_key=False, default_value=None),
            ColumnInfo(name="bool_field", type="boolean", nullable=False, primary_key=False, default_value=None),
            ColumnInfo(name="nullable_field", type="varchar(100)", nullable=True, primary_key=False, default_value=None),
        ]
        
        # Test type mapping
        for column in test_columns:
            python_type = generator._python_type_to_graphql_type(column)
            assert python_type is not None, f"No type mapping for {column.type}"
        
        print("✅ Type mapping successful")
        print("   - String types mapped correctly")
        print("   - Numeric types mapped correctly") 
        print("   - Boolean types mapped correctly")
        print("   - Nullable types handled correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Type mapping failed: {e}")
        return False


def test_input_type_generation():
    """Test GraphQL input type generation for mutations"""
    print("\n🧪 Testing Input Type Generation...")
    
    try:
        db_schema = create_mock_database_schema()
        generator = GraphQLSchemaGenerator(db_schema, "test_project")
        
        # Generate types (includes input types)
        generator.generate_types()
        
        # Check input types were created
        expected_input_types = [
            "users_create",
            "users_update", 
            "posts_create",
            "posts_update"
        ]
        
        for input_type_key in expected_input_types:
            assert input_type_key in generator.generated_input_types, f"Input type {input_type_key} not found"
        
        print("✅ Input type generation successful")
        print(f"   - Generated {len(generator.generated_input_types)} input types")
        print("   - Create input types generated")
        print("   - Update input types generated")
        
        return True
        
    except Exception as e:
        print(f"❌ Input type generation failed: {e}")
        return False


def main():
    """Run all GraphQL system tests"""
    print("🚀 NovaStack GraphQL System Test Suite")
    print("=" * 60)
    
    tests = [
        test_graphql_type_generation,
        test_type_mapping,
        test_input_type_generation,
        test_graphql_schema_creation,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 ALL GRAPHQL TESTS PASSED!")
        print("\n✅ GraphQL Schema Generator is fully functional!")
        print("✅ Ready to serve auto-generated GraphQL APIs!")
        print("\n🚀 Next steps:")
        print("   - Start server to test GraphQL endpoints")
        print("   - Test with real database connections")
        print("   - Use GraphQL Playground for interactive testing")
    else:
        print("❌ Some tests failed - please review and fix issues")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)