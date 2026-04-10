# config/settings.py
import os
from dotenv import load_dotenv

load_dotenv()


def _get_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"필수 환경변수가 비어 있습니다: {name}")
    return value


DISCORD_TOKEN = _get_required_env("DISCORD_BOT_TOKEN")
GEMINI_API_KEY = _get_required_env("GEMINI_API_KEY")
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemma-3-27b-it")
ANALYSIS_DEFAULT_DAYS = 7
ANALYSIS_MAX_DAYS = 30
