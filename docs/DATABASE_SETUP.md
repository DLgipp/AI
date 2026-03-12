# 🗄️ Database Setup Guide

## Production Database Architecture

The memory layer now uses specialized databases for each memory type:

| Memory Type | Database | Purpose |
|-------------|----------|---------|
| **Episodic** | PostgreSQL | Events, conversations, experiences |
| **Semantic** | Milvus (Vector DB) | Knowledge, concepts with embeddings |
| **Relational** | Neo4j (Graph DB) | Entity relationships, connections |
| **Personality** | PostgreSQL | Traits, values, personality state |

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd c:\AI
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Start Databases with Docker

```bash
docker-compose -f docker-compose.databases.yml up -d
```

This starts:
- **PostgreSQL** on port 5432
- **Milvus** on port 19530
- **Neo4j** on ports 7474 (HTTP) and 7687 (Bolt)

### 3. Verify Databases are Running

```bash
docker-compose -f docker-compose.databases.yml ps
```

All services should show `Up` status.

### 4. Run Migration (Optional)

If you have existing SQLite data to migrate:

```bash
python scripts/migrate_databases.py
```

### 5. Test Connection

```bash
python scripts/test_database_connections.py
```

---

## 📋 Database Configuration

### PostgreSQL

**Connection Details:**
- Host: `localhost`
- Port: `5432`
- User: `postgres`
- Password: `postgres`
- Database: `ai_assistant`

**Connection String:**
```
postgresql://postgres:postgres@localhost:5432/ai_assistant
```

**Access:**
- pgAdmin: `http://localhost:5432` (if installed)
- CLI: `psql -U postgres -d ai_assistant`

### Milvus (Vector DB)

**Connection Details:**
- Host: `localhost`
- Port: `19530` (gRPC)
- Collection: `semantic_memories`
- Index: HNSW
- Metric: COSINE
- Embedding Dimension: 768

**Access:**
- Attu (Milvus GUI): `http://localhost:9091` (if available)

### Neo4j (Graph DB)

**Connection Details:**
- URI: `bolt://localhost:7687`
- User: `neo4j`
- Password: `password`
- Database: `neo4j`

**Access:**
- Neo4j Browser: `http://localhost:7474`
- Login with credentials above

---

## 🔧 Manual Setup (Without Docker)

### PostgreSQL

1. **Install PostgreSQL 15+**
   - Windows: https://www.postgresql.org/download/windows/
   - Or use PostgreSQL from Docker

2. **Create Database**
   ```sql
   CREATE DATABASE ai_assistant;
   ```

3. **Update config.py**
   ```python
   POSTGRES_USER = "your_user"
   POSTGRES_PASSWORD = "your_password"
   POSTGRES_DB = "ai_assistant"
   ```

### Milvus

1. **Install Milvus Standalone**
   
   Follow official guide: https://milvus.io/docs/install_standalone-docker.md

   Or use Docker Compose (recommended):
   ```bash
   docker-compose -f docker-compose.databases.yml up -d milvus-standalone etcd minio
   ```

2. **Verify Installation**
   ```python
   from pymilvus import connections
   connections.connect(host="localhost", port=19530)
   ```

### Neo4j

1. **Install Neo4j**
   - Windows: https://neo4j.com/download-center/#community
   - Or use Docker: `docker-compose -f docker-compose.databases.yml up -d neo4j`

2. **Install APOC Plugin**
   - Required for graph algorithms
   - Already configured in docker-compose.yml

3. **Verify Installation**
   ```python
   from neo4j import GraphDatabase
   driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
   driver.verify_connectivity()
   ```

---

## 📊 Database Schema

### PostgreSQL - Episodic Memory

```sql
CREATE TABLE episodic_memories (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    emotion_valence FLOAT DEFAULT 0.0,
    emotion_arousal FLOAT DEFAULT 0.5,
    importance FLOAT DEFAULT 0.5,
    topic VARCHAR(100) DEFAULT 'general',
    intent VARCHAR(100) DEFAULT 'unknown',
    goal TEXT DEFAULT '',
    user_reaction TEXT,
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_session ON episodic_memories(session_id);
CREATE INDEX idx_timestamp ON episodic_memories(timestamp);
CREATE INDEX idx_importance ON episodic_memories(importance DESC);
CREATE INDEX idx_emotion ON episodic_memories(emotion_valence, emotion_arousal);
```

