import os

import discord
from discord import ui
from discord.ext import commands
from discord.utils import get

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.reactions = True

bot = commands.Bot(command_prefix='<', intents=intents)

class RoleButton(ui.Button):
    def __init__(self, role):
        super().__init__(label="Get KeinOG-Member Role", style=discord.ButtonStyle.primary)
        self.role = role

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        member = interaction.user

        if guild is None:
            await interaction.response.send_message("Guild is None", ephemeral=True)
            return

        if member is None:
            await interaction.response.send_message("Member is None", ephemeral=True)
            return

        role = discord.utils.get(guild.roles, name=self.role)

        if role is None:
            await interaction.response.send_message(f"Role '{self.role}' not found or you don't have permission to assign this role.", ephemeral=True)
            return

        if not isinstance(member, discord.Member):
            await interaction.response.send_message("Cannot add role to a non-Member user", ephemeral=True)
            return

        try:
            await member.add_roles(role)
            await interaction.response.send_message(f"Role {role.name} has been added to you!", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to assign that role.", ephemeral=True)
        except discord.HTTPException:
            await interaction.response.send_message("Error occurred while assigning the role.", ephemeral=True)

class RoleView(ui.View):
    def __init__(self, role):
        super().__init__()
        self.add_item(RoleButton(role))


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
              await member.add_roles(role)
              print(f"Added role 'KeinOG-Member' to {member.display_name}.")
          else:
              print("Member not found in the guild.")
      else:
          print("Guild not found.")
          
@bot.command(name='kick')
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
    
token = os.getenv('DISCORD_TOKEN')
if not token:
    raise ValueError("No DISCORD_TOKEN environment variable found")

bot.run(token)