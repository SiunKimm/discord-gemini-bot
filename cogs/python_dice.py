# cogs/python_dice.py
import random
import discord
from discord import app_commands
from discord.ext import commands

class DiceCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="주사위", description="운을 시험해 보세요")
    async def roll_dice(self, interaction: discord.Interaction):
        num = random.randint(1, 6)
        await interaction.response.send_message(f"주사위 결과는 {num}입니다.")
