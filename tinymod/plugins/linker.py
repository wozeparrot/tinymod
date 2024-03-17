from hata import Client, Guild, Role, Message, Embed, Color
from github import Github, Auth

import os, re
from datetime import timezone

TinyMod: Client
GUILD: Guild
ADMIN_ROLE: Role

GITHUB = Github(auth=Auth.Token(os.environ["GH_TOKEN"]))

NUMBER_PATTERN = re.compile(r'##(\d+)')

@TinyMod.events
async def message_create(client: Client, message: Message):
  # ignore messages from bots
  if message.author.bot: return
  # ignore empty messages
  if not message.content: return

  # see if there is a `##<number>` at the end of the message
  match = re.search(NUMBER_PATTERN, message.content)
  if match is None: return
  number = int(match.group(1))

  print(f"Trying to link an issue/pr number: {number}")

  issue = GITHUB.get_repo("tinygrad/tinygrad").get_issue(number)
  # determine if it is a PR or not
  if (pr := issue.pull_request is not None): issue = issue.as_pull_request()

  # build an embed
  embed = Embed(title=issue.title, url=issue.html_url)
  embed.add_author(issue.user.name or issue.user.login, issue.user.avatar_url, issue.user.html_url)

  if not pr: state = issue.state
  elif issue.merged: state = "merged"
  elif issue.closed_at is not None: state = "closed"
  elif issue.draft: state = "draft"
  else: state = issue.state
  embed.add_footer(f"GitHub {'Pull' if pr else 'Issue'} #{number} | {state}")

  # fields look ugly so we build a description
  if pr:
    embed.description = f"""**{issue.comments} comments, {issue.commits} commits :: +{issue.additions}, -{issue.deletions}**
    """
    # set the embed color based on the PR status
    if issue.merged:
      embed.color = Color(0x6f42c1)
    elif issue.closed_at is not None:
      embed.color = Color(0xd73a49)
    else:
      if issue.draft: embed.color = Color(0x6a737d)
      else: embed.color = Color(0x2cbe4e)
  else:
    embed.description = f"""**{issue.comments} comments**
    """
    # set the embed color based on the issue status
    if issue.closed_at is not None:
      embed.color = Color(0xd73a49)
    else:
      embed.color = Color(0x2cbe4e)
  embed.description += f"""Created at <t:{int(issue.created_at.replace(tzinfo=timezone.utc).timestamp())}:D>, Updated at <t:{int(issue.updated_at.replace(tzinfo=timezone.utc).timestamp())}:D>"""

  print(f"Linked issue/pr number: {number}")

  # link to the github issue or pr
  await client.message_create(message.channel, embed=embed)

