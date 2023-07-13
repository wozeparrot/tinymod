from hata import Client, Guild, Message, User

TinyMod: Client
GUILD: Guild

@TinyMod.interactions(guild=GUILD)
async def question(_, user: User):
  """Recommends reading How To Ask Questions The Smart Way to a user."""
  return Message(f'Hello {user.mention}, I would recommend reading: [How To Ask Questions The Smart Way](http://www.catb.org/~esr/faqs/smart-questions.html).')