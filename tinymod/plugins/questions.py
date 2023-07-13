from hata import Client, Guild, User

TinyMod: Client
GUILD: Guild

@TinyMod.interactions(guild=GUILD)
async def question(user: User):
  """Recommends reading How To Ask Questions The Smart Way to a user."""
  return f"Hello {user:m}, I would recommend reading: [How To Ask Questions The Smart Way](http://www.catb.org/~esr/faqs/smart-questions.html)."
