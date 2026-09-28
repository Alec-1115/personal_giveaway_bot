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


# =========================================================
# HELPERS
# =========================================================

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


def parse_redeemable_links(value: str) -> list[str]:
    return [
        link.strip()
        for link in value.splitlines()
        if link.strip()
    ]


# =========================================================
# GIVEAWAY VIEW
# =========================================================

class GiveawayView(discord.ui.View):

    def __init__(
        self,
        giveaway_name: str,
        reward_name: str,
        reward: discord.Role | None,
        winners: int,
        duration: int
    ):
        super().__init__(
            timeout=duration
        )

        self.giveaway_name = giveaway_name
        self.reward_name = reward_name
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

        # Already entered
        if user.id in self.entries:

            await interaction.response.send_message(
                "You have already entered this giveaway!",
                ephemeral=True
            )

            return

        # Add entry
        self.entries.add(user.id)

        await interaction.response.send_message(
            "You've entered the giveaway! 🎉",
            ephemeral=True
        )

        # Update entry count
        if self.message:

            embed = self.message.embeds[0]

            embed = update_entry_count(
                embed=embed,
                entry_count=len(self.entries)
            )

            await self.message.edit(
                embed=embed,
                view=self
            )

            # Send confirmation DM
            await send_entry_dm(
                user=user,
                giveaway_name=self.giveaway_name,
                reward_name=self.reward_name,
                winners=self.winners,
                giveaway_link=self.message.jump_url
            )

    async def on_timeout(self):
        pass


# =========================================================
# REWARD TYPE SELECTOR
# =========================================================

class RewardTypeView(discord.ui.View):

    def __init__(
        self,
        bot: commands.Bot
    ):
        super().__init__(
            timeout=300
        )

        self.bot = bot

    @discord.ui.select(
        placeholder="Select reward type...",
        options=[
            discord.SelectOption(
                label="Role",
                description="Give winners a Discord role.",
                emoji="🏷️",
                value="role"
            ),
            discord.SelectOption(
                label="Redeemable Link",
                description="Give winners a private redeemable link.",
                emoji="🔗",
                value="redeemable"
            )
        ]
    )
    async def reward_type_select(
        self,
        interaction: discord.Interaction,
        select: discord.ui.Select
    ):

        reward_type = select.values[0]

        # -------------------------------------------------
        # ROLE
        # -------------------------------------------------

        if reward_type == "role":

            await interaction.response.edit_message(
                content=(
                    "First, select the Discord role that will "
                    "be given to the winners."
                ),
                view=RoleSelectorView(
                    bot=self.bot
                )
            )

            return

        # -------------------------------------------------
        # REDEEMABLE
        # -------------------------------------------------

        await interaction.response.edit_message(
            content=(
                "Select the channel where the giveaway "
                "will be posted."
            ),
            view=RedeemableChannelSelectorView(
                bot=self.bot
            )
        )


# =========================================================
# ROLE SELECTOR
# =========================================================

class RoleSelectorView(discord.ui.View):

    def __init__(
        self,
        bot: commands.Bot
    ):
        super().__init__(
            timeout=300
        )

        self.bot = bot

    @discord.ui.select(
        cls=discord.ui.RoleSelect,
        placeholder="Select the reward role..."
    )
    async def role_select(
        self,
        interaction: discord.Interaction,
        select: discord.ui.RoleSelect
    ):

        role = select.values[0]

        await interaction.response.edit_message(
            content=(
                "Now select the channel where the giveaway "
                "will be posted."
            ),
            view=RoleChannelSelectorView(
                bot=self.bot,
                role=role
            )
        )


# =========================================================
# ROLE CHANNEL SELECTOR
# =========================================================

class RoleChannelSelectorView(discord.ui.View):

    def __init__(
        self,
        bot: commands.Bot,
        role: discord.Role
    ):
        super().__init__(
            timeout=300
        )

        self.bot = bot
        self.role = role

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        placeholder="Select giveaway channel...",
        channel_types=[
            discord.ChannelType.text
        ]
    )
    async def channel_select(
        self,
        interaction: discord.Interaction,
        select: discord.ui.ChannelSelect
    ):

        selected_channel = select.values[0]

        if interaction.guild is None:

            await interaction.response.send_message(
                "This can only be used inside a server.",
                ephemeral=True
            )

            return

        # Resolve AppCommandChannel into the real Discord channel
        channel = interaction.guild.get_channel(
            selected_channel.id
        )

        if not isinstance(channel, discord.TextChannel):

            await interaction.response.send_message(
                "I couldn't access that text channel.",
                ephemeral=True
            )

            return

        await interaction.response.send_modal(
            RoleGiveawayModal(
                bot=self.bot,
                role=self.role,
                channel=channel
            )
        )


# =========================================================
# REDEEMABLE CHANNEL SELECTOR
# =========================================================

