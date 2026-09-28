import asyncio

import discord

from services.giveaway_dm import (
    send_redeemable_dm,
    send_winner_dm
)
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
        reward_name: str,
        reward_type: str,
        reward: discord.Role | None,
        redeemable_links: list[str],
        winners: int,
        duration: int,
        entries: set[int]
    ):

        self.bot = bot
        self.message = message

        self.giveaway_name = giveaway_name
        self.reward_name = reward_name
        self.reward_type = reward_type

        self.reward = reward
        self.redeemable_links = redeemable_links

        self.winners = winners
        self.duration = duration
        self.entries = entries

        self.closed = False

    async def start(self):

        await asyncio.sleep(
            self.duration
        )

        await self.end()

    async def end(self):

        if self.closed:
            return

        self.closed = True

        winner_ids = select_winners(
            entries=self.entries,
            winner_count=self.winners
        )

        winners = []

        guild = self.message.guild

        if guild is None:
            return

        for index, user_id in enumerate(
            winner_ids
        ):

            member = guild.get_member(
                user_id
            )

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

            # Role reward.
            if self.reward_type == "role":

                if self.reward is not None:

                    await give_role_prize(
                        member=member,
                        role=self.reward
                    )

                    await send_winner_dm(
                        user=member,
                        giveaway_name=self.giveaway_name,
                        reward_name=self.reward_name
                    )

            # Redeemable reward.
            elif self.reward_type == "redeemable":

                if index < len(
                    self.redeemable_links
                ):

                    link = self.redeemable_links[
                        index
                    ]

                    await send_redeemable_dm(
                        user=member,
                        giveaway_name=self.giveaway_name,
                        reward_name=self.reward_name,
                        link=link
                    )

        embed = self.message.embeds[0]

        embed = close_giveaway_embed(
            embed=embed,
            winners=winners
        )

        view = create_closed_view()

        await self.message.edit(
            embed=embed,
            view=view
        )