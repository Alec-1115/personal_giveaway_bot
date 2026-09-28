import discord


async def send_entry_dm(
    user: discord.User | discord.Member,
    giveaway_name: str,
    reward_name: str,
    winners: int,
    giveaway_link: str
):

    try:

        await user.send(
            f"🎉 You entered the **{giveaway_name}** giveaway!\n\n"
            f"**Prize:** {reward_name}\n"
            f"**Winners:** {winners}\n\n"
            f"[View giveaway]({giveaway_link})"
        )

    except discord.Forbidden:
        pass


async def send_winner_dm(
    user: discord.User | discord.Member,
    giveaway_name: str,
    reward_name: str
):

    try:

        await user.send(
            f"🎉 **Congratulations!**\n\n"
            f"You won the **{giveaway_name}** giveaway!\n\n"
            f"**Prize:** {reward_name}"
        )

    except discord.Forbidden:
        pass


async def send_redeemable_dm(
    user: discord.User | discord.Member,
    giveaway_name: str,
    reward_name: str,
    link: str
):

    try:

        await user.send(
            f"🎉 **Congratulations!**\n\n"
            f"You won the **{giveaway_name}** giveaway!\n\n"
            f"**Prize:** {reward_name}\n\n"
            f"**Your redeemable link:**\n"
            f"{link}"
        )

        return True

    except discord.Forbidden:
        return False

    except discord.HTTPException:
        return False