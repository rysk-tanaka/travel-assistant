"""
GitHub integration for storing and retrieving checklist data.

このモジュールは、GitHubリポジトリを使用してチェックリストデータを
永続化するための機能を提供します。
"""

import json
from typing import Any

from github import Github, GithubException
from github.ContentFile import ContentFile
from github.Repository import Repository

from src.config.settings import settings
from src.models import GitHubSyncError, TripChecklist
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class GitHubSync:
    """GitHub同期機能を提供するクラス."""

    def __init__(self) -> None:
        """GitHubクライアントを初期化."""
        if not settings.GITHUB_TOKEN:
            raise GitHubSyncError("GitHub Token is not configured")

        self.github = Github(settings.GITHUB_TOKEN)
        self._repo: Repository | None = None

    @property
    def repo(self) -> Repository:
        """GitHubリポジトリオブジェクトを取得（遅延読み込み）."""
        if self._repo is None:
            try:
                repo_name = f"{settings.GITHUB_USERNAME}/{settings.GITHUB_REPO_NAME}"
                self._repo = self.github.get_repo(repo_name)
                logger.info(f"Connected to GitHub repository: {repo_name}")
            except GithubException as e:
                logger.error(f"Failed to get repository: {e}")
                raise GitHubSyncError(f"Failed to access repository: {e}") from e
        return self._repo

    def _get_file_path(self, checklist: TripChecklist) -> str:
        """チェックリストのGitHub上のファイルパスを生成."""
        year = checklist.start_date.strftime("%Y")
        month = checklist.start_date.strftime("%m")
        destination = checklist.destination.replace("/", "-").replace(" ", "_")
        filename = f"{checklist.start_date.strftime('%Y%m%d')}-{destination}-{checklist.purpose}.md"

        return f"trips/{year}/{month}/{filename}"

    def _get_metadata_path(self, checklist: TripChecklist) -> str:
        """チェックリストのメタデータファイルパスを生成."""
        base_path = self._get_file_path(checklist)
        return base_path.replace(".md", "_metadata.json")

    def save_checklist(self, checklist: TripChecklist) -> str:
        """チェックリストをGitHubに保存."""
        if not settings.ENABLE_GITHUB_SYNC:
            logger.warning("GitHub sync is disabled")
            return ""

        try:
            # Markdownファイルの保存
            file_path = self._get_file_path(checklist)
            content = self._generate_markdown_content(checklist)

            # ファイルの作成または更新
            try:
                file_or_files = self.repo.get_contents(file_path, ref=settings.GITHUB_BRANCH)
                # get_contents()はファイルの場合ContentFile、ディレクトリの場合list[ContentFile]を返す
                if isinstance(file_or_files, list):
                    # ディレクトリの場合はエラー
                    raise GitHubSyncError(f"Path {file_path} is a directory, not a file")

                file = file_or_files  # 型を絞り込み
                self.repo.update_file(
                    path=file_path,
                    message=f"Update checklist for {checklist.destination}",
                    content=content,
                    sha=file.sha,
                    branch=settings.GITHUB_BRANCH,
                )
                logger.info(f"Updated checklist at: {file_path}")
            except GithubException:
                # ファイルが存在しない場合は新規作成
                self.repo.create_file(
                    path=file_path,
                    message=f"Create checklist for {checklist.destination}",
                    content=content,
                    branch=settings.GITHUB_BRANCH,
                )
                logger.info(f"Created new checklist at: {file_path}")

            # メタデータの保存
            self._save_metadata(checklist)

            # GitHub URLを返す
            return f"{settings.github_repo_url}/blob/{settings.GITHUB_BRANCH}/{file_path}"

        except Exception as e:
            logger.error(f"Failed to save checklist: {e}")
            raise GitHubSyncError(f"Failed to save checklist: {e}") from e

    def _save_metadata(self, checklist: TripChecklist) -> None:
        """チェックリストのメタデータを保存."""
        metadata_path = self._get_metadata_path(checklist)
        metadata = {
            "checklist_id": checklist.id,
            "user_id": checklist.user_id,
            "status": checklist.status,
            "created_at": checklist.created_at.isoformat(),
            "updated_at": checklist.updated_at.isoformat(),
            "completion_percentage": checklist.completion_percentage,
            "template_used": checklist.template_used,
            "weather_data": checklist.weather_data,
            "item_stats": {
                "total": checklist.total_count,
                "completed": checklist.completed_count,
                "auto_added": sum(1 for item in checklist.items if item.auto_added),
            },
        }

        content = json.dumps(metadata, ensure_ascii=False, indent=2)

        try:
            file_or_files = self.repo.get_contents(metadata_path, ref=settings.GITHUB_BRANCH)
            if isinstance(file_or_files, list):
                raise GitHubSyncError(f"Path {metadata_path} is a directory, not a file")

            file = file_or_files  # 型を絞り込み
            self.repo.update_file(
                path=metadata_path,
                message=f"Update metadata for {checklist.destination}",
                content=content,
                sha=file.sha,
                branch=settings.GITHUB_BRANCH,
            )
        except GithubException:
            self.repo.create_file(
                path=metadata_path,
                message=f"Create metadata for {checklist.destination}",
                content=content,
                branch=settings.GITHUB_BRANCH,
            )

    def load_checklist(self, checklist_id: str, user_id: str) -> TripChecklist | None:
        """チェックリストIDからチェックリストを読み込み."""
        if not settings.ENABLE_GITHUB_SYNC:
            logger.warning("GitHub sync is disabled")
            return None

        try:
            # メタデータファイルを検索
            metadata_files = self._find_metadata_files(checklist_id)

            for metadata_file in metadata_files:
                metadata = json.loads(metadata_file.decoded_content.decode("utf-8"))

                # ユーザーIDとチェックリストIDが一致するか確認
                if (
                    metadata.get("checklist_id") == checklist_id
                    and metadata.get("user_id") == user_id
                ):
                    # 対応するMarkdownファイルを読み込み
                    markdown_path = metadata_file.path.replace("_metadata.json", ".md")
                    return self._load_checklist_from_path(markdown_path, metadata)

            logger.warning(f"Checklist not found: {checklist_id}")
            return None

        except Exception as e:
            logger.error(f"Failed to load checklist: {e}")
            raise GitHubSyncError(f"Failed to load checklist: {e}") from e

    def _find_metadata_files(self, checklist_id: str) -> list[ContentFile]:
        """指定されたチェックリストIDのメタデータファイルを検索."""
        metadata_files = []

        try:
            # tripsディレクトリを再帰的に検索
            contents_or_file = self.repo.get_contents("trips", ref=settings.GITHUB_BRANCH)

            # 最初のget_contentsの結果を処理
            if isinstance(contents_or_file, list):
                contents = contents_or_file
            else:
                # ファイルの場合（通常はあり得ないが、念のため）
                contents = [contents_or_file]

            while contents:
                file_content = contents.pop(0)
                if file_content.type == "dir":
                    sub_contents = self.repo.get_contents(
                        file_content.path, ref=settings.GITHUB_BRANCH
                    )
                    if isinstance(sub_contents, list):
                        contents.extend(sub_contents)
                    else:
                        contents.append(sub_contents)
                elif file_content.name.endswith("_metadata.json"):
                    metadata_files.append(file_content)

        except GithubException as e:
            logger.error(f"Failed to search metadata files: {e}")

        return metadata_files

    def _load_checklist_from_path(
        self, markdown_path: str, metadata: dict[str, Any]
    ) -> TripChecklist | None:
        """Markdownファイルとメタデータからチェックリストを復元."""
        try:
            file_or_files = self.repo.get_contents(markdown_path, ref=settings.GITHUB_BRANCH)
            if isinstance(file_or_files, list):
                # ディレクトリの場合はエラー
                logger.error(f"Path {markdown_path} is a directory, not a file")
                return None

            markdown_file = file_or_files  # 型を絞り込み
            markdown_content = markdown_file.decoded_content.decode("utf-8")

            # Markdownからチェックリストを復元
            checklist = self._parse_markdown_to_checklist(markdown_content, metadata)
            return checklist

        except Exception as e:
            logger.error(f"Failed to load checklist from path {markdown_path}: {e}")
            return None

    def get_user_trips(self, user_id: str, limit: int = 10) -> list[dict[str, Any]]:
        """指定ユーザーの旅行リストを取得."""
        if not settings.ENABLE_GITHUB_SYNC:
            logger.warning("GitHub sync is disabled")
            return []

        trips = []

        try:
            metadata_files = self._find_metadata_files("")  # 全メタデータファイルを取得

            for metadata_file in metadata_files:
                try:
                    metadata = json.loads(metadata_file.decoded_content.decode("utf-8"))

                    if metadata.get("user_id") == user_id:
                        # ファイルパスから旅行情報を抽出
                        path_parts = metadata_file.path.split("/")
                        if len(path_parts) >= 4:  # trips/YYYY/MM/filename_metadata.json
                            trip_info = {
                                "checklist_id": metadata.get("checklist_id"),
                                "year": path_parts[1],
                                "month": path_parts[2],
                                "filename": path_parts[3].replace("_metadata.json", ""),
                                "status": metadata.get("status"),
                                "created_at": metadata.get("created_at"),
                                "updated_at": metadata.get("updated_at"),
                                "completion_percentage": metadata.get("completion_percentage", 0),
                                "github_url": (
                                    f"{settings.github_repo_url}/blob/{settings.GITHUB_BRANCH}/"
                                    f"{metadata_file.path.replace('_metadata.json', '.md')}"
                                ),
                            }
                            trips.append(trip_info)

                except Exception as e:
                    logger.error(f"Failed to parse metadata file {metadata_file.path}: {e}")
                    continue

            # 更新日時でソート（新しい順）
            trips.sort(key=lambda x: x.get("updated_at", ""), reverse=True)

            return trips[:limit]

        except Exception as e:
            logger.error(f"Failed to get user trips: {e}")
            return []

    def delete_checklist(self, checklist_id: str, user_id: str) -> bool:
        """チェックリストを削除."""
        if not settings.ENABLE_GITHUB_SYNC:
            logger.warning("GitHub sync is disabled")
            return False

        try:
            # メタデータファイルを検索
            metadata_files = self._find_metadata_files(checklist_id)

            for metadata_file in metadata_files:
                metadata = json.loads(metadata_file.decoded_content.decode("utf-8"))

                # ユーザーIDとチェックリストIDが一致するか確認
                if (
                    metadata.get("checklist_id") == checklist_id
                    and metadata.get("user_id") == user_id
                ):
                    # メタデータファイルを削除
                    self.repo.delete_file(
                        path=metadata_file.path,
                        message=f"Delete metadata for checklist {checklist_id}",
                        sha=metadata_file.sha,
                        branch=settings.GITHUB_BRANCH,
                    )

                    # Markdownファイルを削除
                    markdown_path = metadata_file.path.replace("_metadata.json", ".md")
                    try:
                        file_or_files = self.repo.get_contents(
                            markdown_path, ref=settings.GITHUB_BRANCH
                        )
                        if isinstance(file_or_files, list):
                            logger.warning(f"Path {markdown_path} is a directory, not a file")
                        else:
                            markdown_file = file_or_files  # 型を絞り込み
                            self.repo.delete_file(
                                path=markdown_path,
                                message=f"Delete checklist {checklist_id}",
                                sha=markdown_file.sha,
                                branch=settings.GITHUB_BRANCH,
                            )
                    except GithubException:
                        logger.warning(f"Markdown file not found: {markdown_path}")

                    logger.info(f"Deleted checklist: {checklist_id}")
                    return True

            logger.warning(f"Checklist not found for deletion: {checklist_id}")
            return False

        except Exception as e:
            logger.error(f"Failed to delete checklist: {e}")
            raise GitHubSyncError(f"Failed to delete checklist: {e}") from e

    def _generate_markdown_content(self, checklist: TripChecklist) -> str:
        """チェックリストのMarkdownコンテンツを生成."""
        # Front Matterを追加
        front_matter = f"""---
type: "{checklist.purpose}_trip"
destination: "{checklist.destination}"
dates:
  start: "{checklist.start_date.isoformat()}"
  end: "{checklist.end_date.isoformat()}"
status: "{checklist.status}"
checklist_progress: {checklist.completion_percentage:.2f}
template_used: "{checklist.template_used or "manual"}"
---

"""

        return front_matter + checklist.to_markdown()

    def _parse_markdown_to_checklist(
        self, markdown_content: str, metadata: dict[str, Any]
    ) -> TripChecklist:
        """MarkdownコンテンツからTripChecklistオブジェクトを復元."""
        # TODO: 実装が必要
        # この実装は複雑になるため、別途詳細な実装が必要
        raise NotImplementedError("Markdown parsing is not yet implemented")
