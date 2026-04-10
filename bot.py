# bot.py
from importlib import import_module
from collections import defaultdict, deque
import asyncio
import logging
import time
from typing import Optional
import discord
from discord import app_commands
from discord.ext import commands

from config.settings import (
    DISCORD_GUILD_ID,
    DISCORD_TOKEN,
    GEMINI_RESPONDER_CHANNEL_ID,
    GEMINI_RESPONDER_SYSTEM_PROMPT,
    GEMINI_RESPONDER_HISTORY_TURNS,
    GEMINI_RESPONDER_COOLDOWN_SECONDS,
    GEMINI_RESPONDER_AUTO_START,
    GEMINI_RESPONDER_REQUIRE_MENTION,
    GEMINI_RESPONDER_TARGET_BOT_ID,
    GEMINI_RESPONDER_TARGET_BOT_TAG,
)
from utils.gemini_wrapper import ask_gemini_question
from utils.text_utils import chunk_text

COG_SPECS = [
    ("cogs.python_dice", "DiceCog"),
    ("cogs.python_time", "TimeCog"),
    ("cogs.google_gemini", "GeminiCog"),
    ("cogs.user_analysis", "UserAnalysisCog"),
]

logger = logging.getLogger(__name__)
conversation_histories: dict[int, deque[str]] = defaultdict(
    lambda: deque(maxlen=max(2, GEMINI_RESPONDER_HISTORY_TURNS * 2))
)
recent_bot_replies: dict[int, deque[str]] = defaultdict(lambda: deque(maxlen=3))
last_reply_at_by_channel: dict[int, float] = defaultdict(float)

active_responder_channel_id = GEMINI_RESPONDER_CHANNEL_ID
responder_enabled = GEMINI_RESPONDER_AUTO_START and GEMINI_RESPONDER_CHANNEL_ID > 0
active_target_bot_id = GEMINI_RESPONDER_TARGET_BOT_ID if responder_enabled else 0
active_target_bot_tag = GEMINI_RESPONDER_TARGET_BOT_TAG if responder_enabled else ""
active_require_mention = GEMINI_RESPONDER_REQUIRE_MENTION

# 디스코드 봇 인텐트 설정
intents = discord.Intents.default()
intents.message_content = True

# 봇 인스턴스 생성
bot = commands.Bot(command_prefix=commands.when_mentioned, intents=intents)


def _build_recent_history(channel_id: int) -> str:
    history = conversation_histories[channel_id]
    if not history:
        return "(이전 대화 없음)"
    return "\n".join(history)


def _normalize_text(text: str) -> str:
    return " ".join(text.lower().split())


def _is_on_cooldown(channel_id: int) -> bool:
    elapsed = time.monotonic() - last_reply_at_by_channel[channel_id]
    return elapsed < max(0, GEMINI_RESPONDER_COOLDOWN_SECONDS)


def _responder_status_text() -> str:
    enabled_text = "ON" if responder_enabled else "OFF"
    target_bot_id_text = str(active_target_bot_id) if active_target_bot_id > 0 else "(없음)"
    target_bot_tag_text = active_target_bot_tag or "(없음)"
    return (
        f"대화 모드: {enabled_text}\n"
        f"채널 ID: {active_responder_channel_id}\n"
        f"대상 봇 ID: {target_bot_id_text}\n"
        f"대상 봇 태그: {target_bot_tag_text}\n"
        f"기억 턴: {GEMINI_RESPONDER_HISTORY_TURNS}\n"
        f"쿨다운(초): {GEMINI_RESPONDER_COOLDOWN_SECONDS}\n"
        f"멘션 필요: {'ON' if active_require_mention else 'OFF'}"
    )


async def load_cogs() -> None:
    for module_name, cog_name in COG_SPECS:
        try:
            module = import_module(module_name)
            cog_class = getattr(module, cog_name)
            await bot.add_cog(cog_class(bot))
            logger.info("Cog loaded: %s.%s", module_name, cog_name)
        except Exception:
            logger.exception("Failed to load cog: %s.%s", module_name, cog_name)
            raise

# 봇이 준비되었을 때 실행되는 이벤트
@bot.event
async def on_ready():
    logger.info("봇 로그인 성공: %s", bot.user)
    if bot.guilds:
        guild_summary = ", ".join(f"{g.name}({g.id})" for g in bot.guilds)
        logger.info("참여 서버 목록: %s", guild_summary)

