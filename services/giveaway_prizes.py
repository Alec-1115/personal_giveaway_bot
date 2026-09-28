import discord


async def give_role_prize(
    member: discord.Member,
    role: discord.Role
) -> bool:

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