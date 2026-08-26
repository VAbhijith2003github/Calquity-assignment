import os
from pathlib import Path
from dotenv import load_dotenv

# Walk up directories to find the .env file dynamically
env_path = None
for parent in Path(__file__).resolve().parents:
    candidate = parent / ".env"
    if candidate.exists():
        env_path = candidate
        break

if env_path:
    load_dotenv(dotenv_path=env_path)

# Retrieval service configurations
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

COLLECTION_NAME = "parcelpilot_documents"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
