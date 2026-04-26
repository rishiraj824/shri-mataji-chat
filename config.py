from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
RAW_YOUTUBE_DIR = DATA_DIR / "raw" / "youtube"
RAW_PDF_DIR = DATA_DIR / "raw" / "pdfs"
PROCESSED_DIR = DATA_DIR / "processed"
CHROMA_DIR = BASE_DIR / "chroma_db"

YOUTUBE_CHANNELS = [
    "https://www.youtube.com/@ShriMatajiExcerpts",
    "https://www.youtube.com/@SahajaYoga_Talks_Music",
]

# Keywords to filter OUT music videos (applied to title)
MUSIC_FILTER_KEYWORDS = [
    "music", "bhajan", "song", "concert", "instrumental",
    "mantra music", "meditation music", "raag", "raga",
]

CHUNK_SIZE = 800       # tokens per chunk
CHUNK_OVERLAP = 100    # overlap between chunks
CHAT_MODEL = "claude-sonnet-4-6"
COLLECTION_NAME = "shri_mataji"