### PostgreSQL - Personality Memory

```sql
CREATE TABLE personality_state (
    id SERIAL PRIMARY KEY,
    openness FLOAT DEFAULT 0.5,
    conscientiousness FLOAT DEFAULT 0.5,
    extraversion FLOAT DEFAULT 0.5,
    agreeableness FLOAT DEFAULT 0.5,
    neuroticism FLOAT DEFAULT 0.5,
    curiosity FLOAT DEFAULT 0.5,
    creativity FLOAT DEFAULT 0.5,
    empathy FLOAT DEFAULT 0.5,
    humor FLOAT DEFAULT 0.5,
    assertiveness FLOAT DEFAULT 0.5,
    values TEXT,
    mood_valence FLOAT DEFAULT 0.0,
    mood_arousal FLOAT DEFAULT 0.5,
    relationships TEXT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1
);
```

### Milvus - Semantic Memory

```python
# Collection Schema
fields = [
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
    FieldSchema(name="concept", dtype=DataType.VARCHAR, max_length=500),
    FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=10000),
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=768),
    FieldSchema(name="category", dtype=DataType.VARCHAR, max_length=100),
    FieldSchema(name="tags", dtype=DataType.VARCHAR, max_length=1000),
    FieldSchema(name="importance", dtype=DataType.FLOAT),
    FieldSchema(name="confidence", dtype=DataType.FLOAT),
    FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=100),
    FieldSchema(name="created_at", dtype=DataType.VARCHAR, max_length=50)
]

# Index
index_params = {
    "index_type": "HNSW",
    "metric_type": "COSINE",
    "params": {"M": 8, "efConstruction": 200}
}
```

### Neo4j - Relational Memory

```cypher
// Node Label
(:Entity {
    name: STRING,
    entity_type: STRING,
    properties: MAP,
    created_at: STRING
})

// Relationship Type
(:Entity)-[:RELATION {
    relation_type: STRING,
    strength: FLOAT,
    properties: MAP,
    created_at: STRING
}]->(:Entity)
```

---

## 🔍 Testing

### Test PostgreSQL Connection

```python
from modules.memory.episodic_memory import PostgreSQLEpisodicMemoryStore, EpisodicMemory
from datetime import datetime

store = PostgreSQLEpisodicMemoryStore()

# Save test memory
memory = EpisodicMemory(
    id=None,
    session_id="test",
    timestamp=datetime.now().isoformat(),
    event_type="test",
    content="Test memory",
    importance=0.5
)
id = store.save(memory)
print(f"Saved episodic memory with ID: {id}")

# Retrieve
recent = store.get_recent(limit=1)
print(f"Retrieved {len(recent)} memories")
```

### Test Milvus Connection

```python
from modules.memory.semantic_memory import MilvusSemanticMemoryStore, SemanticMemory

store = MilvusSemanticMemoryStore()

# Save test memory
memory = SemanticMemory(
    id=None,
    concept="test",
    content="Test knowledge",
    embedding=[0.1] * 768,  # 768-dim vector
    importance=0.5
)
id = store.save(memory)
print(f"Saved semantic memory with ID: {id}")

# Search
results = store.search_by_vector([0.1] * 768, limit=5)
print(f"Found {len(results)} similar memories")
```

### Test Neo4j Connection

```python
from modules.memory.relational_memory import Neo4jRelationalMemoryStore, Entity, Relation

store = Neo4jRelationalMemoryStore()

# Create test entity
entity = Entity(
    id=None,
    name="TestEntity",
    entity_type="concept",
    properties={"test": True}
)
id = store.create_entity(entity)
print(f"Created entity with ID: {id}")

# Get statistics
stats = store.get_statistics()
print(f"Graph stats: {stats}")
```

### Test Personality Memory

