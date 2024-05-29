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
    Sends this help message
    """

    def __init__(self, bot):
        self.bot = bot


    @discord.slash_command()
    @discord.option("module", description="Get info on a particular command.", required=False)
    async def help(self, ctx: discord.ApplicationContext, module: str):
        """Shows all modules of that bot"""

        # checks if cog parameter was given
        # if not: sending all modules and commands not associated with a cog
        if module is None:
            # starting to build embed
            emb = discord.Embed(title='Commands and modules', color=discord.Color.blue(),
                                description=f'Use `/help <module>` to gain more information about that module '
                                            f':smiley:\n')

            # iterating trough cogs, gathering descriptions
            cogs_desc = ''
            for cog in self.bot.cogs:
                if(cog != "Admin"):
                    cogs_desc += f'`{cog}` {self.bot.cogs[cog].__doc__}\n'

            # adding 'list' of cogs to embed
            emb.add_field(name='Modules', value=cogs_desc, inline=False)

            # integrating trough uncategorized commands
            commands_desc = ''
            for command in self.bot.walk_application_commands():
                # if cog not in a cog
                # listing command if cog name is None and command isn't hidden
                if not command.cog:
                    commands_desc += f'{command.name} - {command.help}\n'

            # adding those commands to embed
            if commands_desc:
                emb.add_field(name='Not belonging to a module', value=commands_desc, inline=False)


        else:
            # iterating trough cogs
            for cog in self.bot.cogs:
                # check if cog is the matching one
                if cog.lower() == module.lower() and module.lower() != "admin":

                    # making title - getting description from doc-string below class
                    emb = discord.Embed(title=f'{cog} - Commands', description=self.bot.cogs[cog].__doc__,
                                        color=discord.Color.green())

                    # getting commands from cog
                    for command in self.bot.get_cog(cog).get_commands():
                        # if cog is not hidden
                        if not command.hidden:
                            emb.add_field(name=f"`/{command.name}`", value=command.help, inline=False)
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