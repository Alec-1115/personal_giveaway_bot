import re
from datetime import datetime, timedelta, timezone

import discord
from discord import app_commands
from discord.ext import commands

from services.giveaway_dm import send_entry_dm
from services.giveaway_manager import GiveawayManager
from services.giveaway_messages import (
    create_giveaway_embed,
    update_entry_count
)


def parse_duration(value: str) -> int:

    match = re.fullmatch(
        r"\s*(\d+)\s*(seconds?|secs?|s|minutes?|mins?|m|hours?|hrs?|h|days?|d)\s*",
        value.lower()
    )

    if not match:
        raise ValueError(
            "Invalid duration. Use something like 30m, 24h or 7d."
        )

    amount = int(match.group(1))
    unit = match.group(2)

    if amount <= 0:
        raise ValueError(
            "Duration must be greater than zero."
        )

    if unit in {
        "s",
        "sec",
        "secs",
        "second",
        "seconds"
    }:
        return amount

    if unit in {
        "m",
        "min",
        "mins",
        "minute",
        "minutes"
    }:
        return amount * 60

    if unit in {
        "h",
        "hr",
        "hrs",
        "hour",
        "hours"
    }:
        return amount * 3600

    return amount * 86400


class GiveawayView(discord.ui.View):

    def __init__(
        self,
        giveaway_name: str,
        reward: discord.Role,
        winners: int,
        duration: int
    ):

        super().__init__(timeout=duration)

        self.giveaway_name = giveaway_name
        self.reward = reward
        self.winners = winners

        self.entries: set[int] = set()

        self.message: discord.Message | None = None

    @discord.ui.button(
        label="Enter Giveaway",
        emoji="🎉",
        style=discord.ButtonStyle.primary
    )
    async def enter(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        user = interaction.user

        if user.id in self.entries:

            await interaction.response.send_message(
                "You have already entered this giveaway!",
                ephemeral=True
            )

            return

        # Add user to entries.
        self.entries.add(user.id)

        # Update entry count.
        if self.message:

            embed = self.message.embeds[0]

            embed = update_entry_count(
                embed,
                len(self.entries)
            )

            await self.message.edit(
                embed=embed,
                view=self
            )

        # Respond to the interaction immediately.
        await interaction.response.send_message(
            "You've entered the giveaway! 🎉",
            ephemeral=True
        )

        # Send confirmation DM.
        if self.message:

            await send_entry_dm(
                user=user,
                giveaway_name=self.giveaway_name,
                reward=self.reward,
                winners=self.winners,
                giveaway_link=self.message.jump_url
            )

    async def on_timeout(self):
        pass


class GiveawayCreate(commands.Cog):

    def __init__(
        self,
        bot: commands.Bot
    ):

        self.bot = bot

    @app_commands.command(
        name="gcreate",
        description="Create a role giveaway."
    )
    @app_commands.describe(
        name="The name of the giveaway",
        reward="The Discord role being given away",
        winners="How many winners there will be",
        duration="How long entries stay open, e.g. 24h or 7d"
    )
    async def gcreate(
        self,
        interaction: discord.Interaction,
        name: str,
        reward: discord.Role,
        winners: app_commands.Range[int, 1, 100],
        duration: str
    ):

        # Parse duration.
        try:

            duration_seconds = parse_duration(
                duration
            )

        except ValueError as error:

            await interaction.response.send_message(
                str(error),
                ephemeral=True
            )

            return

        # Calculate end time.
        end_time = (
            datetime.now(timezone.utc)
            + timedelta(
                seconds=duration_seconds
            )
        )

        # Create embed.
        embed = create_giveaway_embed(
            name=name,
            reward=reward,
            winners=winners,
            end_timestamp=int(
                end_time.timestamp()
            )
        )

        # Create button view.
        view = GiveawayView(
            giveaway_name=name,
            reward=reward,
            winners=winners,
            duration=duration_seconds
        )

        # Send giveaway.
        await interaction.response.send_message(
            embed=embed,
            view=view
        )

        # Get the sent message.
        view.message = (
            await interaction.original_response()
        )

        # Start manager.
        manager = GiveawayManager(
            bot=self.bot,
            message=view.message,
            giveaway_name=name,
            reward=reward,
            winners=winners,
            duration=duration_seconds,
            entries=view.entries
        )

        self.bot.loop.create_task(
            manager.start()
        )


async def setup(bot: commands.Bot):

    await bot.add_cog(
        GiveawayCreate(bot)
    )