class RedeemableChannelSelectorView(discord.ui.View):

    def __init__(
        self,
        bot: commands.Bot
    ):
        super().__init__(
            timeout=300
        )

        self.bot = bot

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        placeholder="Select giveaway channel...",
        channel_types=[
            discord.ChannelType.text
        ]
    )
    async def channel_select(
        self,
        interaction: discord.Interaction,
        select: discord.ui.ChannelSelect
    ):

        selected_channel = select.values[0]

        if interaction.guild is None:

            await interaction.response.send_message(
                "This can only be used inside a server.",
                ephemeral=True
            )

            return

        # Resolve AppCommandChannel into the real Discord channel
        channel = interaction.guild.get_channel(
            selected_channel.id
        )

        if not isinstance(channel, discord.TextChannel):

            await interaction.response.send_message(
                "I couldn't access that text channel.",
                ephemeral=True
            )

            return

        await interaction.response.send_modal(
            RedeemableGiveawayModal(
                bot=self.bot,
                channel=channel
            )
        )


# =========================================================
# ROLE GIVEAWAY MODAL
# =========================================================

class RoleGiveawayModal(discord.ui.Modal):

    giveaway_name = discord.ui.TextInput(
        label="Giveaway Name",
        placeholder="Enter the giveaway name...",
        required=True,
        max_length=100
    )

    description = discord.ui.TextInput(
        label="Description",
        placeholder="Enter the giveaway description...",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=1000
    )

    winners = discord.ui.TextInput(
        label="Number of Winners",
        placeholder="Example: 1",
        required=True,
        max_length=3
    )

    duration = discord.ui.TextInput(
        label="Duration",
        placeholder="Example: 30m, 24h or 7d",
        required=True,
        max_length=20
    )

    def __init__(
        self,
        bot: commands.Bot,
        role: discord.Role,
        channel: discord.TextChannel
    ):
        super().__init__(
            title="Create Role Giveaway"
        )

        self.bot = bot
        self.role = role
        self.channel = channel

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):

        # Winners
        try:

            winner_count = int(
                self.winners.value
            )

        except ValueError:

            await interaction.response.send_message(
                "Number of winners must be a whole number.",
                ephemeral=True
            )

            return

        if not 1 <= winner_count <= 100:

            await interaction.response.send_message(
                "Number of winners must be between 1 and 100.",
                ephemeral=True
            )

            return

        # Duration
        try:

            duration_seconds = parse_duration(
                self.duration.value
            )

        except ValueError as error:

            await interaction.response.send_message(
                str(error),
                ephemeral=True
            )

            return

        # Create giveaway
        await create_giveaway(
            interaction=interaction,
            bot=self.bot,
            channel=self.channel,
            giveaway_name=self.giveaway_name.value,
            reward_name=self.role.name,
            description=self.description.value,
            reward=self.role,
            reward_type="role",
            winners=winner_count,
            duration=duration_seconds,
            redeemable_links=[]
        )


# =========================================================
# REDEEMABLE GIVEAWAY MODAL
# =========================================================

class RedeemableGiveawayModal(discord.ui.Modal):

    giveaway_name = discord.ui.TextInput(
        label="Giveaway Name",
        placeholder="Enter the giveaway name...",
        required=True,
        max_length=100
    )

    reward_name = discord.ui.TextInput(
        label="Reward Name",
        placeholder="What is being given away?",
        required=True,
        max_length=100
    )

    description = discord.ui.TextInput(
        label="Description",
        placeholder="Enter the giveaway description...",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=1000
    )

    winners = discord.ui.TextInput(
        label="Number of Winners",
        placeholder="Example: 3",
        required=True,
        max_length=3
    )

    duration = discord.ui.TextInput(
        label="Duration",
        placeholder="Example: 30m, 24h or 7d",
        required=True,
        max_length=20
    )

    def __init__(
        self,
        bot: commands.Bot,
        channel: discord.TextChannel
    ):
        super().__init__(
            title="Create Redeemable Giveaway"
        )

        self.bot = bot
        self.channel = channel

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):

        # Winners
        try:

            winner_count = int(
                self.winners.value
            )

        except ValueError:

            await interaction.response.send_message(
                "Number of winners must be a whole number.",
                ephemeral=True
            )

            return

        if not 1 <= winner_count <= 100:

            await interaction.response.send_message(
                "Number of winners must be between 1 and 100.",
                ephemeral=True
            )

            return

        # Duration
        try:

            duration_seconds = parse_duration(
                self.duration.value
            )

        except ValueError as error:

            await interaction.response.send_message(
                str(error),
                ephemeral=True
            )

            return

        # Store the details in a view.
        # The button will open the links modal.
        view = RedeemableLinksStartView(
            bot=self.bot,
            channel=self.channel,
            giveaway_name=self.giveaway_name.value,
            reward_name=self.reward_name.value,
            description=self.description.value,
            winners=winner_count,
            duration=duration_seconds
        )

        await interaction.response.send_message(
            (
                "Your giveaway details are ready.\n\n"
                f"**Winners:** {winner_count}\n"
                f"**Channel:** {self.channel.mention}\n\n"
                "Click the button below to add the "
                "redeemable links."
            ),
            view=view,
            ephemeral=True
        )


