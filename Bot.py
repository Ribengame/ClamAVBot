import discord
import aiohttp
import os
import subprocess
import tempfile
import zipfile

TOKEN = "PASTE_YOUR_DISCORD_BOT_TOKEN_HERE"

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author.bot:
        return

    for attachment in message.attachments:
        try:
            # Download the attachment to a temporary file
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                async with aiohttp.ClientSession() as session:
                    async with session.get(attachment.url) as resp:
                        if resp.status == 200:
                            tmp.write(await resp.read())
                        else:
                            await message.channel.send(f"Failed to download `{attachment.filename}`.")
                            return
                file_path = tmp.name

            # Check if file is a .zip and if it's encrypted
            if attachment.filename.lower().endswith('.zip'):
                try:
                    with zipfile.ZipFile(file_path, 'r') as zip_file:
                        encrypted = any(info.flag_bits & 0x1 for info in zip_file.infolist())
                        if encrypted:
                            await message.channel.send(f"`{attachment.filename}` is encrypted. I cannot detect viruses.")
                            continue  # Skip scanning
                except zipfile.BadZipFile:
                    await message.channel.send(f"`{attachment.filename}` is not a valid zip file.")
                    continue

            # Scan the file with ClamAV
            result = subprocess.run(["clamscan", file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = result.stdout.decode()

            # Send scan result to Discord
            if "FOUND" in output:
                await message.channel.send(f"Virus detected in `{attachment.filename}`:\n```{output}```")
            elif "OK" in output:
                await message.channel.send(f"`{attachment.filename}` is clean.")
            else:
                await message.channel.send(f"Scan result for `{attachment.filename}` is ambiguous:\n```{output}```")

        except Exception as e:
            await message.channel.send(f"Error while scanning `{attachment.filename}`: {e}")

        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

client.run(TOKEN)
