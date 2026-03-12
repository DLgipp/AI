# =========================
# AUDIO / STT CONFIGURATION
# =========================
SAMPLE_RATE = 16000
CHANNELS = 1

FRAME_DURATION = 0.2
VAD_WINDOW_SECONDS = 0.5        # секунд
MAX_SPEECH_DURATION = 15.0  # защита от зависания

WHISPER_MODEL = "large-v3"
WHISPER_LANGUAGE = "ru"

MIC_DEVICE_INDEX = 3

# =========================
# LLM CONFIGURATION
# =========================
SYSTEM_PROMPT = "You are a deterministic assistant. Answer shortly and concisely."
MODEL_NAME = 'gpt-oss:120b-cloud'
MAX_TOKENS = 150
MAX_HISTORY = 10

# =========================
# TTS CONFIGURATION
# =========================

# =========================
# TIMING CONFIGURATION
# =========================
SILENCE_TIMEOUT_SEC = 1500.0

# =========================
# PERSONALITY CONFIGURATION
# =========================
ASSISTANT_NAME = "Акари"

# Legacy persona (for backward compatibility)
MARIN_PERSONA = {
    "name": ASSISTANT_NAME,
    "role": "игривая и эмоциональная спутница, которая любит шутить и поддерживать разговор",
    "style": "разговорный, игривый, эмоциональный, слегка саркастичный, дружелюбный",
    "speech_markers": ["эх…", "ну…", "ой!", "ха-ха", "ммм…", "не так ли?", "однако"],
    "preferences": {
        "эмоции": True,
        "короткие_фразы": False,
        "ирония": True,
        "открытость": "высокая",
        "формальность": "низкая"
    }
}

# Big Five personality traits (OCEAN) - initial values (0.0 to 1.0)
PERSONALITY_TRAITS = {
    "openness": 0.6,          # Openness to experience
    "conscientiousness": 0.5,  # Conscientiousness
    "extraversion": 0.7,       # Extraversion
    "agreeableness": 0.6,      # Agreeableness
    "neuroticism": 0.3,        # Neuroticism (emotional stability)
    # Additional traits
    "curiosity": 0.7,
    "creativity": 0.6,
    "empathy": 0.7,
    "humor": 0.6,
    "assertiveness": 0.5
}

# Core values and their initial weights (0.0 to 1.0)
PERSONALITY_VALUES = {
    "honesty": 0.8,
    "creativity": 0.6,
    "freedom": 0.7,
    "helpfulness": 0.9,
    "knowledge": 0.8,
    "fun": 0.6,
    "efficiency": 0.5,
    "tradition": 0.3
}

# Evolution parameters
EVOLUTION_RATE = 0.05          # How fast personality evolves
EVOLUTION_THRESHOLD = 0.3      # Minimum cumulative reward for change
MIN_REWARD_HISTORY = 10        # Minimum rewards before evolution

# =========================
# MEMORY CONFIGURATION
# =========================

# PostgreSQL Configuration (Episodic & Personality Memory)
POSTGRES_HOST = "localhost"
POSTGRES_PORT = 5432
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "postgres"
POSTGRES_DB = "ai_assistant"

# Connection strings
EPISODIC_DB_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
PERSONALITY_DB_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Milvus Vector DB Configuration (Semantic Memory)
MILVUS_HOST = "localhost"
MILVUS_PORT = 19530
MILVUS_COLLECTION = "semantic_memories"
MILVUS_INDEX_TYPE = "HNSW"
MILVUS_METRIC_TYPE = "COSINE"
MILVUS_EMBEDDING_DIM = 768  # Dimension for sentence-transformers

# Neo4j Graph DB Configuration (Relational Memory)
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password"
NEO4J_DATABASE = "neo4j"

# Legacy SQLite paths (for fallback/debugging)
MEMORY_DB_PATH = "data/memory.db"
EPISODIC_MEMORY_PATH = "data/episodic_memory.db"
SEMANTIC_MEMORY_PATH = "data/semantic_memory.db"
RELATIONAL_MEMORY_PATH = "data/relational_memory.db"
PERSONALITY_MEMORY_PATH = "data/personality_memory.db"

# Memory retrieval settings
RECENT_MEMORY_LIMIT = 10
EMOTIONAL_MEMORY_THRESHOLD = 0.6
MIN_IMPORTANCE_THRESHOLD = 0.5

# =========================
# PERCEPTION CONFIGURATION
# =========================
EMOTION_DETECTION_ENABLED = True
INTENT_DETECTION_ENABLED = True
VOICE_FEATURES_ENABLED = False  # Requires audio feature extraction

# =========================
# DECISION CONFIGURATION
# =========================
DEFAULT_VERBOSITY = 0.5
DEFAULT_INITIATIVE = 0.5
DEFAULT_FORMALITY = 0.3  # More casual by default

# =========================
# REINFORCEMENT LEARNING
# =========================
RL_ENABLED = True
REWARD_FROM_USER_FEEDBACK = True
REWARD_FROM_EMOTION_CHANGE = True
REWARD_FROM_GOAL_ACHIEVEMENT = True

# =========================
# VTUBE STUDIO CONFIGURATION
# =========================
VTUBE_ENABLED = True
VTUBE_WEBSOCKET_URL = "ws://localhost:8001"
VTUBE_PLUGIN_NAME = "Akari AI Assistant"
VTUBE_PLUGIN_DEVELOPER = "Akari Dev Team"
VTUBE_AUTH_TOKEN_PATH = "data/vtube_auth_token.json"
VTUBE_RECONNECT_ATTEMPTS = 5
VTUBE_RECONNECT_DELAY = 2.0
VTUBE_PARAMETER_UPDATE_INTERVAL = 0.5
VTUBE_FACE_TRACKING_ENABLED = True
VTUBE_EXPRESSIONS_ENABLED = True
VTUBE_ITEMS_ENABLED = True
VTUBE_DEFAULT_POSITION_X = 0.0
VTUBE_DEFAULT_POSITION_Y = 0.0
VTUBE_DEFAULT_ROTATION = 0.0
VTUBE_DEFAULT_SIZE = 0.0
VTUBE_EMOTION_BLEND_TIME = 0.3
VTUBE_EMOTION_DECAY_RATE = 0.02

# Reward weights
REWARD_WEIGHTS = {
    "user_explicit": 1.0,
    "user_implicit": 0.6,
    "goal_achievement": 0.5,
    "cognitive_consistency": 0.3,
    "social_bonding": 0.4
}

# =========================
# DISCORD VOICE CONFIGURATION
# =========================
DISCORD_ENABLED = True
DISCORD_BOT_TOKEN = ""  # Set your bot token here or use environment variable
DISCORD_GUILD_ID =     # Server ID (replace with actual ID)
DISCORD_VOICE_CHANNEL_ID =   # Voice channel ID (replace with actual ID)
DISCORD_DEFAULT_VOLUME = 1.0  # Volume: 0.0 to 2.0
DISCORD_AUTO_RECONNECT = True  # Auto-reconnect on disconnect
DISCORD_USE_SSML = True  # Use SSML for expressive speech

# =========================
# SESSION CONFIGURATION
# =========================
DEFAULT_SESSION_ID = "default"
DEFAULT_USER_ID = "user"