import discord
import aiohttp
import os
import tempfile
import zipfile
import pyclamd

TOKEN = "PASTE_YOUR_DISCORD_BOT_TOKEN_HERE"

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Initialize ClamAV daemon client using Unix socket.
# For TCP, use ClamdNetworkSocket(host='127.0.0.1', port=3310)
cd = pyclamd.ClamdUnixSocket()

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author.bot:
        return

    for attachment in message.attachments:
        try:
            # Download attachment to a temporary file
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                async with aiohttp.ClientSession() as session:
                    async with session.get(attachment.url) as resp:
                        if resp.status == 200:
                            content = await resp.read()
                            tmp.write(content)
                        else:
                            await message.channel.send(f"Failed to download `{attachment.filename}`.")
                            return
                file_path = tmp.name

            # Check if the file is a ZIP archive and verify if it's encrypted
            if attachment.filename.lower().endswith('.zip'):
                try:
                    with zipfile.ZipFile(file_path, 'r') as zip_file:
                        encrypted = any(info.flag_bits & 0x1 for info in zip_file.infolist())
                        if encrypted:
                            await message.channel.send(f"`{attachment.filename}` is encrypted. Unable to scan for viruses.")
                            continue
                except zipfile.BadZipFile:
                    await message.channel.send(f"`{attachment.filename}` is not a valid zip file.")
                    continue

            # Scan file contents in memory to avoid file permission issues
            scan_result = cd.scan_stream(content)

            # Interpret scan results
            if scan_result is None:
                await message.channel.send(f"`{attachment.filename}` is clean.")
            else:
                virus_name = list(scan_result.values())[0][1]
                await message.channel.send(f"Virus detected in `{attachment.filename}`: `{virus_name}`")

        except Exception as e:
            await message.channel.send(f"Error occurred while scanning `{attachment.filename}`: {e}")

        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

client.run(TOKEN)
