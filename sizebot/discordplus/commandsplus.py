import asyncio
import functools

from discord.ext import commands
from discord.ext.commands.cog import Cog
from discord.ext.commands.errors import CommandError, CommandInvokeError


class Command(commands.Command):
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


def command(name=None, cls=None, **attrs):
    """A decorator that transforms a function into a :class:`.Command`
    or if called with :func:`.group`, :class:`.Group`.
    By default the ``help`` attribute is received automatically from the
    docstring of the function and is cleaned up with the use of
    ``inspect.cleandoc``. If the docstring is ``bytes``, then it is decoded
    into :class:`str` using utf-8 encoding.
    All checks added using the :func:`.check` & co. decorators are added into
    the function. There is no way to supply your own checks through this
    decorator.
    Parameters
    -----------
    name: :class:`str`
        The name to create the command with. By default this uses the
        function name unchanged.
    cls
        The class to construct with. By default this is :class:`.Command`.
        You usually do not change this.
    attrs
        Keyword arguments to pass into the construction of the class denoted
        by ``cls``.
    Raises
    -------
    TypeError
        If the function is not a coroutine or is already a command.
    """
    if cls is None:
        cls = Command

    def decorator(func):
        if isinstance(func, Command):
            raise TypeError('Callback is already a command.')
        return cls(func, name=name, **attrs)

    return decorator


def wrap_callback(coro):
    @functools.wraps(coro)
    async def wrapped(*args, **kwargs):
        try:
            ret = await coro(*args, **kwargs)
        except CommandError:
            raise
        except asyncio.CancelledError:
            return
        except Exception as exc:
            raise CommandInvokeError(exc) from exc
        return ret
    return wrapped
