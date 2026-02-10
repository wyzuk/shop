import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import time as pytime
import random
import os
from dotenv import load_dotenv

# Load environment variables (for Archcraft local testing)
load_dotenv()
TOKEN = os.getenv("TOKEN")

# Setup intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="+", intents=intents)

# Storage for /revive
offer_dashboard = {}
offer_counter = 1

# --- BACKGROUND TASK: Live Status ---
@tasks.loop(minutes=10)
async def change_status():
    # Dynamic population count
    people = random.randint(8350, 8420) 
    await bot.change_presence(activity=discord.Game(name=f"Serving {people} people"))

@bot.event
async def on_ready():
    await bot.tree.sync()
    if not change_status.is_running():
        change_status.start()
    print(f"✅ Manager Cluster is live for Jamim.")

# --- HELPER: Emoji Fetcher ---
def get_emoji(name):
    # Searches your server for the emoji by name
    emoji = discord.utils.get(bot.emojis, name=name)
    return str(emoji) if emoji else f":{name}:"

# --- SLASH COMMANDS ---

@bot.tree.command(name="ofc", description="Create a new shop offer")
@app_commands.describe(name="Service (e.g. Crunchyroll)", price="Price", duration="Duration", expiry_time="Time (1h, 2d, 30m)")
async def ofc(interaction: discord.Interaction, name: str, price: str, duration: str, expiry_time: str):
    global offer_counter
    
    offer_id = str(offer_counter).zfill(2)
    offer_counter += 1

    # Time Parsing
    seconds = 0
    unit = expiry_time[-1].lower()
    try:
        amount = int(expiry_time[:-1])
        if unit == 'h': seconds = amount * 3600
        elif unit == 'm': seconds = amount * 60
        elif unit == 'd': seconds = amount * 86400
    except ValueError:
        await interaction.response.send_message("Invalid time format! Use 1h, 30m, etc.", ephemeral=True)
        return
    
    future_unix = int(pytime.time() + seconds)
    countdown_text = f"⌛ Offer available for: <t:{future_unix}:R>"
    ticket_link = "https://discord.com/channels/1375331809365327933/1393990894797193256"

    # Modern Text UI
    offer_content = (
        f"# {name} Offer {get_emoji('crunchyroll')}\n"
        f"-# Offer No: {offer_id}\n"
        f"> {duration} {name} = **{price}**\n\n"
        f"{countdown_text}\n"
        f"🎫 Create ticket at: {ticket_link}\n"
        f"- Accepts {get_emoji('LTC')} {get_emoji('bkash')}\n"
        f"@everyone @here"
    )

    await interaction.response.send_message("✨ Dispatching Offer...", ephemeral=True)
    msg = await interaction.channel.send(offer_content)
    
    # Save to "Dashboard"
    offer_dashboard[offer_id] = offer_content

    # Expiration Logic (The "Cutting" effect)
    if seconds > 0:
        await asyncio.sleep(seconds)
        # Apply strikethrough to the service line
        expired_line = f"~~{duration} {name} = {price}~~"
        
        expired_content = (
            f"# {name} Offer {get_emoji('crunchyroll')}\n"
            f"-# Offer No: {offer_id}\n"
            f"> {expired_line}\n\n"
            f"❌ **OFFER EXPIRED**\n"
            f"🎫 Create ticket at: {ticket_link}\n"
            f"- Accepts {get_emoji('LTC')} {get_emoji('bkash')}"
        )
        await msg.edit(content=expired_content)

@bot.tree.command(name="revive", description="Revive an old offer by ID")
async def revive(interaction: discord.Interaction, offer_no: str):
    oid = offer_no.zfill(2)
    if oid in offer_dashboard:
        await interaction.response.send_message("🔄 Reviving...", ephemeral=True)
        await interaction.channel.send(offer_dashboard[oid])
    else:
        await interaction.response.send_message("❌ ID not found in current session.", ephemeral=True)

# --- PREFIX MODERATION (No DM / No Reason) ---

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member):
    await member.ban()
    await ctx.send(f"🔨 **{member.display_name}** banned.")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member):
    await member.kick()
    await ctx.send(f"👢 **{member.display_name}** kicked.")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def mute(ctx, member: discord.Member):
    role = discord.utils.get(ctx.guild.roles, name="Muted")
    if role:
        await member.add_roles(role)
        await ctx.send(f"🔇 **{member.display_name}** muted.")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, member: discord.Member):
    role = discord.utils.get(ctx.guild.roles, name="Muted")
    if role:
        await member.remove_roles(role)
        await ctx.send(f"🔊 **{member.display_name}** unmuted.")

bot.run(TOKEN)
