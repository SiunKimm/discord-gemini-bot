# bot.py
from importlib import import_module
import logging
import discord
from discord.ext import commands

from config.settings import DISCORD_TOKEN

COG_SPECS = [
    ("cogs.python_dice", "DiceCog"),
    ("cogs.python_time", "TimeCog"),
    ("cogs.google_gemini", "GeminiCog"),
    ("cogs.user_analysis", "UserAnalysisCog"),
]

logger = logging.getLogger(__name__)

# 디스코드 봇 인텐트 설정
intents = discord.Intents.default()
intents.message_content = True

# 봇 인스턴스 생성
bot = commands.Bot(command_prefix="/", intents=intents)


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

# 슬래시 커맨드 등록 및 Cog 추가
@bot.event
async def setup_hook():
    # 모든 글로벌 커맨드 초기화
    bot.tree.clear_commands(guild=None)

    await load_cogs()

    # 글로벌 커맨드 재등록
    await bot.tree.sync()
    logger.info("커맨드 초기화 및 재등록 완료")

# 봇 실행
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
bot.run(DISCORD_TOKEN)
