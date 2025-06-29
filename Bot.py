import discord
import aiohttp
import os
import subprocess
import tempfile

# Provide the token directly here
TOKEN = "PASTE_YOUR_DISCORD_BOT_TOKEN_HERE"

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# The following Git update logic is disabled
# import git
# import schedule
# import time
# import threading
# GIT_REPO = "https://github.com/Ribengame/ClamAVBot.git"
# GIT_BRANCH = "main"
# CLONE_DIR = "/app/code"

# def pull_latest():
#     try:
#         if not os.path.isdir(CLONE_DIR + "/.git"):
#             git.Repo.clone_from(GIT_REPO, CLONE_DIR, branch=GIT_BRANCH)
#             print("Repository cloned")
#         else:
#             repo = git.Repo(CLONE_DIR)
#             origin = repo.remotes.origin
#             origin.pull()
#             print("Repository updated")
#     except Exception as e:
#         print(f"Git update failed: {e}")

# schedule.every(5).minutes.do(pull_latest)

# def run_schedule():
#     while True:
#         schedule.run_pending()
#         time.sleep(1)

# threading.Thread(target=run_schedule, daemon=True).start()
# pull_latest()

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
