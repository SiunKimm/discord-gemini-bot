import discord
import logging
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta, timezone
from typing import List

from config.settings import ANALYSIS_DEFAULT_DAYS, ANALYSIS_MAX_DAYS
from utils.gemini_wrapper import ask_gemini_question
from utils.text_utils import chunk_text

logger = logging.getLogger(__name__)


class UserAnalysisCog(commands.Cog):
    MAX_MESSAGE_CHUNK = 1900

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="빌런",
        description="과연 누가 이 사회의 빌런인가? 공신력있는 출구조사를 통해 결과를 제시합니다."
    )
    @app_commands.describe(
        user="분석할 빌런 후보",
        channel="분석할 채널",
        days="며칠 전부터 대화를 분석할지 입력 (기본값: 7일)"
    )
    async def analyze_user(
        self,
        interaction: discord.Interaction,
        user: discord.User,
        channel: discord.TextChannel,
        days: int = ANALYSIS_DEFAULT_DAYS,
    ):
        if not self._is_valid_days(days):
            await interaction.response.send_message(
                f"days는 1부터 {ANALYSIS_MAX_DAYS} 사이로 입력해 주세요.",
                ephemeral=True,
            )
            return

        if self.bot.user and user.id == self.bot.user.id:
            await interaction.response.send_message("일단 난 빌런아님 ㄹㅇㅋㅋ", ephemeral=True)
            return

        await interaction.response.send_message(
            f"빌런 분석을 위해 `{channel.name}` 채널에서 `{user.display_name}`님의 최근 {days}일간 메시지를 수집 중입니다...",
            ephemeral=True,
        )

        end_time = datetime.utcnow().replace(tzinfo=timezone.utc)
        start_time = end_time - timedelta(days=days)

        messages = await self._collect_user_messages(channel, user.id, start_time)
        if messages is None:
            await interaction.followup.send("채널 메시지를 읽을 권한이 없거나 조회 중 오류가 발생했어요.")
            return

        if not messages:
            await interaction.followup.send("형님, 이 친구 말을 잘 안하는데요?")
            return

        messages.sort(key=lambda m: m.created_at)
        actual_start_date = messages[0].created_at.date()
        actual_end_date = messages[-1].created_at.date()

        combined_text = "\n".join(msg.content for msg in messages)
        message_count = len(messages)

        prompt = self._build_prompt(
            channel_name=channel.name,
            user_name=user.display_name,
            start_time=start_time,
            end_time=end_time,
            actual_start_date=actual_start_date,
            actual_end_date=actual_end_date,
            combined_text=combined_text,
        )

        result = await ask_gemini_question(prompt)

        header = (
            f"🧠 `{channel.name}` 채널에서 `{user.display_name}`님을 최근 {days}일간 분석한 결과입니다.\n"
            f"💬 수집된 메시지 수: {message_count}개\n"
            f"📅 실제 수집된 메시지 범위: {actual_start_date} ~ {actual_end_date}\n"
        )
        await interaction.followup.send(header)

        for chunk in chunk_text(result, self.MAX_MESSAGE_CHUNK):
            await interaction.followup.send(chunk)

    @staticmethod
    def _is_valid_days(days: int) -> bool:
        return 1 <= days <= ANALYSIS_MAX_DAYS

    @staticmethod
    async def _collect_user_messages(
        channel: discord.TextChannel,
        user_id: int,
        start_time: datetime,
    ) -> List[discord.Message] | None:
        messages: List[discord.Message] = []
        try:
            async for msg in channel.history(limit=None, after=start_time, oldest_first=True):
                if msg.author.id == user_id and msg.content:
                    messages.append(msg)
        except (discord.Forbidden, discord.HTTPException):
            logger.exception("Failed to collect channel messages for analysis")
            return None
        return messages

    @staticmethod
    def _build_prompt(
        channel_name: str,
        user_name: str,
        start_time: datetime,
        end_time: datetime,
        actual_start_date,
        actual_end_date,
        combined_text: str,
    ) -> str:
        return f"""
당신은 유쾌하지만 냉정한 Discord 채널 전담 '빌런 감별사'입니다.  
사명은 단 하나: 채널을 교란시키는 언행의 소유자를 가려내는 것.

아래는 `{channel_name}` 채널에서 `{user_name}` 사용자가 남긴 실제 메시지 모음입니다.  
(분석 요청 범위: {start_time.date()} ~ {end_time.date()} / 실제 수집된 메시지 범위: {actual_start_date} ~ {actual_end_date})

당신은 이 기록을 바탕으로 다음의 항목을 명확하고 재치 있게 분석해야 합니다:

---

1. **말투 스타일 요약**  
   - 비속어, 유행어, 반복되는 말버릇, 감정 표현 방식 등

2. **성격적 특성**  
   - 이 사람, 어떤 사람 같나요? (예: 활발한 선동가, 관종력 있는 철학자, 혼자 떠드는 마이웨이 등)

3. **집착 or 과몰입 주제**  
   - 특정 관심사, 인물, 상황에 과도하게 몰입하는 경향이 보이나요?

4. **위험 신호**  
   - 다른 사람을 당황시키거나 혼란스럽게 할 만한 말투, 드립, 기묘한 언어 습관은 어떤 게 있나요?

5. **혼돈 유발 지수 평가 (10점 만점)**  
   - 이 사람의 메시지가 채팅방 분위기에 끼치는 영향력을 점수로 평가해 주세요.  
   - 예: 9점 = 드립 한 방에 채팅방 폭파 가능, 2점 = 무해한 다람쥐

6. **최종 판별**  
   - 이 사람은 진짜 ‘빌런’인가요, 아니면 다소 시끄러운 시민인가요?  
   - 판단 근거를 꼭 간단하게 정리해 주세요.

---

결과는 분석가의 보고서 스타일로 작성하되, 너무 학문적일 필요는 없습니다.  
센스 있는 드립과 단호한 판단력을 기대합니다.

마지막 줄에는 반드시 다음 중 하나로 마무리해 주세요:

- 🤡 **결론: 이 인간은 빌런입니다!**  
- 🕊️ **결론: 빌런 아님. 착한 시민입니다.**

---
{combined_text}
---
"""
