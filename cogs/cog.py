import os


async def setup(bot):
    for root, _, files in os.walk("cogs"):
        for file in files:
            if not file.endswith(".py"):
                continue

            if file in {"cog.py", "__init__.py"}:
                continue

            path = os.path.join(root, file)

            extension = path[:-3].replace(os.sep, ".")

            await bot.load_extension(extension)