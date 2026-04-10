# cogs/google_gemini.py
import discord
from discord import app_commands
from discord.ext import commands
from utils.gemini_wrapper import ask_gemini_question
from utils.text_utils import chunk_text

class GeminiCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="소라고동", description="마법의 소라고동님 도와주세요")
    async def ask_gemini(self, interaction: discord.Interaction, question: str):
        await interaction.response.send_message(f"'{question}' 에 대해 생각 중... 잠시만 기다려줘!", ephemeral=True)
        response_text = await ask_gemini_question(question)
        for chunk in chunk_text(response_text):
            await interaction.followup.send(chunk)
