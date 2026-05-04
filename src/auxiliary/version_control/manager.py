from __future__ import annotations

import asyncio
import contextlib
import logging
from pathlib import Path

from src.core.types.result import Err, Ok, Result

logger = logging.getLogger(__name__)


class VersionManager:
    def __init__(self, repo_path: Path = Path()) -> None:
        self._repo_path = repo_path
        self._enabled = False
        self._github_token: str | None = None
        self._auto_push = False
        self._git = None

    def initialize(self, github_token: str | None = None, auto_push: bool = False) -> Result[None]:
        try:
            import git
            try:
                self._git = git.Repo(self._repo_path)
            except git.InvalidGitRepositoryError:
                self._git = git.Repo.init(self._repo_path)
            self._github_token = github_token
            self._auto_push = auto_push
            self._enabled = True
            return Ok(None)
        except Exception as e:
            return Err(f"Git initialization failed: {e}")

    async def auto_commit(self, message: str) -> Result[None]:
        if not self._enabled or self._git is None:
            return Ok(None)
        try:
            await asyncio.to_thread(self._do_commit, message)
            return Ok(None)
        except Exception as e:
            logger.error(f"Auto commit failed: {e}")
            return Ok(None)

    def _do_commit(self, message: str) -> None:
        self._git.git.add(A=True)
        with contextlib.suppress(Exception):
            self._git.index.commit(message)

    async def push_to_remote(self) -> Result[None]:
        if not self._enabled or not self._auto_push:
            return Ok(None)
        try:
            await asyncio.to_thread(self._do_push)
            return Ok(None)
        except Exception as e:
            logger.error(f"Push failed: {e}")
            return Ok(None)

    def _do_push(self) -> None:
        if self._git and "origin" in [r.name for r in self._git.remotes]:
            self._git.remotes.origin.push()

    def create_issue(self, title: str, body: str) -> Result[None]:
        if not self._enabled or not self._github_token:
            return Ok(None)
        try:
            from github import Github
            g = Github(self._github_token)
            repo = g.get_repo(str(self._git.remote().url).replace("https://github.com/", "").replace(".git", ""))
            repo.create_issue(title=title, body=body)
            return Ok(None)
        except Exception as e:
            logger.error(f"Issue creation failed: {e}")
            return Ok(None)

    @property
    def is_enabled(self) -> bool:
        return self._enabled
