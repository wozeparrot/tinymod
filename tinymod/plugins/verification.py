from hata import Client, Embed, EmbedField, Guild, InteractionEvent, Role, Channel
from hata.ext.slash import Button, ButtonStyle, InteractionResponse, Row, iter_component_interactions

import random

TinyMod: Client
GUILD: Guild
ADMIN_ROLE: Role

NUMBER_OF_CLICKS = 3

ROLE = Role.precreate(1068999934516408380)
CHANNEL = Channel.precreate(1069241062616469566)

# Randomized Button Based Verification
RED_BUTTON = Button("Red", custom_id="verification.red", style=ButtonStyle.red)
GREEN_BUTTON = Button("Green", custom_id="verification.green", style=ButtonStyle.green)
BLUE_BUTTON = Button("Blue", custom_id="verification.blue", style=ButtonStyle.blue)
COMPONENTS = Row(RED_BUTTON, GREEN_BUTTON, BLUE_BUTTON)
BUTTONS = ["red", "green", "blue"]
BUTTON_EMOJI = {"red": "🔴", "green": "🟢", "blue": "🔵"}

@TinyMod.interactions(guild=GUILD, show_for_invoking_user_only=True)
async def verify(client: Client, event: InteractionEvent):
  early_exit = False
  if not event.user.has_role(ADMIN_ROLE):
    if event.user.has_role(ROLE):
      early_exit = True
      yield "You are already verified!"
    if event.channel != CHANNEL and not early_exit:
      early_exit = True
      yield "Please use this command in <#1069241062616469566>."

  if not early_exit:
    # generate a list of buttons that have to be clicked in order (3 for now)
    buttons = random.choices(BUTTONS, k=NUMBER_OF_CLICKS)

    print(f"Serving verification request from {event.user.full_name} ({event.user.id}) with buttons {buttons}")

    # send the initial verification message
    embed = Embed("Please click on the buttons in the following order")
    for button in buttons:
      embed.add_field(f"{BUTTON_EMOJI[button]} {button.capitalize()}", None, inline=True)
    message = yield InteractionResponse(embed=embed, components=COMPONENTS)

    failed = False
    try:
      clicked = []
      async for component_interaction in iter_component_interactions(message, timeout=10, check=lambda interaction: interaction.user is event.user):
        # check if the user clicked the correct button
        if component_interaction.custom_id.split(".")[-1] == buttons[len(clicked)]:
          embed.set_field(len(clicked), EmbedField(f"~~⚫ {buttons[len(clicked)].capitalize()}~~", inline=True))
          clicked.append(component_interaction.custom_id)
          if len(clicked) == NUMBER_OF_CLICKS:
            break
          yield InteractionResponse(embed=embed, components=COMPONENTS, message=message, event=component_interaction)
        else:
          failed = True
          embed.title = "Incorrect button clicked! Restart verification by typing `/verify`"
          embed.description = "❌"
          embed.fields = None
          yield InteractionResponse(embed=embed, components=None, message=message, event=component_interaction)
    except TimeoutError:
      failed = True
      embed.title = "Verification timed out! Restart verification by typing `/verify`"
      embed.description = "❌"
      embed.fields = None
      yield InteractionResponse(embed=embed, components=None, message=message, event=event)

      print(f"Verification timed out for {event.user.full_name} ({event.user.id})")

    if not failed:
      embed.title = "Verification successful!"
      embed.description = "✅"
      embed.fields = None
      yield InteractionResponse(embed=embed, components=None, message=message, event=event)

      # add the role to the user
      await client.user_role_add(event.user, ROLE)

      print(f"Verification successful for {event.user.full_name} ({event.user.id})")
    else: print(f"Verification failed for {event.user.full_name} ({event.user.id})")
