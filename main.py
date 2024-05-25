import os

import discord
import openai
from discord.ext import commands
from discord.utils import get
from pytube import YouTube

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.reactions = True

openai.api_key = os.environ['OPENAI_KEY']

bot = commands.Bot(command_prefix='<', intents=intents)

ffmpeg_executable = 'ffmpeg'

@bot.event
async def on_raw_reaction_add(payload):
    channel_id = payload.channel_id
    if channel_id == 926500132130791462:
        guild = bot.get_guild(payload.guild_id)
        if guild is not None:
            member = guild.get_member(payload.user_id)
            if member is not None:
                role = get(guild.roles, name="KeinOG-Member")

                if role is None:
                    print("Role 'KeinOG-Member' not found.")
                    return
                try:
                    await member.add_roles(role)
                    print(f"Added role 'KeinOG-Member' to {member.display_name}.")
                except discord.Forbidden:
                    print("I don't have permission to assign that role.")
                except discord.HTTPException as e:
                    print(f"Error occurred while assigning the role: {e}")
            else:
                print("Member not found in the guild.")
        else:
            print("Guild not found.")

@bot.command(name='join', help='Joins the voice channel you are currently in.')
async def join(ctx):
    if ctx.author.voice is None:
        await ctx.send("You are not connected to a voice channel.")
        return
    channel = ctx.author.voice.channel
    await channel.connect()

@bot.command(name='leave', help='Leaves the current voice channel.')
async def leave(ctx):
    if ctx.voice_client is not None:
        await ctx.voice_client.disconnect()

@bot.command(name='play', help='Plays audio from a YouTube URL.')
async def play(ctx, url):
    if ctx.voice_client is None:
        await ctx.send("I am not connected to a voice channel.")
        return

    try:
        yt = YouTube(url)
        stream = yt.streams.filter(only_audio=True).first()
        await ctx.send(f"Now playing: {yt.title}")

        filename = f"{yt.title}.mp3"
        if stream is not None:
            stream.download(output_path="audio", filename=filename)
        source = discord.FFmpegPCMAudio(executable=ffmpeg_executable, source=f"audio/{filename}")

        ctx.voice_client.play(source, after=lambda e: print(f'Player error: {e}') if e else None)
    except Exception as e:
        await ctx.send(f"Process Failed: {e}")

@bot.command(name='stop', help='Stops the current audio playback.')
async def stop(ctx):
    if ctx.voice_client is not None:
        ctx.voice_client.stop()
        await ctx.send("Playback stopped.")

@bot.command(name='kick', help='Kicks a member from the server.')
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    if reason is None:
        reason = "No reason provided."
    try:
        await member.kick(reason=reason)
        await ctx.send(f'User {member.mention} has been kicked for: {reason}')
    except discord.Forbidden:
        await ctx.send(f'I do not have permission to kick {member.mention}')
    except discord.HTTPException:
        await ctx.send('Kicking failed')

async def kick_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Please mention the member to kick.')
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send('Member not found.')
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send('You do not have permission to kick members.')
    else:
        await ctx.send('An error occurred while kicking the member.')

@bot.command(name='role', help='Adds a role to a member.')
@commands.has_permissions(manage_roles=True)
async def role(ctx, member: discord.Member, role_name: str):
    guild = ctx.guild
    role = get(guild.roles, name=role_name)

    if role is None:
        await ctx.send(f"Role '{role_name}' not found.")
        return

    try:
        await member.add_roles(role)
        await ctx.send(f"Role '{role.name}' has been added to {member.mention}!")
    except discord.Forbidden:
        await ctx.send("I don't have permission to assign that role.")
    except discord.HTTPException as e:
        await ctx.send(f"Error occurred while assigning the role: {e}")

@bot.command(name='remRole', help='Removes a role from a member.')
@commands.has_permissions(manage_roles=True)
async def remRole(ctx, member: discord.Member, role_name: str):
    guild = ctx.guild
    role = get(guild.roles, name=role_name)

    if role is None:
        await ctx.send(f"Role '{role_name}' not found.")
        return

    try:
        await member.remove_roles(role)
        await ctx.send(f"Role '{role.name}' has been removed from {member.mention}!")
    except discord.Forbidden:
        await ctx.send("I don't have permission to remove that role.")
    except discord.HTTPException as e:
        await ctx.send(f"Error occurred while removing the role: {e}")

token = os.getenv('DISCORD_TOKEN')
if not token:
    raise ValueError("No DISCORD_TOKEN environment variable found")

bot.run(token)
