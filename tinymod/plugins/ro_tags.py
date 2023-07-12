from hata import Client, Guild

import os, pathlib

from hata.ext.slash import abort

TinyMod: Client
GUILD: Guild

# load all tags from the tags folder
TAGS = {}
for file in (pathlib.Path(__file__).parent.parent.parent / "assets/ro_tags/").iterdir():
  TAGS[file.stem] = file.read_text()
TAG_NAMES = list(TAGS)

@TinyMod.interactions(guild=GUILD)
async def tags(tag: ("str", "Tag to send")):
  """Sends a short snippet of information."""
  if tag not in TAGS: abort(f"Tag `{tag}` not found.")
  return TAGS[tag]

@tags.autocomplete("tag")
async def tags_autocomplete(value):
  if value is None: return TAG_NAMES[:25]
  return [tag for tag in TAG_NAMES if tag.startswith(value.casefold())]
