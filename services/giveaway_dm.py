import discord


async def send_entry_dm(
    user: discord.User | discord.Member,
    giveaway_name: str,
    reward: discord.Role,
    winners: int,
    giveaway_link: str
):

    try:

        await user.send(
            f"🎉 You entered the **{giveaway_name}** giveaway!\n\n"
            f"**Prize:** {reward.name}\n"
            f"**Winners:** {winners}\n\n"
            f"[View giveaway]({giveaway_link})"
        )

    except discord.Forbidden:
        pass


async def send_winner_dm(
    user: discord.User,
    giveaway_name: str,
    reward: discord.Role
):

    try:

        await user.send(
            f"🎉 **Congratulations!**\n\n"
            f"You won the **{giveaway_name}** giveaway!\n\n"
            f"**Prize:** {reward.name}"
        )

    except discord.Forbidden:
        pass