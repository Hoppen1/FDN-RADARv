import os
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

# Carga las variables de entorno desde el archivo .env (para desarrollo local)
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Configuración de Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# IDs configurados
CANAL_JUSTIFICAR_ID = 1472753301044072589
ROL_PERSONAL_ID = 1472065658752733214


class JustificacionView(discord.ui.View):

  def __init__(self):
    super().__init__(timeout=None)

  @discord.ui.button(
      label="Validar Justificación",
      style=discord.ButtonStyle.green,
      custom_id="btn_validar_justificacion",
  )
  async def validar(
      self, interaction: discord.Interaction, button: discord.ui.Button
  ):
    # Respondemos de inmediato para evitar el error de tiempo de espera
    await interaction.response.defer(ephemeral=True)

    if not interaction.message.embeds:
      await interaction.followup.send(
          "No se encontró el embed.", ephemeral=True
      )
      return

    embed = interaction.message.embeds[0]
    fields = embed.fields
    nuevos_campos = []

    for field in fields:
      if field.name == "Estado":
        nuevos_campos.append(
            discord.EmbedField(
                name="Estado", value="🟢 Aceptada", inline=field.inline
            )
        )
      else:
        nuevos_campos.append(field)

    embed.clear_fields()
    for f in nuevos_campos:
      embed.add_field(name=f.name, value=f.value, inline=f.inline)

    embed.color = discord.Color.green()
    button.disabled = True
    button.label = "Validada"
    button.style = discord.ButtonStyle.secondary

    # Actualizamos el mensaje con la vista modificada
    await interaction.message.edit(embed=embed, view=self)
    await interaction.followup.send(
        "Has validado la justificación correctamente.", ephemeral=True
    )


class JustificarModal(discord.ui.Modal, title="Crear Justificación de Ausencia"):
  motivo = discord.ui.TextInput(
      label="Motivo de ausencia",
      style=discord.TextStyle.long,
      placeholder="Escribe el motivo detallado...",
      required=True,
  )
  dia_inicio = discord.ui.TextInput(
      label="Día de inicio", placeholder="Ej: DD/MM/AAAA", required=True, max_length=20
  )
  dia_termino = discord.ui.TextInput(
      label="Día de término",
      placeholder="Ej: DD/MM/AAAA",
      required=True,
      max_length=20,
  )

  async def on_submit(self, interaction: discord.Interaction):
    embed = discord.Embed(
        title="📋 Nueva Justificación de Ausencia",
        color=discord.Color.orange(),
        timestamp=discord.utils.utcnow(),
    )
    embed.add_field(
        name="Solicitante", value=interaction.user.mention, inline=False
    )
    embed.add_field(name="Motivo", value=self.motivo.value, inline=False)
    embed.add_field(
        name="Fecha de Inicio", value=self.dia_inicio.value, inline=True
    )
    embed.add_field(
        name="Fecha de Término", value=self.dia_termino.value, inline=True
    )
    embed.add_field(name="Estado", value="🔴 Sin leer", inline=False)
    embed.set_footer(text=f"ID de Usuario: {interaction.user.id}")

    await interaction.channel.send(embed=embed, view=JustificacionView())
    await interaction.response.send_message(
        "Tu justificación ha sido enviada correctamente al panel de revisión.",
        ephemeral=True,
    )


class MensajeModal(discord.ui.Modal, title="Crear Mensaje Informativo"):
  titulo = discord.ui.TextInput(
      label="Título del Mensaje",
      placeholder="Título principal...",
      required=True,
      max_length=256,
  )
  detalle = discord.ui.TextInput(
      label="Detalle / Contenido",
      style=discord.TextStyle.long,
      placeholder="Escribe la información detallada aquí...",
      required=True,
  )
  encargado = discord.ui.TextInput(
      label="Encargado / Autor",
      placeholder="Nombre o equipo responsable",
      required=True,
      max_length=100,
  )

  async def on_submit(self, interaction: discord.Interaction):
    embed = discord.Embed(
        title=f"📢 {self.titulo.value}",
        description=self.detalle.value,
        color=discord.Color.blue(),
        timestamp=discord.utils.utcnow(),
    )
    embed.add_field(
        name="📌 Encargado", value=self.encargado.value, inline=False
    )
    embed.set_footer(
        text=f"Canal de información • Enviado por {interaction.user.name}",
        icon_url=interaction.user.display_avatar.url,
    )

    await interaction.channel.send(embed=embed)
    await interaction.response.send_message(
        "Mensaje publicado exitosamente.", ephemeral=True
    )


@bot.event
async def on_ready():
  print(f"¡Conectado como {bot.user}!")
  
  # Registramos la vista de manera persistente para que los botones sigan respondiendo tras reiniciar
  bot.add_view(JustificacionView())
  
  try:
    synced = await bot.tree.sync()
    print(f"Sincronizados {len(synced)} comandos slash.")
  except Exception as e:
    print(e)


@bot.tree.command(
    name="justificar", description="Envía una solicitud de justificación."
)
async def justificar(interaction: discord.Interaction):
  if interaction.channel_id != CANAL_JUSTIFICAR_ID:
    await interaction.response.send_message(
        "❌ Este comando solo se puede usar en el canal designado para ello.",
        ephemeral=True,
    )
    return
  await interaction.response.send_modal(JustificarModal())


@bot.tree.command(
    name="mensaje",
    description="Crea un mensaje informativo con diseño profesional.",
)
async def mensaje(interaction: discord.Interaction):
  await interaction.response.send_modal(MensajeModal())


@bot.tree.command(
    name="personal",
    description="Muestra un panel actualizado con el personal con rol asignado.",
)
async def personal(interaction: discord.Interaction):
  guild = interaction.guild
  rol = guild.get_role(ROL_PERSONAL_ID)

  if not rol:
    await interaction.response.send_message(
        "❌ No se encontró el rol especificado en este servidor.", ephemeral=True
    )
    return

  miembros_con_rol = [m for m in guild.members if rol in m.roles]
  total = len(miembros_con_rol)
  listado_nombres = (
      "\n".join([m.mention for m in miembros_con_rol])
      if miembros_con_rol
      else "Ninguno"
  )
  if len(listado_nombres) > 1024:
    listado_nombres = (
        "Hay demasiados miembros para listar, pero el contador es exacto."
    )

  embed = discord.Embed(
      title="👥 Panel de Personal Activo",
      description=f"Listado oficial de usuarios con el rol **{rol.name}**.",
      color=discord.Color.purple(),
      timestamp=discord.utils.utcnow(),
  )
  embed.add_field(name="📊 Total de Personal", value=str(total), inline=False)
  embed.add_field(name="📋 Miembros", value=listado_nombres, inline=False)
  embed.set_footer(text="Panel actualizado dinámicamente")

  await interaction.response.send_message(embed=embed)

bot.run(TOKEN)
