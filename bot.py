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
        intents.reactions = True  # Ensure reactions are enabled
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()


bot = MyBot()


def random_color():
    return discord.Color(random.randint(0, 0xFFFFFF))


active_votes = {}


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

    active_votes[message.id] = {
        "message": message,
        "text": text,
        "vote_type": vote_type,
        "num_options": num_options
    }


class VoteSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=f"Vote {vote_id}", value=str(vote_id))
            for vote_id in active_votes
        ]
        super().__init__(placeholder="Choose a vote to edit...", min_values=1, max_values=1, options=options)

    async def callback(self, select_interaction: discord.Interaction):
        vote_id = int(self.values[0])
        vote_data = active_votes[vote_id]

        class EditView(discord.ui.View):
            def __init__(self, vote_id: int):
                super().__init__()
                self.vote_id = vote_id

            @discord.ui.button(label="Edit Text", style=discord.ButtonStyle.primary)
            async def edit_text(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                await button_interaction.response.send_modal(EditTextModal(self.vote_id))

            @discord.ui.button(label="Delete Vote", style=discord.ButtonStyle.danger)
            async def delete_vote(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                message = vote_data["message"]
                await message.delete()
                del active_votes[self.vote_id]
                await button_interaction.response.send_message("Vote deleted.", ephemeral=True)

            @discord.ui.button(label="End Vote", style=discord.ButtonStyle.secondary)
            async def end_vote(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                message = vote_data["message"]
                message = await button_interaction.channel.fetch_message(message.id)
                reactions = message.reactions
                results = {}
                for reaction in reactions:
                    if reaction.emoji not in results:
                        results[reaction.emoji] = reaction.count - 1  # Subtracting bot's own reaction
                results_text = "\n".join([f"{emoji}: {count}" for emoji, count in results.items()])
                if not results_text:
                    results_text = "No votes recorded."
                results_embed = discord.Embed(title="Vote Results", description=results_text, color=random_color())
                await button_interaction.response.send_message(embed=results_embed, ephemeral=True)
                await message.delete()
                del active_votes[self.vote_id]

        view = EditView(vote_id)
        await select_interaction.response.send_message(f"Selected vote: {vote_data['text']}", view=view, ephemeral=True)


class EditTextModal(discord.ui.Modal, title="Edit Vote Text"):
    new_text = discord.ui.TextInput(label="New Vote Text")

    def __init__(self, vote_id: int):
        super().__init__()
        self.vote_id = vote_id

    async def on_submit(self, modal_interaction: discord.Interaction):
        new_text = self.new_text.value
        vote_data = active_votes[self.vote_id]
        message = vote_data["message"]
        embed = discord.Embed(description=new_text, color=random_color())
        await message.edit(embed=embed)
        vote_data["text"] = new_text
        await modal_interaction.response.send_message("Vote text updated.", ephemeral=True)


@bot.tree.command(
    name="edit_vote",
    description="Slash command for editing votes!",
)
async def edit_vote(interaction: discord.Interaction):
    if not active_votes:
        await interaction.response.send_message("There are no active votes to edit.", ephemeral=True)
        return

    view = discord.ui.View()
    view.add_item(VoteSelect())
    await interaction.response.send_message("Select a vote to edit:", view=view, ephemeral=True)

bot.run(TOKEN)
