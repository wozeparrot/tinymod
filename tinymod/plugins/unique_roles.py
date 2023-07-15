from hata import Client, Guild, Role

TinyMod: Client
GUILD: Guild
ADMIN_ROLE: Role

BLUE_ROLE = Role.precreate(1126608788674322472)
PURPLE_ROLE = Role.precreate(1068980606672850944)

@TinyMod.events
async def guild_user_update(client: Client, guild: Guild, user, old_attributes):
  if "role_ids" not in old_attributes: return

  if not (PURPLE_ROLE.id in old_attributes["role_ids"] or BLUE_ROLE.id in old_attributes["role_ids"]): return

  # check if the user has the purple role previously
  if PURPLE_ROLE.id in old_attributes["role_ids"]:
    # check if the user has the blue role now
    if user.has_role(BLUE_ROLE):
      # remove the purple role
      await client.user_role_delete(user, PURPLE_ROLE)
  # check if the user has the blue role previously
  elif BLUE_ROLE.id in old_attributes["role_ids"]:
    # check if the user has the purple role now
    if user.has_role(PURPLE_ROLE):
      # remove the blue role
      await client.user_role_delete(user, BLUE_ROLE)
