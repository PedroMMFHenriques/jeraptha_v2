import discord
from discord.ext import commands

"""@bot.slash_command(name="help", description="Get info about the commands.")
@discord.option("command", description="Get info on a particular command.", choices=[x.name for x in bot.commands], required=False)
async def help(ctx: discord.ApplicationContext, command: str):
    help_embed = discord.Embed(title="Commands Info") 
    command_names_list = [x.name for x in bot.commands]
    if not command:
        help_embed.add_field(
            name="List of supported commands:",
            value="\n".join([". /"+x.name for _,x in enumerate(bot.commands)]),
            inline=False
        )
        help_embed.add_field(
        name="Details",
        value="Type `/help <command name>` for more details about each command.",
        inline=False
    )

    elif command in command_names_list:
        help_embed.add_field(
        name=command,
        value=bot.get_command(command).description
    )
    else:
        help_embed.add_field(
        name="Oh, no!",
        value="I didn't find command :("
    )
    await ctx.respond(embed=help_embed, ephemeral=True)"""

class Help(commands.Cog):
    """
    Displays help message.
    """

    def __init__(self, bot):
        self.bot = bot


    @discord.slash_command(name="help", description="Shows all modules and commands.")
    @discord.option("module", description="Get info on a particular command.", required=False)
    async def help(self, ctx: discord.ApplicationContext, module: str):
        # General Command
        if module is None:
            # starting to build embed
            emb = discord.Embed(title='All Modules', color=0x009900,
                                description=f'Use `/help <module>` to get more information about a particular module.')

            # iterating through cogs
            for cog in self.bot.cogs:
                if(cog != "Admin"):
                    emb.add_field(name=f'`{cog}`', value=f'{self.bot.cogs[cog].__doc__}\n', inline=False)
 

            # itegrating through uncategorized commands
            commands_desc = ''
            for command in self.bot.walk_application_commands():
                # if cog not in a cog
                # listing command if cog name is None and command isn't hidden
                if not command.cog:
                    commands_desc += f'{command.name} - {command.help}\n'

            # adding those commands to embed
            if commands_desc:
                emb.add_field(name='Not belonging to a module:', value=commands_desc, inline=False)


        else: # Particular command
            # iterating through cogs
            for cog in self.bot.cogs:
                # check if cog is the matching one
                if cog.lower() == module.lower() and module.lower() != "admin":

                    # making title - getting description from doc-string below class
                    emb = discord.Embed(title=f'{cog} Commands', description=self.bot.cogs[cog].__doc__,
                                        color=0x009900)

                    # getting commands from cog
                    for command in self.bot.get_cog(cog).walk_commands():
                        # if cog is not hidden
                        extra_field = ""
                        if(command.parent is not None):
                            extra_field = command.parent.name + " "
                        emb.add_field(name=f"`/{extra_field}{command.name}`", value=command.description, inline=False)
                    # found cog - breaking loop
                    break

            # if module not found
            # yes, for-loops have an else statement, it's called when no 'break' was issued
            else:
                emb = discord.Embed(title="What's that?!",
                                    description=f"I've never heard from a module called `{module[0]}` before :scream:",
                                    color=discord.Color.orange())


        await ctx.respond(embed=emb, ephemeral=True)


def setup(bot):
    bot.add_cog(Help(bot))