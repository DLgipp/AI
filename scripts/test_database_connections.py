"""
Database Connection Test Script

Tests connections to all production databases:
- PostgreSQL (Episodic & Personality Memory)
- Milvus (Semantic Memory)
- Neo4j (Relational Memory)
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    POSTGRES_HOST,
    POSTGRES_PORT,
    POSTGRES_USER,
    POSTGRES_PASSWORD,
    POSTGRES_DB,
    MILVUS_HOST,
    MILVUS_PORT,
    NEO4J_URI,
    NEO4J_USER,
    NEO4J_PASSWORD
)


def test_postgresql():
    """Test PostgreSQL connection."""
    print("\n" + "="*60)
    print("Testing PostgreSQL Connection")
    print("="*60)
    print(f"Host: {POSTGRES_HOST}:{POSTGRES_PORT}")
    print(f"Database: {POSTGRES_DB}")
    print(f"User: {POSTGRES_USER}")
    
    try:
        from modules.memory.episodic_memory import PostgreSQLEpisodicMemoryStore
        from modules.memory.personality_memory import PostgreSQLPersonalityMemoryStore
        from datetime import datetime
        
        # Test Episodic Memory
        print("\n📊 Testing Episodic Memory store...")
        episodic_store = PostgreSQLEpisodicMemoryStore(auto_init=True)
        
        # Save test memory
        from modules.memory.episodic_memory import EpisodicMemory
        test_memory = EpisodicMemory(
            id=None,
            session_id="test_connection",
            timestamp=datetime.now().isoformat(),
            event_type="test",
            content="Database connection test",
            importance=0.5
        )
        memory_id = episodic_store.save(test_memory)
        print(f"✅ Saved test memory with ID: {memory_id}")
        
        # Retrieve
        recent = episodic_store.get_recent(limit=1)
        print(f"✅ Retrieved {len(recent)} memories")
        
        # Clean up test
        if recent:
            episodic_store.delete(recent[0].id)
            print(f"✅ Cleaned up test memory")
        
        episodic_store.close()
        
        # Test Personality Memory
        print("\n🧠 Testing Personality Memory store...")
        personality_store = PostgreSQLPersonalityMemoryStore(auto_init=True)
        
        # Get state
        state = personality_store.get_state()
        print(f"✅ Retrieved personality state")
        print(f"   Dominant trait: {state.get_dominant_trait()}")
        print(f"   Mood valence: {state.mood_valence:+.2f}")
        
        personality_store.close()
        
        print("\n✅ PostgreSQL: ALL TESTS PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ PostgreSQL: CONNECTION FAILED")
        print(f"   Error: {e}")
        return False


def test_milvus():
    """Test Milvus connection."""
    print("\n" + "="*60)
    print("Testing Milvus Connection")
    print("="*60)
    print(f"Host: {MILVUS_HOST}:{MILVUS_PORT}")
    print(f"Collection: semantic_memories")
    
    try:
        from modules.memory.semantic_memory import MilvusSemanticMemoryStore, SemanticMemory
        
        print("\n📊 Connecting to Milvus...")
        store = MilvusSemanticMemoryStore(auto_connect=True)
        
        # Get statistics
        stats = store.get_statistics()
        print(f"✅ Connected successfully")
        print(f"   Total memories: {stats['total_memories']}")
        print(f"   Average importance: {stats['average_importance']:.2f}")
        
        # Save test memory
        print("\n💾 Testing save operation...")
        test_memory = SemanticMemory(
            id=None,
            concept="test",
            content="Database connection test",
            embedding=[0.1] * 768,  # 768-dim vector
            importance=0.5
        )
        memory_id = store.save(test_memory)
        print(f"✅ Saved test memory with ID: {memory_id}")
        
        # Search
        print("\n🔍 Testing vector search...")
        results = store.search_by_vector([0.1] * 768, limit=5)
        print(f"✅ Search returned {len(results)} results")
        
        # Clean up test
        if memory_id:
            store.delete(memory_id)
            print(f"✅ Cleaned up test memory")
        
        store.close()
        
        print("\n✅ Milvus: ALL TESTS PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Milvus: CONNECTION FAILED")
        print(f"   Error: {e}")
        print(f"\n💡 Make sure Milvus is running:")
        print(f"   docker-compose -f docker-compose.databases.yml up -d milvus-standalone etcd minio")
        return False


def test_neo4j():
    """Test Neo4j connection."""
    print("\n" + "="*60)
    print("Testing Neo4j Connection")
    print("="*60)
    print(f"URI: {NEO4J_URI}")
    print(f"User: {NEO4J_USER}")
    
    try:
        from modules.memory.relational_memory import Neo4jRelationalMemoryStore, Entity, Relation
        
        print("\n📊 Connecting to Neo4j...")
        store = Neo4jRelationalMemoryStore(auto_connect=True)
        
        # Get statistics
        stats = store.get_statistics()
        print(f"✅ Connected successfully")
        print(f"   Total entities: {stats['total_entities']}")
        print(f"   Total relations: {stats['total_relations']}")
        print(f"   Entity types: {stats['num_entity_types']}")
        print(f"   Relation types: {stats['num_relation_types']}")
        
        # Create test entity
        print("\n💾 Testing entity creation...")
        test_entity = Entity(
            id=None,
            name="TestEntity",
            entity_type="concept",
            properties={"test": True, "purpose": "connection_test"}
        )
        entity_id = store.create_entity(test_entity)
        print(f"✅ Created entity with ID: {entity_id}")
        
        # Get entity
        print("\n🔍 Testing entity retrieval...")
        entity = store.get_entity("TestEntity")
        if entity:
            print(f"✅ Retrieved entity: {entity.name}")
        
        # Create another entity and relation
        print("\n🔗 Testing relation creation...")
        test_entity2 = Entity(
            id=None,
            name="TestEntity2",
            entity_type="concept",
            properties={"test": True}
        )
        entity2_id = store.create_entity(test_entity2)
        
        test_relation = Relation(
            id=None,
            source_id=entity_id,
            target_id=entity2_id,
            relation_type="related_to",
            strength=0.9,
            properties={"test": True}
        )
        relation_id = store.create_relation(test_relation)
        print(f"✅ Created relation with ID: {relation_id}")
        
        # Find path
        print("\n🛤️ Testing path finding...")
        path = store.find_path("TestEntity", "TestEntity2")
        if path:
            print(f"✅ Found path with {len(path)} relations")
        
        # Clean up test
        print("\n🧹 Cleaning up test data...")
        store.delete_entity("TestEntity", detach=True)
        store.delete_entity("TestEntity2", detach=True)
        print(f"✅ Cleaned up test entities")
        
        store.close()
        
        print("\n✅ Neo4j: ALL TESTS PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Neo4j: CONNECTION FAILED")
        print(f"   Error: {e}")
        print(f"\n💡 Make sure Neo4j is running:")
        print(f"   docker-compose -f docker-compose.databases.yml up -d neo4j")
        return False


def test_memory_layer():
    """Test unified Memory Layer with production databases."""
    print("\n" + "="*60)
    print("Testing Unified Memory Layer")
    print("="*60)
    
    try:
        from modules.memory import MemoryLayer
        
        print("\n📦 Initializing Memory Layer with production databases...")
        memory = MemoryLayer(use_production_dbs=True)
        
        print(f"✅ Episodic Memory: {type(memory.episodic).__name__}")
        print(f"✅ Semantic Memory: {type(memory.semantic).__name__}")
        print(f"✅ Relational Memory: {type(memory.relational).__name__}")
        print(f"✅ Personality Memory: {type(memory.personality).__name__}")
        
        # Get overall statistics
        print("\n📊 Getting memory statistics...")
        stats = memory.get_statistics()
        
        print(f"\n   Episodic Memory:")
        print(f"      Total memories: {stats['episodic']['total_memories']}")
        print(f"      Avg valence: {stats['episodic']['average_valence']:.2f}")
        
        print(f"\n   Semantic Memory:")
        print(f"      Total memories: {stats['semantic']['total_memories']}")
        print(f"      Avg importance: {stats['semantic']['average_importance']:.2f}")
        
        print(f"\n   Relational Memory:")
        print(f"      Total entities: {stats['relational']['total_entities']}")
        print(f"      Total relations: {stats['relational']['total_relations']}")
        
        print(f"\n   Personality Memory:")
        print(f"      Dominant trait: {stats['personality']['dominant_trait']}")
        print(f"      Mood valence: {stats['personality']['current_mood_valence']:.2f}")
        
        # Close connections
        memory.episodic.close()
        memory.semantic.close()
        memory.relational.close()
        memory.personality.close()
        
        print("\n✅ Memory Layer: ALL TESTS PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Memory Layer: TEST FAILED")
        print(f"   Error: {e}")
        return False


def main():
    """Run all database tests."""
    print("\n" + "🧪 "*20)
    print(" Database Connection Test Suite")
    print("🧪 "*20)
    
    results = {
        "PostgreSQL": test_postgresql(),
        "Milvus": test_milvus(),
        "Neo4j": test_neo4j(),
        "Memory Layer": test_memory_layer()
    }
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for db, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {db}: {status}")
    
    total_passed = sum(results.values())
    total_tests = len(results)
    
    print("\n" + "="*60)
    print(f"Total: {total_passed}/{total_tests} tests passed")
    print("="*60)
    
    if total_passed == total_tests:
        print("\n🎉 All databases are ready for production use!")
        return 0
    else:
        print("\n⚠️  Some databases failed. Check the errors above.")
        print("\n💡 To start all databases:")
        print("   docker-compose -f docker-compose.databases.yml up -d")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
