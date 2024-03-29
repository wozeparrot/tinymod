from hata import Client, Guild, InteractionEvent, Message, Role, Emoji
from hata.ext.slash import Button, Row, ButtonStyle
from github import Github, Auth

import os, re, logging

TinyMod: Client
GUILD: Guild
ADMIN_ROLE: Role

CHANNEL_ID = 1069254062131920966
ROLE = Role.precreate(1068980606672850944)
GITHUB = Github(auth=Auth.Token(os.environ["GH_TOKEN"]))
ACCEPT_EMOJI = Emoji.precreate(1127803062455648316)
DENY_EMOJI = Emoji.precreate(1128032112486912190)

ACCEPT_BUTTON = Button("Accept", emoji=ACCEPT_EMOJI, custom_id="egc.accept", style=ButtonStyle.green)
DENY_BUTTON = Button("Deny", emoji=DENY_EMOJI, custom_id="egc.deny", style=ButtonStyle.red)
COMPONENTS = Row(ACCEPT_BUTTON, DENY_BUTTON)

@TinyMod.events # type: ignore
async def message_create(client: Client, message: Message):
  # check channel id
  if message.channel.id != CHANNEL_ID: return
  # check if message is from a bot
  if message.author.bot: return

  # quick returns for messages that don't need to be manually checked
  if message.content is None: return await client.message_delete(message)
  # check if the message is a link to something in the tinygrad repo
  if not ("https://github.com/tinygrad/tinygrad/" in message.content or "http://github.com/tinygrad/tinygrad/" in message.content):
    return await client.message_delete(message)

  logging.info(f"Handling potential contributor {message.author} with message {message.content}")

  dm_channel = await client.channel_private_create(message.author)

  # check if the user already has the role
  if message.author.has_role(ROLE):
    logging.info(f"{message.author} already has the contributor role.")
    await client.message_create(dm_channel, "You already have the contributor role.")
    return await client.message_delete(message)

  # check if the link is to a pr
  if "/pull/" in message.content:
    # get pr number
    pr_number = re.search(r"/pull/(\d+)", message.content)
    logging.info(f"PR number: {pr_number}")
    if pr_number is None:
      # send a direct message to the user
      await client.message_create(dm_channel, "Please post the link to the PR instead.")
      return await client.message_delete(message)
    # check if the pr is merged
    if not GITHUB.get_repo("tinygrad/tinygrad").get_pull(int(pr_number.group(1))).merged:
      logging.info(f"PR {pr_number.group(1)} is not merged.")
      # send a direct message to the user
      await client.message_create(dm_channel, "Your PR is not merged yet. Please wait for it to be merged before posting it.")
      return await client.message_delete(message)
  # check if the link is a merge commit
  elif "/commit/" in message.content:
    # try to pull out the pr number from the commit message
    commit_message = GITHUB.get_repo("tinygrad/tinygrad").get_commit(message.content.split("/")[-1]).commit.message
    pr_number = re.search(r"#(\d+)", commit_message)
    logging.info(f"PR number: {pr_number}")
    # check if the pr number was found
    if pr_number is None:
      # send a direct message to the user
      await client.message_create(dm_channel, "Please post the link to the PR instead.")
      return await client.message_delete(message)
    # check if the pr is merged
    if not GITHUB.get_repo("tinygrad/tinygrad").get_pull(int(pr_number.group(1))).merged:
      logging.info(f"PR {pr_number.group(1)} is not merged.")
      # send a direct message to the user
      await client.message_create(dm_channel, "Your PR is not merged yet. Please wait for it to be merged before posting it.")
      return await client.message_delete(message)
  else:
    logging.info("Link is not a PR or commit.")
    # send a direct message to the user
    await client.message_create(dm_channel, "Please post the link to the PR instead.")
    return await client.message_delete(message)

  logging.info(f"User {message.author} has a valid PR. Waiting for admin approval.")

  # reply with the components for admins to accept or deny
  await client.message_create(message, "", allowed_mentions=("!replied_user",), components=COMPONENTS)

@TinyMod.interactions(custom_id="egc.accept") # type: ignore
async def egc_accept(client: Client, event: InteractionEvent):
  # ensure that user clicking the button is an admin
  if not event.user.has_role(ADMIN_ROLE): return

  logging.info(f"Accepting request from {event.message.referenced_message.author}")

  # give user role
  await client.user_role_add(event.message.referenced_message.author, ROLE)

  # dm the user that their request was accepted
  dm_channel = await client.channel_private_create(event.message.referenced_message.author)
  await client.message_create(dm_channel, "You're now a purple!")

  # cleanup
  await client.message_delete(event.message.referenced_message)
  await client.interaction_component_acknowledge(event)
  await client.interaction_response_message_delete(event)

@TinyMod.interactions(custom_id="egc.deny") # type: ignore
async def egc_deny(client: Client, event: InteractionEvent):
  # ensure that user clicking the button is an admin
  if not event.user.has_role(ADMIN_ROLE): return

  logging.info(f"Denying request from {event.message.referenced_message.author}")

  # cleanup
  await client.message_delete(event.message.referenced_message)
  await client.interaction_component_acknowledge(event)
  await client.interaction_response_message_delete(event)
