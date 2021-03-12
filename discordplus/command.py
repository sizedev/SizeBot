from discord.ext.commands import Command, Cog
from discord.ext.commands.core import wrap_callback

old_init = Command.__init__
old_short_doc = Command.short_doc


def __init__(self, *args, category=None, multiline=False, **kwargs):
    self.category = category
    self.multiline = multiline
    old_init(self, *args, **kwargs)


async def dispatch_error(self, ctx, error):
    ctx.command_failed = True
    cog = self.cog
    try:
        command_on_error = self.on_error
    except AttributeError:
        command_on_error = None

    handled = False

    if command_on_error is not None:
        wrapped_command_on_error = wrap_callback(command_on_error)

        try:
            if cog is not None:
                await wrapped_command_on_error(cog, ctx, error)
            else:
                await wrapped_command_on_error(ctx, error)
            handled = True
        except Exception as e:
            error = e

    if not handled and cog is None:
        cog_on_error = Cog._get_overridden_method(cog.cog_command_error)
        if cog_on_error is not None:
            wrapped_cog_on_error = wrap_callback(cog_on_error)
            try:
                await wrapped_cog_on_error(ctx, error)
                handled = True
            except Exception as e:
                error = e

    if not handled:
        ctx.bot.dispatch("command_error", ctx, error)


@property
def short_doc(self):
    return old_short_doc.fget(self) or "-"


@property
def alias_string(self):
    aliases = ""
    if self.aliases:
        aliases = "*(" + ", ".join(self.aliases) + ")*"
    return aliases


@property
def name_string(self):
    return f"**{self.name}**"


def patch():
    Command.__init__ = __init__
    Command.dispatch_error = dispatch_error
    Command.short_doc = short_doc
    Command.alias_string = alias_string
    Command.name_string = name_string
