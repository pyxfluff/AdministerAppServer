# pyxfluff 2025

import il
import re
import discord
from discord.ext import commands

bot = commands.Bot(intents=discord.Intents.all())

# TODO: Temp variables while I don't; have direct DB access


@bot.slash_command(name="create-release", description="Creates a new release.")
async def new_release(ctx, name: str, latest: bool, distributed_with: str, changelogs: str):
    # Tests
    if not re.search(r"^\d+\.\d+\.\d+(-rc\d+|-beta\d+|-git)?$", name):
        await ctx.respond(":x: The provided version is invalid (does not follow x.x.x-x(git, rc, beta) format)")

    await ctx.respond(f"\n- {name}\n- {latest}\n- {distributed_with}\n- {changelogs}")


@bot.event
async def on_connect():
    if bot.auto_sync_commands:
        await bot.sync_commands()

    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"for new administer versions"
        ), status = discord.Status.idle
    )

    il.cprint("[✓] Versioning bot connected!", 32)

@bot.event
async def on_error(loc):
    il.cprint(f"[x] In version bot thread {loc}: {""}", 32)

# REPLACE BEFORE PUSHING
# bot.run(db.get("VERSION_BOT", db.SECRETS))
