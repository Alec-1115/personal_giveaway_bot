import discord


def create_giveaway_embed(
    name: str,
    reward_name: str,
    reward: discord.Role | None,
    description: str,
    winners: int,
    end_timestamp: int
) -> discord.Embed:

    # Role giveaways display the actual role.
    # Redeemable giveaways display the reward name.
    if reward is not None:
        prize_text = reward.mention
    else:
        prize_text = reward_name

    embed = discord.Embed(
        title=f"🎉 {name}",
        description=(
            f"**Prize:** {prize_text}\n\n"
            f"{description}\n\n"
            "Click the button below to enter!"
        ),
        colour=discord.Colour.blurple()
    )

    embed.add_field(
        name="Winners",
        value=str(winners),
        inline=True
    )

    embed.add_field(
        name="Entries",
        value="0",
        inline=True
    )

    embed.add_field(
        name="Ends",
        value=f"<t:{end_timestamp}:R>",
        inline=True
    )

    embed.set_footer(
        text="Giveaway"
    )

    return embed


def update_entry_count(
    embed: discord.Embed,
    entry_count: int
) -> discord.Embed:

    for index, field in enumerate(embed.fields):

        if field.name == "Entries":

            embed.set_field_at(
                index,
                name="Entries",
                value=str(entry_count),
                inline=True
            )

            break

    return embed


def close_giveaway_embed(
    embed: discord.Embed,
    winners: list[discord.User | discord.Member]
) -> discord.Embed:

    # Change description
    embed.description = (
        "This giveaway has now concluded."
    )

    # Preserve final entry count
    entries_value = "0"

    for field in embed.fields:

        if field.name == "Entries":

            entries_value = field.value
            break

    # Remove existing fields
    embed.clear_fields()

    # Final entry count
    embed.add_field(
        name="Entries",
        value=entries_value,
        inline=True
    )

    # Winners
    if winners:

        winner_text = "\n".join(
            f"{index}. {user.mention}"
            for index, user in enumerate(
                winners,
                start=1
            )
        )

    else:

        winner_text = (
            "No winners — nobody entered."
        )

    embed.add_field(
        name="🏆 Winners",
        value=winner_text,
        inline=False
    )

    embed.set_footer(
        text="Giveaway Closed"
    )

    return embed


def create_closed_view() -> discord.ui.View:

    view = discord.ui.View(
        timeout=None
    )

    button = discord.ui.Button(
        label="Closed",
        emoji="🔒",
        style=discord.ButtonStyle.secondary,
        disabled=True
    )

    view.add_item(
        button
    )

    return view