import discord
from discord import Object


def Snowflake(id):
    return Object(id=id)


def patch():
    discord.Snowflake = Snowflake
