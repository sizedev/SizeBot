import discord
from discord import Object


def Snowflake(id: int) -> Object:
    return Object(id=id)


def patch():
    discord.Snowflake = Snowflake
