import discord


async def give_role_prize(
    member: discord.Member,
    role: discord.Role
) -> bool:
    """
    Give the giveaway role to the winning member.

    Returns True if the role was successfully added.
    Returns False if Discord rejected the action.
    """

    try:

        await member.add_roles(
            role,
            reason="Giveaway prize"
        )

        return True

    except discord.Forbidden:
        return False

    except discord.HTTPException:
        return False