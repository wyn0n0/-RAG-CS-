from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TACTICS_DIR = PROJECT_ROOT / "data" / "tactics"
CHROMA_DIR = PROJECT_ROOT / "data" / "chroma"
UTILITY_LINEUPS_DIR = PROJECT_ROOT / "data" / "utility_lineups"

COLLECTION_NAME = "cs2_tactics"
EMBEDDING_MODEL = "shibing624/text2vec-base-chinese"
RERANK_MODEL = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"

LLM_API_KEY = os.getenv("DEEPSEEK_API_KEY")
LLM_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
LLM_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
