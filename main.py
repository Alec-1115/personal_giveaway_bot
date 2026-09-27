import discord
from discord.ext import commands

from config import DISCORD_TOKEN, GUILD_ID


class GiveawayBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()

        super().__init__(
            command_prefix="!",
            intents=intents
        )

    async def setup_hook(self):
        await self.load_extension("cogs.cog")

        guild = discord.Object(id=int(GUILD_ID))

        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

        print("Slash commands synced.")


bot = GiveawayBot()


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


bot.run(DISCORD_TOKEN)