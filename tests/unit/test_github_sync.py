"""
Unit tests for GitHub sync functionality.
"""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from github import GithubException

from src.core.github_sync import GitHubSync
from src.models import ChecklistItem, GitHubSyncError, TripChecklist


@pytest.fixture
def sample_checklist():
    """テスト用のサンプルチェックリスト."""
    return TripChecklist(
        id="test-checklist-001",
        destination="札幌",
        start_date=date(2025, 6, 28),
        end_date=date(2025, 6, 30),
        purpose="business",
        user_id="test-user-123",
        template_used="sapporo_business",
        items=[
            ChecklistItem(
                name="航空券",
                category="移動関連",
                checked=True,
                auto_added=False,
            ),
            ChecklistItem(
                name="身分証明書",
                category="移動関連",
                checked=False,
                auto_added=False,
            ),
            ChecklistItem(
                name="折り畳み傘",
                category="天気対応",
                checked=False,
                auto_added=True,
                reason="降水確率60%",
            ),
        ],
    )


@pytest.fixture
def mock_github():
    """GitHubのモック."""
    with patch("src.core.github_sync.Github") as mock:
        yield mock


@pytest.fixture
def mock_settings():
    """設定のモック."""
    with patch("src.core.github_sync.settings") as mock:
        mock.GITHUB_TOKEN = "test-token"
        mock.GITHUB_USERNAME = "test-user"
        mock.GITHUB_REPO_NAME = "test-repo"
        mock.GITHUB_BRANCH = "main"
        mock.ENABLE_GITHUB_SYNC = True
        mock.github_repo_url = "https://github.com/test-user/test-repo"
        yield mock


