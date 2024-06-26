import asyncio
import os

import discord
import spotipy
from discord.ext import commands
from discord.utils import get
from pytube import Search, YouTube
from spotipy.oauth2 import SpotifyClientCredentials

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.reactions = True

bot = commands.Bot(command_prefix='<', intents=intents)

ffmpeg_executable = 'ffmpeg'
audio_output_dir = 'spotAudio'
goofy_audios_dir = 'goofyAudios'

SPOTIPY_CLIENT_ID = os.environ['SPOTIFY_CLIENT_ID']
SPOTIPY_CLIENT_SECRET = os.environ['SPOTIFY_CLIENT_SECRET']

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET
))
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

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
@bot.event
async def kick_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Please mention the member to kick.')
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send('Member not found.')
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send('You do not have permission to kick members.')
    else:
        await ctx.send('An error occurred while kicking the member.')
@bot.event
async def ban_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Please mention the member to ban.')
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send('Member not found.')
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send('You do not have permission to ban members.')
    else:
        await ctx.send('An error occurred while banning the member')
@bot.command(name='join', help='Joins the voice channel you are currently in.')
async def _join(ctx):
    if ctx.author.voice is None:
        await ctx.send("You are not connected to a voice channel.")
        return
    channel = ctx.author.voice.channel
    await channel.connect()

@bot.command(name='leave', help='Leaves the current voice channel.')
async def _leave(ctx):
    if ctx.voice_client is not None:
        await ctx.voice_client.disconnect()

@bot.command(name='play', help='Plays audio from a YouTube or Spotify URL.')
async def _play(ctx, url):
    if ctx.voice_client is None:
        await ctx.send("I am not connected to a voice channel.")
        return

    if 'youtube.com' in url or 'youtu.be' in url:
        try:
            yt = YouTube(url)
            stream = yt.streams.filter(only_audio=True).first()
            await ctx.send(f"Now playing: {yt.title}")

            filename = f"{yt.title}.mp3"
            filepath = os.path.join(audio_output_dir, filename)
            if stream is not None:
                stream.download(output_path=audio_output_dir, filename=filename)
            source = discord.FFmpegPCMAudio(executable=ffmpeg_executable, source=filepath)

            ctx.voice_client.play(source, after=lambda e: print(f'Player error: {e}') if e else None)
        except Exception as e:
            await ctx.send(f"Process Failed: {e}")
    elif 'spotify.com' in url:
                try:
                    track_id = url.split('/')[-1].split('?')[0]
                    track = sp.track(track_id)
                    if track is None:
                        await ctx.send("Failed to fetch track details from Spotify.")
                        return

                    track_name = track['name']
                    track_artists = ', '.join(artist['name'] for artist in track['artists'])

                    search_query = f"{track_name} {track_artists}"

                    yt_search = Search(search_query)
                    if yt_search.results:
                        yt_url = f"https://www.youtube.com/watch?v={yt_search.results[0].video_id}"
                        yt = YouTube(yt_url)
                        stream = yt.streams.filter(only_audio=True).first()
                        await ctx.send(f"Now playing: {yt.title}")

                        filename = f"{yt.title}.mp3"
                        filepath = os.path.join(audio_output_dir, filename)
                        if stream is not None:
                            stream.download(output_path=audio_output_dir, filename=filename)
                            source = discord.FFmpegPCMAudio(executable=ffmpeg_executable, source=filepath)

                            if source:
                                ctx.voice_client.play(source, after=lambda e: print(f'Player error: {e}') if e else None)
                            else:
                                await ctx.send("Failed to play audio. Check the provided URL.")
                        else:
                            await ctx.send("Failed to retrieve audio stream.")
                    else:
                        await ctx.send("No matching videos found on YouTube.")
                except Exception as e:
                    error_message = str(e)
                    if len(error_message) > 2000:
                        error_message = error_message[:1997] + '...'
                    await ctx.send(f"Process Failed: {error_message}")


@bot.command(name='stop', help='Stops the current audio playback.')
async def _stop(ctx):
    if ctx.voice_client is not None:
        ctx.voice_client.stop()
        await ctx.send("Playback stopped.")

