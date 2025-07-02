"""
Unit tests for Discord bot commands.
"""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from src.bot.commands import TripCommands
from src.models import ChecklistItem, TripChecklist, TripRequest


@pytest.fixture
def mock_bot():
    """Mock Discord bot."""
    bot = MagicMock(spec=discord.ext.commands.Bot)
    bot.user = MagicMock()
    bot.user.id = 123456789
    bot.user.name = "TestBot"
    return bot


@pytest.fixture
def mock_interaction():
    """Mock Discord interaction."""
    interaction = AsyncMock(spec=discord.Interaction)
    interaction.response = AsyncMock()
    interaction.followup = AsyncMock()
    interaction.user = MagicMock()
    interaction.user.id = 987654321
    interaction.user.name = "TestUser"
    interaction.user.display_name = "TestUser"
    interaction.guild_id = 111111111
    interaction.channel_id = 222222222
    return interaction


@pytest.fixture
def sample_checklist():
    """Sample checklist for testing."""
    return TripChecklist(
        id="test-001",
        destination="東京",
        start_date=date(2025, 7, 10),
        end_date=date(2025, 7, 12),
        purpose="business",
        user_id="987654321",
        template_used="domestic_business",
        items=[
            ChecklistItem(
                name="身分証明書",
                category="移動関連",
                checked=False,
                auto_added=False,
            ),
            ChecklistItem(
                name="充電器",
                category="生活用品",
                checked=True,
                auto_added=False,
            ),
            ChecklistItem(
                name="折り畳み傘",
                category="天気対応",
                checked=False,
                auto_added=True,
                reason="降水確率50%",
            ),
        ],
    )


