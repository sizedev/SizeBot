import discord.utils
from discord import Client


def oauth_url(self, *args, **kwargs):
    return discord.utils.oauth_url(self.user.id, *args, **kwargs)


def patch():
    Client.oauth_url = oauth_url
