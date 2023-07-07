from hata import Client, Guild, Message
from hata.ext import asyncio
import aiosqlite

import json, uuid

TinyMod: Client
GUILD: Guild

# ensure that the tables are setup
async def setup(_):
  async with aiosqlite.connect("tinymod.db") as db:
    await db.execute("CREATE TABLE IF NOT EXISTS logging_messages (id TEXT PRIMARY KEY, user_id INTEGER, username TEXT, timestamp INTEGER, action TEXT, content TEXT, json TEXT)")
    await db.commit()

# message logging
async def log_message(action: str, message: Message):
  if message.author.bot: return
  async with aiosqlite.connect("tinymod.db") as db:
    await db.execute("INSERT INTO logging_messages (id, user_id, username, timestamp, action, content, json) VALUES (?, ?, ?, ?, ?, ?, ?)", (str(uuid.uuid4()), message.author.id, message.author.full_name, message.created_at.timestamp(), action, message.content, json.dumps(message.to_data(include_internals=True))))
    await db.commit()

@TinyMod.events
async def message_create(client: Client, message: Message): await log_message("create", message)

@TinyMod.events
async def message_update(client: Client, message: Message, _): await log_message("update", message)

@TinyMod.events
async def message_delete(client: Client, message: Message): await log_message("delete", message)
