"""
Database Migration Script

Migrates from SQLite to production databases:
- PostgreSQL for Episodic and Personality Memory
- Milvus for Semantic Memory (Vector DB)
- Neo4j for Relational Memory (Graph DB)
"""

import os
import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    EPISODIC_DB_URL,
    PERSONALITY_DB_URL,
    MILVUS_HOST,
    MILVUS_PORT,
    MILVUS_COLLECTION,
    NEO4J_URI,
    NEO4J_USER,
    NEO4J_PASSWORD,
    EPISODIC_MEMORY_PATH,
    SEMANTIC_MEMORY_PATH,
    RELATIONAL_MEMORY_PATH,
    PERSONALITY_MEMORY_PATH
)


def migrate_episodic_memory():
    """Migrate episodic memory from SQLite to PostgreSQL."""
    print("\n" + "="*60)
    print("Migrating Episodic Memory: SQLite → PostgreSQL")
    print("="*60)
    
    if not os.path.exists(EPISODIC_MEMORY_PATH):
        print(f"⚠️  SQLite database not found: {EPISODIC_MEMORY_PATH}")
        print("Skipping episodic memory migration.")
        return
    
    # Connect to SQLite
    sqlite_conn = sqlite3.connect(EPISODIC_MEMORY_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    cursor = sqlite_conn.cursor()
    
    # Get all memories
    cursor.execute("""
        SELECT id, session_id, timestamp, event_type, content,
               emotion_valence, emotion_arousal, importance,
               topic, intent, goal, user_reaction, metadata
        FROM episodic_memories
        ORDER BY timestamp
    """)
    
    rows = cursor.fetchall()
    
    if not rows:
        print("ℹ️  No episodic memories to migrate.")
        sqlite_conn.close()
        return
    
    # Connect to PostgreSQL
    from modules.memory.episodic_memory import PostgreSQLEpisodicMemoryStore, EpisodicMemory
    
    print(f"📦 Connecting to PostgreSQL...")
    store = PostgreSQLEpisodicMemoryStore(auto_init=True)
    
    migrated_count = 0
    for row in rows:
        memory = EpisodicMemory(
            id=None,  # Let PostgreSQL auto-generate ID
            session_id=row["session_id"],
            timestamp=row["timestamp"],
            event_type=row["event_type"],
            content=row["content"],
            emotion_valence=row["emotion_valence"] or 0.0,
            emotion_arousal=row["emotion_arousal"] or 0.5,
            importance=row["importance"] or 0.5,
            topic=row["topic"] or "general",
            intent=row["intent"] or "unknown",
            goal=row["goal"] or "",
            user_reaction=row["user_reaction"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {}
        )
        
        try:
            store.save(memory)
            migrated_count += 1
        except Exception as e:
            print(f"⚠️  Error migrating memory {row['id']}: {e}")
    
    sqlite_conn.close()
    store.close()
    
    print(f"✅ Migrated {migrated_count}/{len(rows)} episodic memories to PostgreSQL.")


def migrate_semantic_memory():
    """Migrate semantic memory from SQLite to Milvus."""
    print("\n" + "="*60)
    print("Migrating Semantic Memory: SQLite → Milvus")
    print("="*60)
    
    if not os.path.exists(SEMANTIC_MEMORY_PATH):
        print(f"⚠️  SQLite database not found: {SEMANTIC_MEMORY_PATH}")
        print("Skipping semantic memory migration.")
        return
    
    # Connect to SQLite
    sqlite_conn = sqlite3.connect(SEMANTIC_MEMORY_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    cursor = sqlite_conn.cursor()
    
    # Get all memories
    cursor.execute("""
        SELECT id, concept, content, embedding, category, tags,
               importance, confidence, source, created_at
        FROM semantic_memories
        ORDER BY created_at
    """)
    
    rows = cursor.fetchall()
    
    if not rows:
        print("ℹ️  No semantic memories to migrate.")
        sqlite_conn.close()
        return
    
    # Connect to Milvus
    from modules.memory.semantic_memory import MilvusSemanticMemoryStore, SemanticMemory
    
    print(f"📦 Connecting to Milvus ({MILVUS_HOST}:{MILVUS_PORT})...")
    
    try:
        store = MilvusSemanticMemoryStore(auto_connect=True)
    except ConnectionError as e:
        print(f"❌ Failed to connect to Milvus: {e}")
        print("Make sure Milvus is running: docker-compose up -d milvus")
        sqlite_conn.close()
        return
    
    migrated_count = 0
    for row in rows:
        embedding = json.loads(row["embedding"]) if row["embedding"] else []
        
        # Skip if embedding dimension doesn't match
        if len(embedding) == 0:
            print(f"⚠️  Skipping memory {row['id']}: empty embedding")
            continue
        
        memory = SemanticMemory(
            id=None,  # Let Milvus auto-generate ID
            concept=row["concept"],
            content=row["content"],
            embedding=embedding,
            category=row["category"] or "general",
            tags=json.loads(row["tags"]) if row["tags"] else [],
            importance=row["importance"] or 0.5,
            confidence=row["confidence"] or 1.0,
            source=row["source"] or "conversation",
            created_at=row["created_at"]
        )
        
        try:
            store.save(memory)
            migrated_count += 1
        except Exception as e:
            print(f"⚠️  Error migrating memory {row['id']}: {e}")
    
    sqlite_conn.close()
    store.close()
    
    print(f"✅ Migrated {migrated_count}/{len(rows)} semantic memories to Milvus.")


def migrate_relational_memory():
    """Migrate relational memory from SQLite to Neo4j."""
    print("\n" + "="*60)
    print("Migrating Relational Memory: SQLite → Neo4j")
    print("="*60)
    
    if not os.path.exists(RELATIONAL_MEMORY_PATH):
        print(f"⚠️  SQLite database not found: {RELATIONAL_MEMORY_PATH}")
        print("Skipping relational memory migration.")
        return
    
    # Connect to SQLite
    sqlite_conn = sqlite3.connect(RELATIONAL_MEMORY_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    cursor = sqlite_conn.cursor()
    
    # Get all entities
    cursor.execute("""
        SELECT id, name, entity_type, properties, created_at
        FROM entities
        ORDER BY name
    """)
    
    entities = cursor.fetchall()
    
    # Get all relations
    cursor.execute("""
        SELECT id, source_id, target_id, relation_type, strength,
               properties, created_at
        FROM relations
        ORDER BY id
    """)
    
    relations = cursor.fetchall()
    
    if not entities and not relations:
        print("ℹ️  No relational memories to migrate.")
        sqlite_conn.close()
        return
    
    # Connect to Neo4j
    from modules.memory.relational_memory import Neo4jRelationalMemoryStore, Entity, Relation
    
    print(f"📦 Connecting to Neo4j ({NEO4J_URI})...")
    
    try:
        store = Neo4jRelationalMemoryStore(auto_connect=True)
    except ConnectionError as e:
        print(f"❌ Failed to connect to Neo4j: {e}")
        print("Make sure Neo4j is running: docker-compose up -d neo4j")
        sqlite_conn.close()
        return
    
    # Migrate entities
    migrated_entities = {}
    for row in entities:
        entity = Entity(
            id=None,  # Let Neo4j auto-generate ID
            name=row["name"],
            entity_type=row["entity_type"],
            properties=json.loads(row["properties"]) if row["properties"] else {},
            created_at=row["created_at"]
        )
        
        try:
            new_id = store.create_entity(entity)
            migrated_entities[row["id"]] = new_id
        except Exception as e:
            print(f"⚠️  Error migrating entity {row['id']}: {e}")
    
    # Migrate relations
    migrated_count = 0
    for row in relations:
        source_id = migrated_entities.get(row["source_id"])
        target_id = migrated_entities.get(row["target_id"])
        
        if not source_id or not target_id:
            print(f"⚠️  Skipping relation {row['id']}: missing entity")
            continue
        
        relation = Relation(
            id=None,
            source_id=source_id,
            target_id=target_id,
            relation_type=row["relation_type"],
            strength=row["strength"] or 1.0,
            properties=json.loads(row["properties"]) if row["properties"] else {},
            created_at=row["created_at"]
        )
        
        try:
            store.create_relation(relation)
            migrated_count += 1
        except Exception as e:
            print(f"⚠️  Error migrating relation {row['id']}: {e}")
    
    sqlite_conn.close()
    store.close()
    
    print(f"✅ Migrated {len(migrated_entities)} entities and {migrated_count} relations to Neo4j.")


def migrate_personality_memory():
    """Migrate personality memory from SQLite to PostgreSQL."""
    print("\n" + "="*60)
    print("Migrating Personality Memory: SQLite → PostgreSQL")
    print("="*60)
    
    if not os.path.exists(PERSONALITY_MEMORY_PATH):
        print(f"⚠️  SQLite database not found: {PERSONALITY_MEMORY_PATH}")
        print("Skipping personality memory migration.")
        return
    
    # Connect to SQLite
    sqlite_conn = sqlite3.connect(PERSONALITY_MEMORY_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    cursor = sqlite_conn.cursor()
    
    # Get personality state
    cursor.execute("""
        SELECT id, openness, conscientiousness, extraversion, agreeableness,
               neuroticism, curiosity, creativity, empathy, humor, assertiveness,
               "values", mood_valence, mood_arousal, relationships,
               last_updated, version
        FROM personality_state
        WHERE id = 1
    """)
    
    row = cursor.fetchone()
    
    if not row:
        print("ℹ️  No personality state to migrate.")
        sqlite_conn.close()
        return
    
    # Connect to PostgreSQL
    from modules.memory.personality_memory import PostgreSQLPersonalityMemoryStore, PersonalityState
    
    print(f"📦 Connecting to PostgreSQL...")
    store = PostgreSQLPersonalityMemoryStore(auto_init=True)
    
    # Create state
    state = PersonalityState(
        openness=row["openness"] or 0.5,
        conscientiousness=row["conscientiousness"] or 0.5,
        extraversion=row["extraversion"] or 0.5,
        agreeableness=row["agreeableness"] or 0.5,
        neuroticism=row["neuroticism"] or 0.5,
        curiosity=row["curiosity"] or 0.5,
        creativity=row["creativity"] or 0.5,
        empathy=row["empathy"] or 0.5,
        humor=row["humor"] or 0.5,
        assertiveness=row["assertiveness"] or 0.5,
        values=json.loads(row["values"]) if row["values"] else PersonalityState().values,
        mood_valence=row["mood_valence"] or 0.0,
        mood_arousal=row["mood_arousal"] or 0.5,
        relationships=json.loads(row["relationships"]) if row["relationships"] else {},
        last_updated=row["last_updated"],
        version=row["version"] or 1
    )
    
    try:
        store.save_state(state)
        print(f"✅ Migrated personality state to PostgreSQL.")
    except Exception as e:
        print(f"❌ Error migrating personality state: {e}")
    
    sqlite_conn.close()
    store.close()


def run_all_migrations():
    """Run all database migrations."""
    print("\n" + "🚀 "*20)
    print(" Starting Database Migration")
    print(" SQLite → PostgreSQL + Milvus + Neo4j")
    print("🚀 "*20 + "\n")
    
    start_time = datetime.now()
    
    try:
        # Run migrations
        migrate_episodic_memory()
        migrate_semantic_memory()
        migrate_relational_memory()
        migrate_personality_memory()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print("\n" + "="*60)
        print("✅ Migration Complete!")
        print(f"⏱️  Duration: {duration:.2f} seconds")
        print("="*60 + "\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Migration interrupted by user.")
    except Exception as e:
        print(f"\n\n❌ Migration failed: {e}")
        raise


if __name__ == "__main__":
    run_all_migrations()
