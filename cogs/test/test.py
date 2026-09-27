import discord
from discord import app_commands
from discord.ext import commands


class Test(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="test",
        description="Check if the bot is working."
    )
    async def test(self, interaction: discord.Interaction):
        await interaction.response.send_message("I'm working!", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Test(bot))