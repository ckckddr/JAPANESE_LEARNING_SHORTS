"""
프로젝트 전역 설정
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── 기본 경로 ──────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
CACHE_DIR = DATA_DIR / "cache"
HISTORY_DIR = DATA_DIR / "history"
SCRIPTS_DIR = DATA_DIR / "scripts"
AUDIO_DIR = DATA_DIR / "audio"
VIDEO_DIR = DATA_DIR / "video"
LOG_DIR = DATA_DIR / "logs"

# ── PDF 경로 ───────────────────────────────────────────────
PDF_N1 = BASE_DIR / "grammar n1.pdf"
PDF_N2 = BASE_DIR / "grammar n2.pdf"
PDF_KANJI = BASE_DIR / "word2136.pdf"

# ── 캐시 파일 ──────────────────────────────────────────────
CACHE_N1 = CACHE_DIR / "knowledge_n1.json"
CACHE_N2 = CACHE_DIR / "knowledge_n2.json"
CACHE_KANJI = CACHE_DIR / "kanji.json"
HISTORY_FILE = HISTORY_DIR / "situation_history.json"

# ── API 키 ─────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GOOGLE_TTS_API_KEY = os.getenv("GOOGLE_TTS_API_KEY", "")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")

# ── Gemini 모델 ────────────────────────────────────────────
GEMINI_MODEL = "gemini-2.5-flash"

# ── TTS 설정 ───────────────────────────────────────────────
TTS_VOICE_MALE = "ja-JP-Neural2-C"    # 남성 일본어
TTS_VOICE_FEMALE = "ja-JP-Neural2-B"  # 여성 일본어
TTS_VOICE_NARRATOR = "ja-JP-Neural2-D" # 나레이터(남)

# ── 영상 설정 ──────────────────────────────────────────────
THUMBNAIL_SIZE = (1080, 1920)

# 디렉토리 자동 생성
for d in [CACHE_DIR, HISTORY_DIR, SCRIPTS_DIR, AUDIO_DIR, VIDEO_DIR, LOG_DIR]:
    d.mkdir(parents=True, exist_ok=True)
