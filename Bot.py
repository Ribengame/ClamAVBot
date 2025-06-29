DISCORD_TOKEN=Here_paste_token
GIT_REPO=https://github.com/Ribengame/ClamAVBot.git
GIT_BRANCH=main

import discord
import aiohttp
import os
import subprocess
import tempfile
import git
import schedule
import time
import threading
from dotenv import load_dotenv

#
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GIT_REPO = os.getenv("GIT_REPO")
GIT_BRANCH = os.getenv("GIT_BRANCH", "main")
CLONE_DIR = "/app/code"

intents = discord.Intents.default()
intents.message_content = True

#
def pull_latest():
    try:
        if not os.path.isdir(CLONE_DIR + "/.git"):
            git.Repo.clone_from(GIT_REPO, CLONE_DIR, branch=GIT_BRANCH)
            print("📥 Repository cloned")
        else:
            repo = git.Repo(CLONE_DIR)
            origin = repo.remotes.origin
            origin.pull()
            print("🔄 Repository updated")
    except Exception as e:
        print(f"❌ Git update failed: {e}")

#
schedule.every(5).minutes.do(pull_latest)

def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

threading.Thread(target=run_schedule, daemon=True).start()

#
pull_latest()

#
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author.bot:
        return

    for attachment in message.attachments:
        try:
            # ⬇️ Pobierz plik do tymczasowego katalogu
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                async with aiohttp.ClientSession() as session:
                    async with session.get(attachment.url) as resp:
                        if resp.status == 200:
                            tmp.write(await resp.read())
                        else:
                            await message.channel.send(f"❌ Nie udało się pobrać pliku `{attachment.filename}`.")
                            return
                file_path = tmp.name

            #
            result = subprocess.run(["clamscan", file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = result.stdout.decode()

            #
            if "FOUND" in output:
                await message.channel.send(f"⚠️ Virus detected in `{attachment.filename}`!\n```{output}```")
            elif "OK" in output:
                await message.channel.send(f"✅ `{attachment.filename}` is clean!")
            else:
                await message.channel.send(f"❓ Ambiguous result for `{attachment.filename}`:\n```{output}```")

        except Exception as e:
            await message.channel.send(f"❌ Error scanning `{attachment.filename}`: {e}")

        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

client.run(TOKEN)
