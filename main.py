
import discord
from discord import app_commands
from discord.ext import commands

from config import TOKEN
from music import MusicPlayer
from services.music_source import pesquisar_musicas


intents = discord.Intents.default()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

players = {}


def get_player(guild_id):

    if guild_id not in players:

        players[guild_id] = MusicPlayer(
            bot,
            guild_id
        )

    return players[guild_id]


@bot.event
async def on_ready():

    await bot.tree.sync()

    print("Bot conectado:", bot.user)


# COMANDO PLAY

@bot.tree.command(
    name="play",
    description="Pesquisa e adiciona uma musica"
)
@app_commands.describe(
    pesquisa="Nome da musica ou artista"
)
async def play(
    interaction: discord.Interaction,
    pesquisa: str
):

    if not interaction.user.voice:

        await interaction.response.send_message(
            "Entre em um canal de voz primeiro!",
            ephemeral=True
        )
        return

    await interaction.response.defer()

    try:

        musicas = await pesquisar_musicas(pesquisa)

        if not musicas:

            await interaction.followup.send(
                "Nenhuma musica encontrada."
            )
            return

        musica = musicas[0]

        channel = interaction.user.voice.channel

        voice = interaction.guild.voice_client

        if voice is None:

            voice = await channel.connect()

        elif voice.channel != channel:

            await voice.move_to(channel)

        player = get_player(interaction.guild_id)

        await player.add(musica)

        await interaction.followup.send(
            "Musica adicionada: **" +
            musica["title"] + "**"
        )

    except Exception as error:

        print("Erro no comando play:", error)

        await interaction.followup.send(
            "Nao foi possivel adicionar a musica. Verifique o terminal."
        )


# COMANDO SKIP

@bot.tree.command(
    name="skip",
    description="Avanca para a proxima musica"
)
async def skip(interaction: discord.Interaction):

    player = get_player(interaction.guild_id)

    voice = interaction.guild.voice_client

    if voice is None or not voice.is_playing():

        await interaction.response.send_message(
            "Nao ha musica tocando."
        )
        return

    await player.skip(voice)

    await interaction.response.send_message(
        "Musica avancada!"
    )


# COMANDO STOP

@bot.tree.command(
    name="stop",
    description="Para a musica e limpa a fila"
)
async def stop(interaction: discord.Interaction):

    player = get_player(interaction.guild_id)

    voice = interaction.guild.voice_client

    await player.stop(voice)

    await interaction.response.send_message(
        "Reproducao parada e fila limpa!"
    )


# COMANDO PAUSE

@bot.tree.command(
    name="pause",
    description="Pausa a musica"
)
async def pause(interaction: discord.Interaction):

    voice = interaction.guild.voice_client

    if voice and voice.is_playing():

        voice.pause()

        await interaction.response.send_message(
            "Musica pausada!"
        )

    else:

        await interaction.response.send_message(
            "Nao existe musica tocando."
        )


# COMANDO RESUME

@bot.tree.command(
    name="resume",
    description="Retoma a musica"
)
async def resume(interaction: discord.Interaction):

    voice = interaction.guild.voice_client

    if voice and voice.is_paused():

        voice.resume()

        await interaction.response.send_message(
            "Musica retomada!"
        )

    else:

        await interaction.response.send_message(
            "Nao existe musica pausada."
        )


# COMANDO QUEUE

@bot.tree.command(
    name="queue",
    description="Mostra a fila de musicas"
)
async def queue(interaction: discord.Interaction):

    player = get_player(interaction.guild_id)

    embed = discord.Embed(
        title="Fila de reproducao",
        color=discord.Color.blurple()
    )

    if player.current:

        embed.add_field(
            name="Tocando agora",
            value=player.current["title"],
            inline=False
        )

    else:

        embed.add_field(
            name="Tocando agora",
            value="Nenhuma musica",
            inline=False
        )

    musicas = player.get_queue()

    if musicas:

        descricao = ""

        for index, musica in enumerate(musicas, start=1):

            descricao += (
                str(index) + ". " +
                musica["title"] + "\n"
            )

        embed.add_field(
            name="Proximas musicas",
            value=descricao,
            inline=False
        )

    else:

        embed.add_field(
            name="Proximas musicas",
            value="A fila esta vazia.",
            inline=False
        )

    await interaction.response.send_message(
        embed=embed
    )


bot.run(TOKEN)
