# cogs/python_time.py
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
from zoneinfo import ZoneInfo

class TimeCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="시간", description="현재 시간을 알려드릴까요?")
    async def get_time(self, interaction: discord.Interaction):
        now = datetime.now(ZoneInfo("Asia/Seoul"))
        formatted_time = now.strftime("%p %I시 %M분").replace("AM", "오전").replace("PM", "오후")
        await interaction.response.send_message(f"지금은 {formatted_time}입니다.")
