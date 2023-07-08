from hata import Client, ClientUserBase, Guild, GuildProfile, Message
from hata.ext import asyncio
import aiosqlite

import json, uuid, time

TinyMod: Client
GUILD: Guild

DATABASE = "tinymod.db"

# ensure that the tables are setup
async def setup(_):
  async with aiosqlite.connect(DATABASE) as db:
    await db.execute("CREATE TABLE IF NOT EXISTS logging_messages (id TEXT PRIMARY KEY, timestamp INTEGER, channel_id INTEGER, user_id INTEGER, username TEXT, action TEXT, content TEXT, json TEXT)")
    await db.execute("CREATE TABLE IF NOT EXISTS logging_members (id TEXT PRIMARY KEY, timestamp INTEGER, user_id INTEGER, username TEXT, json TEXT)")
    await db.commit()

# message logging
async def log_message(action: str, message: Message):
  if message.author.bot: return
  async with aiosqlite.connect(DATABASE) as db:
    await db.execute("INSERT INTO logging_messages (id, timestamp, channel_id, user_id, username, action, content, json) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (str(uuid.uuid4()), time.monotonic(), message.channel.id, message.author.id, message.author.full_name, action, message.content, json.dumps(message.to_data(include_internals=True))))
    await db.commit()

@TinyMod.events
async def message_create(client: Client, message: Message): await log_message("create", message)

@TinyMod.events
async def message_update(client: Client, message: Message, _): await log_message("update", message)

@TinyMod.events
async def message_delete(client: Client, message: Message): await log_message("delete", message)

# member logging
@TinyMod.events
async def guild_user_edit(client: Client, guild: Guild, user: ClientUserBase, _):
  profile: GuildProfile | None = user.get_guild_profile_for(guild)
  if profile is None: return
  async with aiosqlite.connect(DATABASE) as db:
    await db.execute("INSERT INTO logging_members (id, timestamp, user_id, username, json) VALUES (?, ?, ?, ?, ?)", (str(uuid.uuid4()), time.monotonic(), user.id, user.full_name, json.dumps(profile.to_data(include_internals=True))))
    await db.commit()