# 슬래시 커맨드 등록 및 Cog 추가
@bot.event
async def setup_hook():
    await load_cogs()

    if DISCORD_GUILD_ID > 0:
        guild = discord.Object(id=DISCORD_GUILD_ID)
        logger.info("길드 커맨드 동기화 시작 | guild_id=%s", DISCORD_GUILD_ID)
        bot.tree.clear_commands(guild=guild)
        bot.tree.copy_global_to(guild=guild)
        synced = await asyncio.wait_for(bot.tree.sync(guild=guild), timeout=30)
        logger.info("길드 커맨드 동기화 완료 | guild_id=%s | count=%s", DISCORD_GUILD_ID, len(synced))
    else:
        logger.info("글로벌 커맨드 동기화 시작")
        synced = await asyncio.wait_for(bot.tree.sync(), timeout=30)
        logger.info("글로벌 커맨드 동기화 완료 | count=%s", len(synced))


@bot.tree.command(name="뫙움말", description="뫙뫙봇의 사용 가능한 명령을 보여줘요.")
async def mwang_help(interaction: discord.Interaction):
    help_text = (
        "🍠 뫙뫙봇 도움말\n"
        "/뫙움말 - 이 도움말을 보여줘요\n"
        "\n"
        "기본 슬래시 명령:\n"
        "/주사위 - 주사위를 굴려요\n"
        "/시간 - 현재 시간을 알려줘요\n"
        "/소라고동 [질문] - Gemini에게 질문해요\n"
        "/빌런 [유저] [채널] [일수] - 메시지 기반 빌런 분석\n"
        "\n"
        "봇-봇 대화 명령:\n"
        "/대화시작 [대상봇] - 고정 채널에서 자동 대화 시작\n"
        "/대화종료 - 자동 대화 중단\n"
        "/대화상태 - 현재 대화 설정 확인\n"
        "/대화설정 [멘션필요] - 멘션 응답 ON/OFF 설정\n"
        "/기억초기화 - 현재 채널 대화 기억 초기화\n"
        "\n"
        "기본 규칙:\n"
        "- 설정된 채널에서만 동작\n"
        "- 설정된 대상 봇에게만 반응\n"
        "- 쿨다운과 반복 억제로 루프를 방지"
    )
    await interaction.response.send_message(help_text)


@bot.tree.command(name="길드아이디", description="현재 서버 ID를 확인해요.")
async def guild_id(interaction: discord.Interaction):
    if interaction.guild_id is None:
        await interaction.response.send_message("서버 채널에서만 확인할 수 있어요.")
        return
    await interaction.response.send_message(f"현재 서버 ID: {interaction.guild_id}")


@bot.tree.command(name="대화시작", description="고정 채널에서 특정 봇과 자동 대화를 시작합니다.")
@app_commands.describe(target_bot="대화할 봇")
async def start_conversation(
    interaction: discord.Interaction,
    target_bot: discord.Member,
):
    global active_responder_channel_id, active_target_bot_id, active_target_bot_tag, responder_enabled

    if not target_bot.bot:
        await interaction.response.send_message("대상은 봇 계정이어야 합니다.")
        return

    if GEMINI_RESPONDER_CHANNEL_ID <= 0:
        await interaction.response.send_message(
            "고정 채널 ID가 설정되지 않았어요. .env의 GEMINI_RESPONDER_CHANNEL_ID를 확인해 주세요.",
        )
        return

    channel = bot.get_channel(GEMINI_RESPONDER_CHANNEL_ID)
    if not isinstance(channel, discord.TextChannel):
        await interaction.response.send_message(
            f"고정 채널을 찾을 수 없어요. 설정된 채널 ID: {GEMINI_RESPONDER_CHANNEL_ID}",
        )
        return

    active_responder_channel_id = GEMINI_RESPONDER_CHANNEL_ID
    active_target_bot_id = target_bot.id
    active_target_bot_tag = str(target_bot)
    responder_enabled = True
    conversation_histories[active_responder_channel_id].clear()
    recent_bot_replies[active_responder_channel_id].clear()
    last_reply_at_by_channel[active_responder_channel_id] = 0.0

    await interaction.response.send_message(
        f"대화 시작! 채널 <#{active_responder_channel_id}> / 대상 `{target_bot}`",
    )


