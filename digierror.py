import discord
from discord.ext import commands
import digiformatter as df

SUCCESS = "success"
USER_NOT_FOUND = "unf"
CHANGE_VALUE_IS_ZERO = "cvi0"
CHANGE_VALUE_IS_ONE = "cvi1"
CHANGE_METHOD_INVALID = "cmi"

async def throw(ctx, code, delete = 0):
    if code == SUCCESS:
        return
    if code == USER_NOT_FOUND:
        df.warn(f"User {ctx.message.author.id} not found.")
        await ctx.send("""Sorry! You aren't registered with SizeBot.
To register, use the `&register` command.""", delete_after = delete)
    if code == CHANGE_VALUE_IS_ZERO:
        df.warn(f"User {ctx.message.author.id} tried to change by zero.")
        await ctx.send("""Nice try.
You can't change by zero. :stuck_out_tounge:""", delete_after = delete)
    if code == CHANGE_VALUE_IS_ONE:
        df.warn(f"User {ctx.message.author.id} tried to change by one.")
        await ctx.send("""You can't change by one.
This is because changing by one doesn't change the value of your attribute, and especially with slowchange tasks, this clogs up SizeBot's memory.""", delete_after = delete)
    if code == CHANGE_METHOD_INVALID:
        df.warn(f"User {ctx.message.author.id} tried to use an invalid changing method.")
        await ctx.send("""Your change method is invalid. Valid methods are add, subtract, multiply, or divide (and aliases for these modes.)""", delete_after = delete)
