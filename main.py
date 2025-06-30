"""
TravelAssistant - AI-powered travel preparation assistant
Main entry point for the Discord bot
"""

import logging
import os
import sys

import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def check_environment() -> None:
    """Check required environment variables."""
    required_vars = ["DISCORD_TOKEN", "GITHUB_TOKEN"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please copy .env.example to .env and fill in the required values")
        sys.exit(1)

    # Check if discord.py is available
    try:
        version = discord.__version__
        logger.info(f"Discord.py {version} imported successfully")
    except AttributeError:
        logger.error("discord.py not found. Please install with: uv sync")
        sys.exit(1)


def create_bot() -> commands.Bot:
    """Create and configure the Discord bot."""
    intents = discord.Intents.default()
    intents.message_content = True

    bot = commands.Bot(
        command_prefix="!", intents=intents, description="AI-powered Travel Assistant"
    )

    @bot.event
    async def on_ready() -> None:
        """Event triggered when the bot is ready"""
        logger.info(f"{bot.user} has connected to Discord!")
        logger.info(f"Bot is in {len(bot.guilds)} guilds")

        # Load cogs
        try:
            await bot.load_extension("src.bot.commands")
            logger.info("Loaded TripCommands cog")
        except Exception as e:
            logger.error(f"Failed to load cog: {e}")

        # Load schedule commands cog
        try:
            await bot.load_extension("src.bot.schedule_commands")
            logger.info("Loaded ScheduleCommands cog")
        except Exception as e:
            logger.error(f"Failed to load schedule commands cog: {e}")

        # Sync slash commands
        try:
            synced = await bot.tree.sync()
            logger.info(f"Synced {len(synced)} slash commands")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")

    @bot.event
    async def on_command_error(
        ctx: commands.Context[commands.Bot], error: commands.CommandError
    ) -> None:
        """Global error handler"""
        if isinstance(error, commands.CommandNotFound):
            await ctx.send(
                "コマンドが見つかりません。`!help`で利用可能なコマンドを確認してください。"
            )
        else:
            logger.error(f"Error in command {ctx.command}: {error}")
            await ctx.send("エラーが発生しました。管理者に連絡してください。")

    # Simple test command
    @bot.command(name="ping")
    async def ping(ctx: commands.Context[commands.Bot]) -> None:
        """Test command to check if bot is responsive"""
        await ctx.send(f"Pong! Latency: {round(bot.latency * 1000)}ms")

    return bot


def run_bot(bot: commands.Bot) -> None:
    """Run the Discord bot."""
    try:
        token = os.getenv("DISCORD_TOKEN")
        if not token:
            logger.error("DISCORD_TOKEN not found in environment variables")
            sys.exit(1)
        bot.run(token)
    except discord.LoginFailure:
        logger.error("Invalid Discord token. Please check your .env file")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


def main() -> None:
    """Main function to run the bot"""
    check_environment()
    bot = create_bot()
    run_bot(bot)


if __name__ == "__main__":
    main()
