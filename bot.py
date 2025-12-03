# Zaroori Libraries Ko Import Karein
import os
import logging
import discord
from discord.ext import commands
from digitalocean import Manager, Droplet
from dotenv import load_dotenv

# --- Configuration & Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# .env file se keys load hongi
load_dotenv()

DISCORD_TOKEN = os.getenv("MTQ0MjM4OTE5MTMxNTk0NzYwNQ.GDkTV6.d14lDjsQFeB_6RFCVep1Hr5T0GGkDCJp9Sob84") 
# Admin ID ko int mein convert karna zaroori hai
ADMIN_USER_ID = int(os.getenv("DISCORD_ADMIN_ID", 0))

DO_TOKEN = os.getenv("DIGITALOCEAN_API_TOKEN")

# DigitalOcean Manager Initialize Karein
try:
    # 🐛 Bug Fix: Yahan DO Token ka check hamesha zaroori hai
    if not DO_TOKEN:
        raise ValueError("DIGITALOCEAN_API_TOKEN is not set.")
    do_manager = Manager(token=DO_TOKEN)
except Exception as e:
    logger.error(f"DigitalOcean Manager initialization failed: {e}")
    exit(1)

# --- Discord Bot Setup ---
# ✅ Bug Fix: Commands ke arguments padhne ke liye message_content Intent zaroori hai
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# --- Utility Functions ---

def is_admin():
    """Custom check function ki command dene wala user admin hai ya nahi."""
    # ✅ Bug Fix: is_admin ko commands.check ke liye sahi tareeke se define kiya gaya hai
    async def predicate(ctx):
        if ctx.author.id != ADMIN_USER_ID:
            await ctx.send("🚫 Aap authorized admin nahi hain.")
            logger.warning(f"Unauthorized access attempt by user ID: {ctx.author.id}")
            return False
        return True
    return commands.check(predicate)

# --- Discord Event Handler ---

@bot.event
async def on_ready():
    """Jab bot Discord se successfully connect ho jaye."""
    print('--------------------------------------------------')
    print(f'🤖 Bot logged in as {bot.user.name} ({bot.user.id})')
    print(f'🔑 Admin ID set to: {ADMIN_USER_ID}')
    print('--------------------------------------------------')
    logger.info("Discord Bot is ready.")

# --- Discord Commands (Core Logic) ---

@bot.command(name='help', help='Sare available commands dikhata hai.')
@is_admin()
async def help_command_discord(ctx):
    """!help command."""
    await ctx.send(
        "📚 **VPS Deploy Bot - Commands:**\n"
        "--- **Deployment** ---\n"
        "1. `!create <name> <region> <size_slug> <owner>` - Naya VPS create karein.\n"
        "2. `!delete <server_id>` - Server ko delete karein.\n"
        "--- **Management** ---\n"
        "3. `!list` - Saare active servers dekhein.\n"
        "4. `!manage <server_id> <action>` - Server par action (e.g., reboot) karein.\n"
        "5. `!ports <server_id> <port_number>` - Server firewall mein port add karein.\n"
    )

@bot.command(name='create', help='DigitalOcean Droplet create karta hai.')
@is_admin()
async def create_server_discord(ctx, name: str, region: str, size: str, owner: str):
    """!create command."""
    
    owner_tag = owner.lower() # Lint Fix: Consistent lower case for tags
    image = 'ubuntu-22-04-x64' 
    tags = [owner_tag, "bot-deployed", "discord-user"]

    await ctx.send(
        f"⏳ Deploying '{name}' (Size: {size}, Owner: {owner_tag}). Wait for confirmation..."
    )

    try:
        droplet = Droplet(
            token=DO_TOKEN,
            name=name,
            region=region,
            size_slug=size,
            image=image,
            tags=tags,
            # ssh_keys=[key_id] 
        )
        droplet.create()
        logger.info(f"Deployment request sent for: {name} by {owner_tag}")

        await ctx.send(
            f"✅ Droplet **'{name}'** create hone ki request bhej di gayi hai. "
            f"Tags: {', '.join(tags)}"
        )

    except Exception as e:
        error_message = f"❌ Creation Failed! Error: {e}"
        logger.error(error_message)
        await ctx.send(error_message)


@bot.command(name='list', help='Saare active Droplets ki list dikhata hai.')
@is_admin()
async def list_servers_discord(ctx):
    """!list command."""
    await ctx.send("⏳ Fetching active droplets...")
    
    try:
        droplets = do_manager.get_all_droplets()
        
        if not droplets:
            await ctx.send("No active droplets found.")
            return

        message = "🌐 **Active DigitalOcean Droplets:**\n"
        for d in droplets:
            ip = d.ip_address if d.ip_address else "IP Pending/Unknown"
            
            message += (
                f"--- \n"
                f"**Name:** `{d.name}`\n"
                f"**ID:** `{d.id}`\n"
                f"**Status:** `{d.status}`\n"
                f"**IP:** `{ip}`\n"
            )
        
        await ctx.send(message)

    except Exception as e:
        await ctx.send(f"❌ Droplets fetch nahi ho paye. Error: {e}")
        logger.error(f"Error fetching droplets: {e}")


@bot.command(name='manage', help='Server par action (reboot/power_off, etc.) karta hai.')
@is_admin()
async def manage_server_discord(ctx, server_id: str, action: str):