class TestTripCommands:
    """Test TripCommands cog."""

    @pytest.mark.skip("Discord command cannot be called directly")
    @pytest.mark.asyncio
    async def test_trip_help(self, mock_bot, mock_interaction):
        """Test trip help command."""
        TripCommands(mock_bot)

        # Discord commands cannot be called directly in tests
        # Would need to test the underlying logic separately

    @pytest.mark.skip("Discord command cannot be called directly")
    @pytest.mark.asyncio
    async def test_trip_invalid_subcommand(self, mock_bot, mock_interaction):
        """Test trip with invalid subcommand."""
        TripCommands(mock_bot)

        # Discord commands cannot be called directly in tests
        # Would need to test the underlying logic separately

    @pytest.mark.skip("trip_check command not implemented yet")
    @pytest.mark.asyncio
    async def test_trip_check_no_checklist(self, mock_bot, mock_interaction):
        """Test trip check when no checklist exists."""
        cog = TripCommands(mock_bot)

        await cog.trip_check(mock_interaction)

        # Check error message
        mock_interaction.response.send_message.assert_called_once()
        call_args = mock_interaction.response.send_message.call_args
        assert "現在のチェックリストが見つかりません" in call_args.args[0]

    @pytest.mark.skip("trip_check command not implemented yet")
    @pytest.mark.asyncio
    async def test_trip_check_with_checklist(self, mock_bot, mock_interaction, sample_checklist):
        """Test trip check with existing checklist."""
        cog = TripCommands(mock_bot)
        cog.checklists[str(mock_interaction.user.id)] = sample_checklist

        await cog.trip_check(mock_interaction)

        # Check that checklist embed was sent
        mock_interaction.response.send_message.assert_called_once()
        call_args = mock_interaction.response.send_message.call_args
        assert "embed" in call_args.kwargs
        assert "view" in call_args.kwargs

    @pytest.mark.skip("Discord command cannot be called directly")
    @pytest.mark.asyncio
    async def test_trip_smart_command(self, mock_bot, mock_interaction):
        """Test trip smart command."""
        TripCommands(mock_bot)

        # Discord commands cannot be called directly in tests
        # Would need to test the underlying logic separately

    @pytest.mark.skip("_create_smart_checklist method not implemented yet")
    @pytest.mark.asyncio
    @patch("src.bot.commands.SmartTemplateEngine")
    async def test_create_smart_checklist_success(
        self, mock_engine, mock_bot, mock_interaction, sample_checklist
    ):
        """Test successful checklist creation."""
        # Setup mock engine
        mock_engine_instance = mock_engine.return_value
        mock_engine_instance.generate_checklist.return_value = sample_checklist

        cog = TripCommands(mock_bot)
        cog.smart_engine = mock_engine_instance

        # Create trip request
        trip_request = TripRequest(
            destination="東京",
            start_date=date(2025, 7, 10),
            end_date=date(2025, 7, 12),
            purpose="business",
            user_id="987654321",
        )

        await cog._create_smart_checklist(mock_interaction, trip_request)

        # Check engine was called
        mock_engine_instance.generate_checklist.assert_called_once_with(trip_request)

        # Check response
        mock_interaction.followup.send.assert_called_once()
        call_args = mock_interaction.followup.send.call_args
        assert "embed" in call_args.kwargs
        assert "view" in call_args.kwargs

    @pytest.mark.skip("_create_smart_checklist method not implemented yet")
    @pytest.mark.asyncio
    @patch("src.bot.commands.SmartTemplateEngine")
    async def test_create_smart_checklist_error(self, mock_engine, mock_bot, mock_interaction):
        """Test checklist creation with error."""
        # Setup mock engine to raise error
        mock_engine_instance = mock_engine.return_value
        mock_engine_instance.generate_checklist.side_effect = Exception("Test error")

        cog = TripCommands(mock_bot)
        cog.smart_engine = mock_engine_instance

        # Create trip request
        trip_request = TripRequest(
            destination="東京",
            start_date=date(2025, 7, 10),
            end_date=date(2025, 7, 12),
            purpose="business",
            user_id="987654321",
        )

        await cog._create_smart_checklist(mock_interaction, trip_request)

        # Check error response
        mock_interaction.followup.send.assert_called_once()
        call_args = mock_interaction.followup.send.call_args
        assert "エラー" in call_args.args[0]

    @pytest.mark.skip("trip_list command not implemented yet")
    @pytest.mark.asyncio
    async def test_trip_list_no_github(self, mock_bot, mock_interaction):
        """Test trip list without GitHub sync."""
        cog = TripCommands(mock_bot)
        cog.github_sync = None

        await cog.trip_list(mock_interaction)

        # Check error message
        mock_interaction.response.send_message.assert_called_once()
        call_args = mock_interaction.response.send_message.call_args
        assert "GitHub連携が有効ではありません" in call_args.args[0]

    @pytest.mark.skip("trip_list command not implemented yet")
    @pytest.mark.asyncio
    @patch("src.bot.commands.GitHubSync")
    async def test_trip_list_with_github(self, mock_github, mock_bot, mock_interaction):
        """Test trip list with GitHub sync."""
        # Setup mock GitHub sync
        mock_github_instance = mock_github.return_value
        mock_github_instance.get_user_trips.return_value = [
            {
                "checklist_id": "test-001",
                "filename": "20250710-東京-business",
                "status": "planning",
                "completion_percentage": 33.33,
                "github_url": "https://github.com/test/test/blob/main/trips/2025/07/test.md",
            }
        ]

        cog = TripCommands(mock_bot)
        cog.github_sync = mock_github_instance

        await cog.trip_list(mock_interaction)

        # Check that list was sent
        mock_interaction.response.send_message.assert_called_once()
        call_args = mock_interaction.response.send_message.call_args
        assert "embed" in call_args.kwargs
        embed = call_args.kwargs["embed"]
        assert "過去の旅行" in embed.title

    @pytest.mark.asyncio
    async def test_create_checklist_embed(self, mock_bot, sample_checklist):
        """Test checklist embed creation."""
        cog = TripCommands(mock_bot)

        embed = cog.create_checklist_embed(sample_checklist)

        assert isinstance(embed, discord.Embed)
        assert "東京" in embed.title
        assert len(embed.fields) > 0

        # Check progress field
        progress_field = next((f for f in embed.fields if "進捗" in f.name), None)
        assert progress_field is not None
        assert "33.33%" in progress_field.value
