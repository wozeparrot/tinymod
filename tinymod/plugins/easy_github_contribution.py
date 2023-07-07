from hata import Client, Guild, InteractionEvent, Message, Role
from hata.ext.slash import Button, Row, ButtonStyle
from github import Github, Auth

import os

TinyMod: Client
GUILD: Guild

CHANNEL_ID = 1069254062131920966
ADMIN_ROLE = Role.precreate(1068980562477465670)
ROLE = Role.precreate(1068980606672850944)
GITHUB = Github(auth=Auth.Token(os.environ["GH_TOKEN"]))

ACCEPT_BUTTON = Button("Accept", custom_id="egc.accept", style=ButtonStyle.green)
DENY_BUTTON = Button("Deny", custom_id="egc.deny", style=ButtonStyle.red)
COMPONENTS = Row(ACCEPT_BUTTON, DENY_BUTTON)

@TinyMod.events
async def message_create(client: Client, message: Message):
  # check channel id
  if message.channel.id != CHANNEL_ID: return
  # check if message is from bot
  if message.author.bot: return

  # quick returns for messages that don't need to be manually checked
  # check if the user already has the role
  if message.author.has_role(ROLE):
    return await client.message_delete(message)
  # check if the message is a link to a pr
  if not (message.content.startswith("https://github.com/tinygrad/tinygrad/") or message.content.startswith("http://github.com/tinygrad/tinygrad/")):
    return await client.message_delete(message)
  # check if the pr is merged
  if not GITHUB.get_repo("tinygrad/tinygrad").get_pull(int(message.content.split("/")[-1])).merged:
    # send a direct message to the user
    dm_channel = await client.channel_private_create(message.author)
    await client.message_create(dm_channel, "Your PR is not merged yet. Please wait for it to be merged before posting it.")
    return await client.message_delete(message)

  # reply with the components for admins to accept or deny
  await client.message_create(message, "", allowed_mentions="!replied_user", components=COMPONENTS)

@TinyMod.interactions(custom_id="egc.accept")
async def egc_accept(client: Client, event: InteractionEvent):
  # ensure that user clicking the button is an admin
  if not event.user.has_role(ADMIN_ROLE): return

  # give user role
  await client.user_role_add(event.user, ROLE)

  # cleanup
  await client.message_delete(event.message.referenced_message)
  await client.interaction_component_acknowledge(event)
  await client.interaction_response_message_delete(event)

@TinyMod.interactions(custom_id="egc.deny")
async def egc_deny(client: Client, event: InteractionEvent):
  # cleanup
  await client.message_delete(event.message.referenced_message)
  await client.interaction_component_acknowledge(event)
  await client.interaction_response_message_delete(event)
