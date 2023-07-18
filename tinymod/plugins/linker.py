from hata import Client, Guild, Role, Message, Embed
from github import Github, Auth

import os, re
from datetime import timezone

TinyMod: Client
GUILD: Guild
ADMIN_ROLE: Role

GITHUB = Github(auth=Auth.Token(os.environ["GH_TOKEN"]))

NUMBER_PATTERN = re.compile(r'#(\d+)$')

@TinyMod.events
async def message_create(client: Client, message: Message):
  # ignore messages from bots
  if message.author.bot: return
  # ignore empty messages
  if not message.content: return

  # see if there is a `#<number>` at the end of the message
  match = re.search(NUMBER_PATTERN, message.content)
  if match is None: return
  number = int(match.group(1))

  issue = GITHUB.get_repo("tinygrad/tinygrad").get_issue(number)
  # determine if it is a PR or not
  if (pr := issue.pull_request is not None): issue = issue.as_pull_request()

  # build an embed
  embed = Embed(title=issue.title, url=issue.html_url)
  embed.add_author(issue.user.name or issue.user.login, issue.user.avatar_url, issue.user.html_url)
  embed.add_footer(f"GitHub {'Pull' if pr else 'Issue'} #{number}")

  # fields look ugly so we build a description
  embed.description = f"""Created at <t:{int(issue.created_at.replace(tzinfo=timezone.utc).timestamp())}:D>, Updated at <t:{int(issue.updated_at.replace(tzinfo=timezone.utc).timestamp())}:D>
                    **{issue.comments} comments"""
  if pr:
    embed.description += f""", {issue.commits} commits :: +{issue.additions}, -{issue.deletions}**"""
  else: embed.description += "**"

  # link to the github issue or pr
  await client.message_create(message.channel, embed=embed)

