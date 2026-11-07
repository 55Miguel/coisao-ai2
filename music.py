
import asyncio
import discord
import sys


class MusicPlayer:
    def __init__(self, bot, guild_id):
        self.bot = bot
        self.guild_id = guild_id
        self.queue = asyncio.Queue()
        self.current = None
        self.task = None
        self.next_event = asyncio.Event()
        self.next_event.set()

    async def add(self, track):
        await self.queue.put(track)

        if self.task is None or self.task.done():
            self.task = asyncio.create_task(self.player_loop())

    async def player_loop(self):
        while True:
            track = await self.queue.get()
            self.current = track
            self.next_event.clear()

            guild = self.bot.get_guild(self.guild_id)
            voice = guild.voice_client if guild else None

            try:
                if not voice or not voice.is_connected():
                    print("Bot nao esta conectado ao canal de voz.")
                    continue

                source = discord.FFmpegPCMAudio(
                    track["url"],
                    before_options=(
                            "-reconnect 1 "
                            "-reconnect_streamed 1 "
                            "-reconnect_delay_max 5"
                        ),
                    options="-vn",
                    stderr=sys.stderr
                )

                source = discord.PCMVolumeTransformer(
                    source,
                    volume=1.5
                )

                def after_play(error):
                    if error:
                        print("Erro no player:", error)

                    self.bot.loop.call_soon_threadsafe(
                        self.next_event.set
                    )

                voice.play(source, after=after_play)

                print("Reproduzindo:", track["title"])

                await self.next_event.wait()

            except Exception as error:
                print("Erro na reproducao:", error)

            finally:
                self.current = None
                self.queue.task_done()

    async def skip(self, voice):
        if voice and (voice.is_playing() or voice.is_paused()):
            voice.stop()

    async def stop(self, voice):
        if voice and (voice.is_playing() or voice.is_paused()):
            voice.stop()

        while not self.queue.empty():
            try:
                self.queue.get_nowait()
                self.queue.task_done()
            except asyncio.QueueEmpty:
                break

    async def pause(self, voice):
        if voice and voice.is_playing():
            voice.pause()

    async def resume(self, voice):
        if voice and voice.is_paused():
            voice.resume()

    def get_queue(self):
        return list(self.queue._queue)
