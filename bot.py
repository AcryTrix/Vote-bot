import discord
import random
import os

from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('TOKEN')


class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.messages = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()


bot = MyBot()


def random_color():
    return discord.Color(random.randint(0, 0xFFFFFF))


@bot.tree.command(
    name="create_vote",
    description="Slash command for creating a vote!",
)
@app_commands.describe(
    text="The text to display in the vote",
    vote_type="The type of the vote (default or select)",
    num_options="Number of options for select type vote (1-9)"
)
async def create_vote(interaction: discord.Interaction, text: str, vote_type: str = "default", num_options: int = 2):
    embed = discord.Embed(description=text, color=random_color())
    await interaction.response.send_message(embed=embed)

    message = await interaction.original_response()

    if vote_type == "default":
        await message.add_reaction("✅")
        await message.add_reaction("❌")
    elif vote_type == "select":
        if not 1 <= num_options <= 9:
            await interaction.followup.send("Number of options must be between 1 and 9.")
            return
        for i in range(1, num_options + 1):
            await message.add_reaction(f"{i}\u20e3")


bot.run(TOKEN)
