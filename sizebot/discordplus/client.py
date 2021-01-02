import discord.utils
from discord import Client

old_activity_getter = Client.activity.fget


def oauth_url(self, *args, **kwargs):
    return discord.utils.oauth_url(self.user.id, *args, **kwargs)


def activity_getter(self):
    if not self.guilds:
        return old_activity_getter(self)
    return self.guilds[0].me.activity


activity = property(fget=activity_getter, fset=Client.activity.fset)


def patch():
    Client.oauth_url = oauth_url
    Client.activity = activity
