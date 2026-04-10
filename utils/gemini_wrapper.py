# utils/gemini_wrapper.py
import asyncio
import logging
import google.generativeai as genai
from config.settings import GEMINI_API_KEY, GEMINI_MODEL_NAME

genai.configure(api_key=GEMINI_API_KEY)
logger = logging.getLogger(__name__)


def _get_model() -> genai.GenerativeModel:
    return genai.GenerativeModel(GEMINI_MODEL_NAME)


async def ask_gemini_question(prompt: str) -> str:
    loop = asyncio.get_running_loop()
    try:
        model = _get_model()
        response = await asyncio.wait_for(
            loop.run_in_executor(None, model.generate_content, prompt),
            timeout=30
        )
        return getattr(response, "text", "Gemini 응답이 비어 있어요.")
    except asyncio.TimeoutError:
        logger.warning("Gemini response timeout after 30 seconds")
        return "Gemini 응답 시간이 너무 오래 걸려 타임아웃이 발생했어요."
    except Exception:
        logger.exception("Gemini response failed")
        return "Gemini 응답 중 오류가 발생했어요. 잠시 후 다시 시도해 주세요."