@bot.command(name='kick', help='Kicks a member from the server.')
@commands.has_permissions(kick_members=True)
async def _kick(ctx, member: discord.Member, *, reason=None):
    if reason is None:
        reason = "No reason provided."
    try:
        await member.kick(reason=reason)
        await ctx.send(f'User {member.mention} has been kicked for: {reason}')
    except discord.Forbidden:
        await ctx.send(f'I do not have permission to kick {member.mention}')
    except discord.HTTPException:
        await ctx.send('Kicking failed')

@bot.command(name='ban', help='Bans a member from the server.')
@commands.has_permissions(ban_members=True)
async def _ban(ctx, member: discord.Member, *, reason=None):
    if member is None:
        await ctx.send("Please specify a member to ban.")
        return
    if member == ctx.message.author:
        await ctx.send("You cannot ban yourself.")
        return
    if member == ctx.guild.owner:
        await ctx.send(f"You cannot ban the server owner {member.mention}.")
        return
        
    if reason is None:
        reason = "No reason provided."
    try:
        await member.ban(reason=reason)
        await ctx.send(f'User {member.mention} has been banned for: {reason}')
    except discord.Forbidden:
        await ctx.send(f'I do not have permission to ban {member.mention}')
    except discord.HTTPException:
        await ctx.send('Banning failed')

@bot.command(name='unban', help='Unbans a member from the server.')
@commands.has_permissions(ban_members=True)
async def _unban(ctx, id: int):
    if id is None:
        await ctx.send("Please provide a valid user.")
        return
    try: 
        user = await bot.fetch_user(id)
        if user is None:
            await ctx.send('User not found.')
            return
        await ctx.guild.unban(user)
        await ctx.send(f"Successfully unbanned {user.name}#{user.discriminator}.")
    except discord.Forbidden:
        await ctx.send('I do not have permission to unban')
    except discord.HTTPException:
        await ctx.send('unbanning failed')
        
@bot.command(name='g_role', help='Adds a role to a member.')
@commands.has_permissions(manage_roles=True)
async def _role(ctx, member: discord.Member, role_name: str):
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

@bot.command(name='r_role', help='Removes a role from a member.')
@commands.has_permissions(manage_roles=True)
async def _remove_role(ctx, member: discord.Member, role_name: str):
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

@bot.command(name='aud1', help='Joins the voice channel, plays a calvin car sound for 9 seconds')
async def _aud1(ctx):
    if ctx.author.voice is None:
        await ctx.send("You are not connected to a voice channel.")
        return

    channel = ctx.author.voice.channel
    voice_client = await channel.connect()

    try:
        song_file = os.path.join(goofy_audios_dir, 'calvinPCwuwuwu.mp3')

        if not os.path.isfile(song_file):
            await ctx.send("The song file 'calvinPCwuwuwu.mp3' was not found in the spotAudio directory.")
            await voice_client.disconnect()
            return

        source = discord.FFmpegPCMAudio(executable=ffmpeg_executable, source=song_file)

        voice_client.play(source)

        await ctx.send("Playing 'calvinPCwuwuwu' for 9 seconds.")

        await asyncio.sleep(9)

        voice_client.stop()
        await ctx.send("Leaving the voice channel.")
        await voice_client.disconnect()
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")
        if voice_client.is_connected():
            await voice_client.disconnect()
            
@bot.command(name='aud2', help='Joins the voice channel, plays a calvin car sound for 2 seconds')
async def _aud2(ctx):
    if ctx.author.voice is None:
        await ctx.send("You are not connected to a voice channel.")
        return

    channel = ctx.author.voice.channel
    voice_client = await channel.connect()

    try:
        song_file = os.path.join(goofy_audios_dir, 'calvinsound2seconds.mp3')

        if not os.path.isfile(song_file):
            await ctx.send("The song file 'calvinsound2seconds.mp3' was not found in the spotAudio directory.")
            await voice_client.disconnect()
            return

        source = discord.FFmpegPCMAudio(executable=ffmpeg_executable, source=song_file)

        voice_client.play(source)

        await ctx.send("Playing 'calvinsound2seconds' for 2 seconds.")

        await asyncio.sleep(2)

        voice_client.stop()
        await ctx.send("Leaving the voice channel.")
        await voice_client.disconnect()
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")
        if voice_client.is_connected():
            await voice_client.disconnect()

token = os.getenv('DISCORD_TOKEN')
if not token:
    raise ValueError("No DISCORD_TOKEN environment variable found")

bot.run(token)