class TestGitHubSync:
    """GitHubSync クラスのテスト."""

    def test_init_without_token(self):
        """トークンなしでの初期化エラー."""
        with patch("src.core.github_sync.settings") as mock_settings:
            mock_settings.GITHUB_TOKEN = ""
            with pytest.raises(GitHubSyncError, match="GitHub Token is not configured"):
                GitHubSync()

    def test_init_with_token(self, mock_github, mock_settings):
        """正常な初期化."""
        sync = GitHubSync()
        assert sync.github is not None
        assert sync._repo is None

    def test_get_file_path(self, mock_github, mock_settings, sample_checklist):
        """ファイルパス生成のテスト."""
        sync = GitHubSync()
        path = sync._get_file_path(sample_checklist)
        assert path == "trips/2025/06/20250628-札幌-business.md"

    def test_get_metadata_path(self, mock_github, mock_settings, sample_checklist):
        """メタデータパス生成のテスト."""
        sync = GitHubSync()
        path = sync._get_metadata_path(sample_checklist)
        assert path == "trips/2025/06/20250628-札幌-business_metadata.json"

    def test_save_checklist_disabled(self, mock_github, sample_checklist):
        """GitHub同期が無効な場合."""
        with patch("src.core.github_sync.settings") as mock_settings:
            mock_settings.GITHUB_TOKEN = "test-token"
            mock_settings.ENABLE_GITHUB_SYNC = False

            sync = GitHubSync()
            result = sync.save_checklist(sample_checklist)
            assert result == ""

    def test_save_checklist_new_file(self, mock_github, mock_settings, sample_checklist):
        """新規ファイルの保存."""
        sync = GitHubSync()

        # モックリポジトリ設定
        mock_repo = MagicMock()
        mock_repo.get_contents.side_effect = GithubException(404, {}, {})
        mock_repo.create_file = MagicMock()
        sync._repo = mock_repo

        url = sync.save_checklist(sample_checklist)

        # create_fileが2回呼ばれることを確認（チェックリストとメタデータ）
        assert mock_repo.create_file.call_count == 2
        assert (
            url
            == "https://github.com/test-user/test-repo/blob/main/trips/2025/06/20250628-札幌-business.md"
        )

    def test_save_checklist_update_file(self, mock_github, mock_settings, sample_checklist):
        """既存ファイルの更新."""
        sync = GitHubSync()

        # モックリポジトリ設定
        mock_repo = MagicMock()
        mock_file = MagicMock()
        mock_file.sha = "test-sha"
        mock_repo.get_contents.return_value = mock_file
        mock_repo.update_file = MagicMock()
        sync._repo = mock_repo

        url = sync.save_checklist(sample_checklist)

        # update_fileが2回呼ばれることを確認
        assert mock_repo.update_file.call_count == 2
        assert (
            url
            == "https://github.com/test-user/test-repo/blob/main/trips/2025/06/20250628-札幌-business.md"
        )

    def test_generate_markdown_content(self, mock_github, mock_settings, sample_checklist):
        """Markdownコンテンツ生成のテスト."""
        sync = GitHubSync()
        content = sync._generate_markdown_content(sample_checklist)

        # Front Matterが含まれているか確認
        assert "---" in content
        assert 'type: "business_trip"' in content
        assert 'destination: "札幌"' in content
        assert "checklist_progress: 33.33" in content

        # チェックリスト内容が含まれているか確認
        assert "# 札幌旅行チェックリスト" in content
        assert "## 移動関連" in content
        assert "- [x] 航空券" in content
        assert "- [ ] 身分証明書" in content
        assert "## 天気対応" in content
        assert "- [ ] 折り畳み傘" in content
        assert "⭐ 降水確率60%" in content

    def test_get_user_trips_disabled(self, mock_github):
        """GitHub同期が無効な場合の履歴取得."""
        with patch("src.core.github_sync.settings") as mock_settings:
            mock_settings.GITHUB_TOKEN = "test-token"
            mock_settings.ENABLE_GITHUB_SYNC = False

            sync = GitHubSync()
            trips = sync.get_user_trips("test-user")
            assert trips == []

    def test_get_user_trips_success(self, mock_github, mock_settings):
        """履歴取得の成功ケース."""
        sync = GitHubSync()

        # モックリポジトリ設定
        mock_repo = MagicMock()

        # メタデータファイルのモック
        mock_metadata_file = MagicMock()
        mock_metadata_file.type = "file"
        mock_metadata_file.name = "20250628-札幌-business_metadata.json"
        mock_metadata_file.path = "trips/2025/06/20250628-札幌-business_metadata.json"
        mock_metadata_file.decoded_content.decode.return_value = """
        {
            "checklist_id": "test-001",
            "user_id": "test-user",
            "status": "planning",
            "created_at": "2025-06-27T10:00:00",
            "updated_at": "2025-06-27T11:00:00",
            "completion_percentage": 33.33
        }
        """

        mock_repo.get_contents.return_value = [mock_metadata_file]
        sync._repo = mock_repo

        trips = sync.get_user_trips("test-user", limit=10)

        assert len(trips) == 1
        assert trips[0]["checklist_id"] == "test-001"
        assert trips[0]["status"] == "planning"
        assert trips[0]["year"] == "2025"
        assert trips[0]["month"] == "06"
        assert trips[0]["filename"] == "20250628-札幌-business"

    def test_delete_checklist_success(self, mock_github, mock_settings):
        """チェックリスト削除の成功ケース."""
        sync = GitHubSync()

        # モックリポジトリ設定
        mock_repo = MagicMock()

        # メタデータファイルのモック
        mock_metadata_file = MagicMock()
        mock_metadata_file.path = "trips/2025/06/test_metadata.json"
        mock_metadata_file.sha = "metadata-sha"
        mock_metadata_file.decoded_content.decode.return_value = """
        {
            "checklist_id": "test-001",
            "user_id": "test-user"
        }
        """

        # Markdownファイルのモック
        mock_markdown_file = MagicMock()
        mock_markdown_file.sha = "markdown-sha"

        mock_repo.get_contents.side_effect = [
            [mock_metadata_file],  # _find_metadata_files
            mock_markdown_file,  # Markdownファイル取得
        ]
        mock_repo.delete_file = MagicMock()

        sync._repo = mock_repo

        result = sync.delete_checklist("test-001", "test-user")

        assert result is True
        assert mock_repo.delete_file.call_count == 2

    def test_delete_checklist_not_found(self, mock_github, mock_settings):
        """存在しないチェックリストの削除."""
        sync = GitHubSync()

        # モックリポジトリ設定
        mock_repo = MagicMock()
        mock_repo.get_contents.return_value = []  # 空のリスト
        sync._repo = mock_repo

        result = sync.delete_checklist("nonexistent", "test-user")

        assert result is False
