import asyncio

import discord

from services.giveaway_dm import send_winner_dm
from services.giveaway_messages import (
    close_giveaway_embed,
    create_closed_view
)
from services.giveaway_prizes import give_role_prize
from services.giveaway_winners import select_winners


class GiveawayManager:

    def __init__(
        self,
        bot: discord.Client,
        message: discord.Message,
        giveaway_name: str,
        reward: discord.Role,
        winners: int,
        duration: int,
        entries: set[int]
    ):
        self.bot = bot
        self.message = message
        self.giveaway_name = giveaway_name
        self.reward = reward
        self.winners = winners
        self.duration = duration
        self.entries = entries

        self.closed = False

    async def start(self):
        """Wait for the giveaway duration, then end it."""

        await asyncio.sleep(
            self.duration
        )

        await self.end()

    async def end(self):
        """Close the giveaway and process the winners."""

        if self.closed:
            return

        self.closed = True

        # Select winners.
        winner_ids = select_winners(
            entries=self.entries,
            winner_count=self.winners
        )

        winners = []

        # Get the guild the giveaway was created in.
        guild = self.message.guild

        if guild is None:
            return

        # Process each winner.
        for user_id in winner_ids:

            # Get the member from the server.
            member = guild.get_member(user_id)

            if member is None:

                try:
                    member = await guild.fetch_member(
                        user_id
                    )

                except discord.NotFound:
                    continue

                except discord.HTTPException:
                    continue

            winners.append(member)

            # Give the role prize.
            await give_role_prize(
                member=member,
                role=self.reward
            )

            # Send winner DM.
            await send_winner_dm(
                user=member,
                giveaway_name=self.giveaway_name,
                reward=self.reward
            )

        # Get the current giveaway embed.
        embed = self.message.embeds[0]

        # Update the giveaway embed.
        embed = close_giveaway_embed(
            embed=embed,
            winners=winners
        )

        # Create the disabled "Closed" button.
        view = create_closed_view()

        # Update the giveaway message.
        await self.message.edit(
            embed=embed,
            view=view
        )