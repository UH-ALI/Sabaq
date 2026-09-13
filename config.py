USE_MOCK_CORE: bool = False   # Flipped to False for Phase 9 real engine integration
INDEX_DIR: str = "data/bio9"
LLM_MODEL: str = "gemini-2.5-flash"          # Primary model
FALLBACK_LLM_MODEL: str = "gemini-2.5-flash-lite"  # Fallback on 429 quota errors
EMBEDDING_MODEL: str = "intfloat/multilingual-e5-base"
DEFAULT_TOP_K: int = 6
