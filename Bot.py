import discord, aiohttp, os, subprocess, tempfile, git, schedule, time, threading

TOKEN = os.getenv("DISCORD_TOKEN")
GIT_REPO = os.getenv("GIT_REPO")  # e.g. "https://github.com/user/repo.git"
GIT_BRANCH = os.getenv("GIT_BRANCH", "main")
CLONE_DIR = "/app/code"

intents = discord.Intents.default()
intents.message_content = True

# update
def pull_latest():
    if not os.path.isdir(CLONE_DIR+"/.git"):
        git.Repo.clone_from(GIT_REPO, CLONE_DIR, branch=GIT_BRANCH)
        print("📥 Repository cloned")
    else:
        repo = git.Repo(CLONE_DIR)
        origin = repo.remotes.origin
        origin.pull()
        print("🔄 Repository updated")

# 
schedule.every(5).minutes.do(pull_latest)

def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

# 
threading.Thread(target=run_schedule, daemon=True).start()

# 
pull_latest()

# 
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"🔧 Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author.bot: return
    for attachment in message.attachments:
        # 
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            async with aiohttp.ClientSession() as session:
                async with session.get(attachment.url) as resp:
                    if resp.status == 200:
                        tmp.write(await resp.read())
            file_path = tmp.name

        # 
        result = subprocess.run(["clamscan", file_path], stdout=subprocess.PIPE)
        output = result.stdout.decode()
        os.remove(file_path)

        if "OK" in output:
            await message.channel.send(f"✅ `{attachment.filename}` is clean!")
        elif "FOUND" in output:
            await message.channel.send(f"⚠️ Virus detected in `{attachment.filename}`!\n```{output}```")
        else:
            await message.channel.send(f"❓ The result is ambiguous:\n```{output}```")

client.run(TOKEN)