# =========================================================
# REDEEMABLE LINKS START VIEW
# =========================================================

class RedeemableLinksStartView(discord.ui.View):

    def __init__(
        self,
        bot: commands.Bot,
        channel: discord.TextChannel,
        giveaway_name: str,
        reward_name: str,
        description: str,
        winners: int,
        duration: int
    ):
        super().__init__(
            timeout=300
        )

        self.bot = bot
        self.channel = channel
        self.giveaway_name = giveaway_name
        self.reward_name = reward_name
        self.description = description
        self.winners = winners
        self.duration = duration

    @discord.ui.button(
        label="Add Redeemable Links",
        emoji="🔗",
        style=discord.ButtonStyle.primary
    )
    async def add_links(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.send_modal(
            RedeemableLinksModal(
                bot=self.bot,
                channel=self.channel,
                giveaway_name=self.giveaway_name,
                reward_name=self.reward_name,
                description=self.description,
                winners=self.winners,
                duration=self.duration
            )
        )


# =========================================================
# REDEEMABLE LINKS MODAL
# =========================================================

class RedeemableLinksModal(discord.ui.Modal):

    links = discord.ui.TextInput(
        label="Redeemable Links",
        placeholder="One link per line...",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=4000
    )

    def __init__(
        self,
        bot: commands.Bot,
        channel: discord.TextChannel,
        giveaway_name: str,
        reward_name: str,
        description: str,
        winners: int,
        duration: int
    ):
        super().__init__(
            title="Add Redeemable Links"
        )

        self.bot = bot
        self.channel = channel
        self.giveaway_name = giveaway_name
        self.reward_name = reward_name
        self.description = description
        self.winners = winners
        self.duration = duration

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):

        links = parse_redeemable_links(
            self.links.value
        )

        # Need enough links for all winners
        if len(links) < self.winners:

            await interaction.response.send_message(
                (
                    f"You need at least {self.winners} "
                    f"redeemable links for {self.winners} "
                    "winners."
                ),
                ephemeral=True
            )

            return

        await create_giveaway(
            interaction=interaction,
            bot=self.bot,
            channel=self.channel,
            giveaway_name=self.giveaway_name,
            reward_name=self.reward_name,
            description=self.description,
            reward=None,
            reward_type="redeemable",
            winners=self.winners,
            duration=self.duration,
            redeemable_links=links
        )


# =========================================================
# CREATE GIVEAWAY
# =========================================================

async def create_giveaway(
    interaction: discord.Interaction,
    bot: commands.Bot,
    channel: discord.TextChannel,
    giveaway_name: str,
    reward_name: str,
    description: str,
    reward: discord.Role | None,
    reward_type: str,
    winners: int,
    duration: int,
    redeemable_links: list[str]
):

    # Calculate end time
    end_time = (
        datetime.now(timezone.utc)
        + timedelta(
            seconds=duration
        )
    )

    # Create embed
    embed = create_giveaway_embed(
        name=giveaway_name,
        reward_name=reward_name,
        reward=reward,
        description=description,
        winners=winners,
        end_timestamp=int(
            end_time.timestamp()
        )
    )

    # Create giveaway view
    view = GiveawayView(
        giveaway_name=giveaway_name,
        reward_name=reward_name,
        reward=reward,
        winners=winners,
        duration=duration
    )

    # Send giveaway to selected channel
    try:

        message = await channel.send(
            embed=embed,
            view=view
        )

    except discord.Forbidden:

        await interaction.response.send_message(
            (
                f"I don't have permission to send messages "
                f"in {channel.mention}."
            ),
            ephemeral=True
        )

        return

    except discord.HTTPException:

        await interaction.response.send_message(
            "I couldn't send the giveaway to that channel.",
            ephemeral=True
        )

        return

    # Store message on view
    view.message = message

    # Create manager
    manager = GiveawayManager(
        bot=bot,
        message=message,
        giveaway_name=giveaway_name,
        reward_name=reward_name,
        reward_type=reward_type,
        reward=reward,
        redeemable_links=redeemable_links,
        winners=winners,
        duration=duration,
        entries=view.entries
    )

    # Start giveaway timer
    bot.loop.create_task(
        manager.start()
    )

    # Tell creator it worked
    await interaction.response.send_message(
        (
            f"Giveaway created in {channel.mention}! 🎉"
        ),
        ephemeral=True
    )


# =========================================================
# COG
# =========================================================

class GiveawayCreate(commands.Cog):

    def __init__(
        self,
        bot: commands.Bot
    ):
        self.bot = bot

    @app_commands.command(
        name="gcreate",
        description="Create a giveaway."
    )
    async def gcreate(
        self,
        interaction: discord.Interaction
    ):

        view = RewardTypeView(
            bot=self.bot
        )

        await interaction.response.send_message(
            "Select the type of reward for this giveaway.",
            view=view,
            ephemeral=True
        )


async def setup(
    bot: commands.Bot
):

    await bot.add_cog(
        GiveawayCreate(bot)
    )