@bot.tree.command(name="대화종료", description="자동 대화를 중단합니다.")
async def stop_conversation(interaction: discord.Interaction):
    global responder_enabled, active_target_bot_id, active_target_bot_tag
    responder_enabled = False
    active_target_bot_id = 0
    active_target_bot_tag = ""
    await interaction.response.send_message("대화 모드를 종료했어요.")


@bot.tree.command(name="대화상태", description="현재 자동 대화 설정을 확인합니다.")
async def conversation_status(interaction: discord.Interaction):
    await interaction.response.send_message(_responder_status_text())


@bot.tree.command(name="대화설정", description="대화 동작 설정(멘션 필요 여부)을 변경합니다.")
@app_commands.describe(멘션필요="ON이면 멘션된 메시지에만 응답")
async def conversation_config(
    interaction: discord.Interaction,
    멘션필요: Optional[bool] = None,
):
    global active_require_mention

    if 멘션필요 is not None:
        active_require_mention = 멘션필요
        await interaction.response.send_message(
            f"대화 설정 변경 완료: 멘션 필요 = {'ON' if active_require_mention else 'OFF'}"
        )
        return

    await interaction.response.send_message(
        f"현재 설정: 멘션 필요 = {'ON' if active_require_mention else 'OFF'}"
    )


@bot.tree.command(name="기억초기화", description="현재 채널의 대화 기억을 비웁니다.")
async def reset_memory(interaction: discord.Interaction):
    channel_id = interaction.channel_id
    if channel_id is None:
        await interaction.response.send_message("채널 정보를 확인할 수 없어요.")
        return

    conversation_histories[channel_id].clear()
    recent_bot_replies[channel_id].clear()
    last_reply_at_by_channel[channel_id] = 0.0
    await interaction.response.send_message("현재 채널 대화 기억을 초기화했어요.")

# 특정 채널에서만 메시지에 응답
@bot.event
async def on_message(message: discord.Message):
    # 봇 자신의 메시지 무시
    if message.author == bot.user:
        logger.info(
            "뫙뫙 발신 | 채널: %s (ID: %s) | 내용: %s",
            getattr(message.channel, "name", "unknown"),
            message.channel.id,
            message.content,
        )
        return

    if not responder_enabled:
        return

    if active_responder_channel_id <= 0 or message.channel.id != active_responder_channel_id:
        return

    logger.info(
        "메시지 수신 | 채널: %s (ID: %s) | 작성자: %s | 내용: %s",
        message.channel.name,
        message.channel.id,
        message.author,
        message.content,
    )

    if not message.author.bot:
        return

    logger.info(
        "상대 봇 메시지 감지 | author=%s | author_id=%s | channel_id=%s",
        message.author,
        message.author.id,
        message.channel.id,
    )

    if active_target_bot_id > 0 and message.author.id != active_target_bot_id:
        return

    if active_target_bot_tag and str(message.author) != active_target_bot_tag:
        return

    if active_require_mention and bot.user is not None and not bot.user.mentioned_in(message):
        return

    content = message.content.strip()
    if not content:
        return

    if _is_on_cooldown(message.channel.id):
        logger.info("쿨다운 중이라 응답을 생략합니다 | channel_id=%s", message.channel.id)
        return

    conversation_histories[message.channel.id].append(f"젬마: {content}")
    recent_history = _build_recent_history(message.channel.id)

    async with message.channel.typing():
        styled_prompt = (
            f"{GEMINI_RESPONDER_SYSTEM_PROMPT}\n\n"
            "최근 대화 기록:\n"
            f"{recent_history}\n\n"
            "뫙뫙 답변:"
        )
        response = await ask_gemini_question(styled_prompt)
        normalized = _normalize_text(response)
        if normalized in recent_bot_replies[message.channel.id]:
            logger.info("반복 응답 감지로 전송 생략 | channel_id=%s", message.channel.id)
            return

        recent_bot_replies[message.channel.id].append(normalized)
        conversation_histories[message.channel.id].append(f"뫙뫙: {response}")
        last_reply_at_by_channel[message.channel.id] = time.monotonic()
        logger.info(
            "뫙뫙 응답 생성 | channel_id=%s | preview=%s",
            message.channel.id,
            (response[:120] + "...") if len(response) > 120 else response,
        )
        for idx, chunk in enumerate(chunk_text(response, 1900)):
            if idx == 0:
                await message.reply(chunk)
            else:
                await message.channel.send(chunk)

# 봇 실행
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
bot.run(DISCORD_TOKEN)