```python
from modules.memory.personality_memory import PostgreSQLPersonalityMemoryStore, PersonalityState

store = PostgreSQLPersonalityMemoryStore()

# Get state
state = store.get_state()
print(f"Dominant trait: {state.get_dominant_trait()}")

# Update trait
store.update_trait("curiosity", 0.8)
print("Updated curiosity to 0.8")
```

---

## 🛠️ Troubleshooting

### PostgreSQL Connection Failed

```bash
# Check if PostgreSQL is running
docker-compose -f docker-compose.databases.yml ps postgres

# View logs
docker-compose -f docker-compose.databases.yml logs postgres

# Restart
docker-compose -f docker-compose.databases.yml restart postgres
```

### Milvus Connection Failed

```bash
# Check all Milvus components
docker-compose -f docker-compose.databases.yml ps

# Milvus requires etcd and minio
docker-compose -f docker-compose.databases.yml up -d milvus-standalone etcd minio

# View logs
docker-compose -f docker-compose.databases.yml logs milvus-standalone
```

### Neo4j Connection Failed

```bash
# Check if Neo4j is running
docker-compose -f docker-compose.databases.yml ps neo4j

# View logs
docker-compose -f docker-compose.databases.yml logs neo4j

# Access Neo4j Browser
# Open http://localhost:7474 in browser
```

### Migration Failed

1. **Check source SQLite files exist**
   ```bash
   dir data\*.db
   ```

2. **Check database connections**
   ```bash
   python scripts/test_database_connections.py
   ```

3. **Run migration step-by-step**
   ```python
   from scripts.migrate_databases import (
       migrate_episodic_memory,
       migrate_semantic_memory,
       migrate_relational_memory,
       migrate_personality_memory
   )
   
   migrate_episodic_memory()    # Step 1
   migrate_semantic_memory()    # Step 2
   migrate_relational_memory()  # Step 3
   migrate_personality_memory() # Step 4
   ```

---

## 📈 Performance Optimization

### PostgreSQL

1. **Connection Pooling** (already configured)
   ```python
   pool_size=10, max_overflow=20
   ```

2. **Indexes** (already created)
   - session_id, timestamp, importance, emotion

3. **Query Optimization**
   - Use `get_recent()` with session_id filter
   - Use appropriate limits

### Milvus

1. **Index Parameters**
   ```python
   index_params = {
       "index_type": "HNSW",
       "metric_type": "COSINE",
       "params": {"M": 8, "efConstruction": 200}
   }
   ```

2. **Search Parameters**
   ```python
   search_params = {
       "metric_type": "COSINE",
       "params": {"ef": 64}
   }
   ```

3. **Embedding Dimension**
   - Match your embedding model (768 for sentence-transformers)

### Neo4j

1. **APOC Procedures** (installed)
   - Use `apoc.path.subgraphNodes()` for efficient traversal

2. **Indexes**
   ```cypher
   CREATE INDEX entity_name FOR (e:Entity) ON (e.name)
   ```

3. **Query Optimization**
   - Use `shortestPath()` for path finding
   - Limit traversal depth

---

## 🔐 Security

### Production Deployment

1. **Change Default Passwords**
   ```yaml
   # docker-compose.databases.yml
   environment:
     POSTGRES_PASSWORD: "strong_password"
     NEO4J_AUTH: neo4j/strong_password
     MINIO_ROOT_PASSWORD: strong_password
   ```

2. **Network Isolation**
   ```yaml
   networks:
     ai_network:
       driver: bridge
   ```

3. **Firewall Rules**
   - Block external access to database ports
   - Allow only application server

---

## 📚 Additional Resources

- **PostgreSQL**: https://www.postgresql.org/docs/
- **Milvus**: https://milvus.io/docs
- **Neo4j**: https://neo4j.com/docs/
- **SQLAlchemy**: https://docs.sqlalchemy.org/
- **pymilvus**: https://milvus.io/docs/install-pymilvus.md

---

## ✅ Checklist

- [ ] Docker installed and running
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Databases started (`docker-compose up -d`)
- [ ] All databases accessible (run test script)
- [ ] Migration completed (if applicable)
- [ ] Application configured (config.py)
- [ ] Memory Layer initialized with production DBs

---

**Status**: Ready for production use! 🎉
