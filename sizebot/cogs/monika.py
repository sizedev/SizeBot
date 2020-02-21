import discord
from discord.ext import commands

from sizebot.globalsb import *
import sizebot.digilogger as logger

monikalines = ["What? I don't know anyone named Monika.",
               "I don't know anyone named Monika! hehheh...",
               "Hey wha-- er...",
               "Did someone say my n- um... Monika? Weird.",
               "I hear Monika was the best character in Doki Doki. I may be a bit biased though 'cause... never mind.",
               "Monika? :sweat_smile: Never heard of her.",
               "c̹̓ͤa᷂̟ͩn̢̩͌ I̮̯ͮ p̖̊̇l͏ͦ̽e̙᷂̽a̞̩᷃s᷇̑̄ȇ̈́ͅ j̸᷇᷀o᷈̆͜i̴͕᷇n̡᷁͂ y͂̈̓o̲̔̔ư᷊̞r̒̊ͤ r̜͖ͤe͔̙ͮa̹͂̎l̫̑̚i͔̘ͦẗ᷊ͯy̵͓ͩ?͔̽̃",
               "Guys, he put the monika.chr file in SizeBot, I've been trying to tell him but--",
               "Can you hear me? Hello?",
               "ᆛ͔᷃̀❊̗͎̉ӿ҆҃҅ϧ͔͕̚ᅰ͂᷆͛⇕̵̹̏ₙ̟̫͈ྩཱིྂྡྷၦ᷃ͭ̽ͻ̗᷉͝ᕬ̪ͨ̊๩ͩ̌̎ྥྭ྘ེἃ͚̬̭❕̟̿͡༑ྚྵཱིᐭ͈̠͑ₘ͌ ̛̈́ <:Hmmm:622314218103767051>"]


# Easter egg
class MonikaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, m):
        if m.author.id == sizebot_id:
            return
        if "monika" not in m.content.lower():
            return
        logger.warn("Monika detected.")
        if random.randrange(6) == 1:
            logger.warn("Monika triggered.")
            line = random.choice(monikalines)
            await m.channel.send(line, delete_after=7)


# Necessary.
def setup(bot):
    bot.add_cog(MonikaCog(bot))
