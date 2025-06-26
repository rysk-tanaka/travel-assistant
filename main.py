"""
TravelAssistant - AI-powered travel preparation assistant
Main entry point for the Discord bot
"""

import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main function to run the bot"""
    # Check required environment variables
    required_vars = ['DISCORD_TOKEN', 'GITHUB_TOKEN']
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please copy .env.example to .env and fill in the required values")
        sys.exit(1)

    # Import bot after environment check
    try:
        import discord
        from discord.ext import commands
        logger.info("Discord.py imported successfully")
    except ImportError:
        logger.error("discord.py not found. Please install with: uv sync")
        sys.exit(1)

    # Import our modules
    from src.bot.commands import TripCommands

    # Bot configuration
    intents = discord.Intents.default()
    intents.message_content = True

    bot = commands.Bot(
        command_prefix='!',
        intents=intents,
        description='AI-powered Travel Assistant'
    )

    @bot.event
    async def on_ready():
        """Event triggered when the bot is ready"""
        logger.info(f'{bot.user} has connected to Discord!')
        logger.info(f'Bot is in {len(bot.guilds)} guilds')

        # Load cogs
        try:
            await bot.load_extension('src.bot.commands')
            logger.info('Loaded TripCommands cog')
        except Exception as e:
            logger.error(f'Failed to load cog: {e}')

        # Sync slash commands
        try:
            synced = await bot.tree.sync()
            logger.info(f'Synced {len(synced)} slash commands')
        except Exception as e:
            logger.error(f'Failed to sync commands: {e}')

    @bot.event
    async def on_command_error(ctx, error):
        """Global error handler"""
        if isinstance(error, commands.CommandNotFound):
            await ctx.send('コマンドが見つかりません。`!help`で利用可能なコマンドを確認してください。')
        else:
            logger.error(f'Error in command {ctx.command}: {error}')
            await ctx.send('エラーが発生しました。管理者に連絡してください。')

    # Simple test command
    @bot.command(name='ping')
    async def ping(ctx):
        """Test command to check if bot is responsive"""
        await ctx.send(f'Pong! Latency: {round(bot.latency * 1000)}ms')

    # Slash command example
    @bot.tree.command(name='trip', description='旅行準備アシスタント')
    async def trip(interaction: discord.Interaction):
        """Base trip command"""
        await interaction.response.send_message(
            'TravelAssistant へようこそ！\\n'
            '利用可能なサブコマンド:\\n'
            '- `/trip smart` - スマートチェックリスト生成\\n'
            '- `/trip check` - チェックリスト確認\\n'
            '詳細は開発中です...'
        )

    # Run the bot
    try:
        bot.run(os.getenv('DISCORD_TOKEN'))
    except discord.LoginFailure:
        logger.error('Invalid Discord token. Please check your .env file')
        sys.exit(1)
    except Exception as e:
        logger.error(f'Unexpected error: {e}')
        sys.exit(1)


if __name__ == '__main__':
    main()
