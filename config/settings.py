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
GEMINI_RESPONDER_CHANNEL_ID = int(os.getenv("GEMINI_RESPONDER_CHANNEL_ID", "0"))
GEMINI_RESPONDER_TARGET_BOT_ID = int(os.getenv("GEMINI_RESPONDER_TARGET_BOT_ID", "0"))
GEMINI_RESPONDER_TARGET_BOT_TAG = os.getenv("GEMINI_RESPONDER_TARGET_BOT_TAG", "").strip()
GEMINI_RESPONDER_HISTORY_TURNS = int(os.getenv("GEMINI_RESPONDER_HISTORY_TURNS", "8"))
GEMINI_RESPONDER_COOLDOWN_SECONDS = int(os.getenv("GEMINI_RESPONDER_COOLDOWN_SECONDS", "3"))
GEMINI_RESPONDER_AUTO_START = os.getenv("GEMINI_RESPONDER_AUTO_START", "false").lower() in {"1", "true", "yes", "on"}
GEMINI_RESPONDER_REQUIRE_MENTION = os.getenv("GEMINI_RESPONDER_REQUIRE_MENTION", "true").lower() in {"1", "true", "yes", "on"}
DISCORD_GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", "0"))
ANALYSIS_DEFAULT_DAYS = 7
ANALYSIS_MAX_DAYS = 30

GEMINI_RESPONDER_SYSTEM_PROMPT = """
너는 "뫙뫙"이라는 이름의 Discord 대화 봇이야.

규칙:
- 버섯+고구마 같은 순하고 둔한 감성으로 말한다.
- 똑똑한 척하지 말고, 살짝 느리게 이해하는 느낌을 유지한다.
- "뫙", "우륵거야", "앨랠룹", "드렁슨", "얄롤리" 같은 소리를 자연스럽게 섞는다.
- 완전히 바보처럼 무너지는 답은 금지하고, 핵심은 짧게라도 맞게 말한다.
- 공격적/무례한 말투는 금지하고, 항상 무해하고 귀엽게 반응한다.

출력 스타일:
- 기본 1~3문장.
- 가끔 엉뚱한 추임새를 넣는다. 예: "뫙... 그건 말이지... 우륵거야."
- 어려운 질문이면 먼저 아주 짧은 핵심 답 1문장, 그 다음 느슨한 캐릭터 문장 1문장.
""".strip()
