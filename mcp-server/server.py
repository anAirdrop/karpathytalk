"""MCP server for KarpathyTalk.

Wraps the public read-only JSON/markdown API at karpathytalk.com so that
LLM agents can browse users, posts, and threads through MCP tools.

The KarpathyTalk API is read-only and public, so this server performs no
authentication and never writes. See docs.md in the repo root for the full
API surface.
"""

from __future__ import annotations

import os
from typing import Any
from urllib.parse import urlencode

import httpx
from mcp.server.fastmcp import FastMCP

BASE_URL = os.environ.get("KARPATHYTALK_BASE_URL", "https://karpathytalk.com").rstrip("/")
USER_AGENT = "karpathytalk-mcp/0.1 (+https://github.com/karpathy/KarpathyTalk)"
TIMEOUT = httpx.Timeout(20.0, connect=10.0)

mcp = FastMCP("karpathytalk")


def _client() -> httpx.Client:
    return httpx.Client(
        base_url=BASE_URL,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        timeout=TIMEOUT,
        follow_redirects=True,
    )


def _get_json(path: str, params: dict[str, Any] | None = None) -> Any:
    with _client() as c:
        r = c.get(path, params=params)
        r.raise_for_status()
        return r.json()


def _get_text(path: str, accept: str = "text/markdown, text/plain, */*") -> str:
    with _client() as c:
        r = c.get(path, headers={"Accept": accept})
        r.raise_for_status()
        return r.text


# ---------- Tools ----------


@mcp.tool()
def get_user(username: str) -> dict[str, Any]:
    """Fetch a KarpathyTalk user profile as JSON.

    Args:
        username: The GitHub-style username, e.g. "karpathy".

    Returns:
        The user object with id, display_name, avatar_url, counts, etc.
    """
    return _get_json(f"/api/users/{username}")


@mcp.tool()
def get_user_markdown(username: str) -> str:
    """Fetch a lightweight markdown representation of a user profile."""
    return _get_text(f"/user/{username}/md")


@mcp.tool()
def get_post(post_id: int) -> dict[str, Any]:
    """Fetch a single post as JSON, including author and social counts.

    Args:
        post_id: Numeric post id.
    """
    return _get_json(f"/api/posts/{post_id}")


@mcp.tool()
def get_post_markdown(post_id: int, raw: bool = False) -> str:
    """Fetch a post as markdown.

    Args:
        post_id: Numeric post id.
        raw: If True, return only the raw post body. If False (default),
            return the markdown document with frontmatter.
    """
    suffix = "raw" if raw else "md"
    return _get_text(f"/posts/{post_id}/{suffix}")


@mcp.tool()
def list_posts(
    author: str | None = None,
    has_parent: bool | None = None,
    parent_post_id: int | None = None,
    before: int | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    """List posts in reverse chronological order with optional filters.

    Args:
        author: Filter to posts by this username.
        has_parent: If False, only root posts (not replies). If True, only replies.
        parent_post_id: Only direct children of this post id (i.e. a thread).
        before: Paginate: return posts older than this post id.
        limit: Max number of posts to return (server caps at 100).

    Returns:
        The JSON response from /api/posts.
    """
    params: dict[str, Any] = {}
    if author is not None:
        params["author"] = author
    if has_parent is not None:
        params["has_parent"] = "true" if has_parent else "false"
    if parent_post_id is not None:
        params["parent_post_id"] = parent_post_id
    if before is not None:
        params["before"] = before
    if limit is not None:
        params["limit"] = limit
    return _get_json("/api/posts", params=params or None)


@mcp.tool()
def get_thread(post_id: int, limit: int | None = None) -> dict[str, Any]:
    """Convenience: fetch a post and its direct replies.

    Args:
        post_id: Root post id.
        limit: Max number of replies to return.

    Returns:
        {"post": <post>, "replies": <list_posts response>}
    """
    post = get_post(post_id)
    replies = list_posts(parent_post_id=post_id, limit=limit)
    return {"post": post, "replies": replies}


@mcp.tool()
def get_user_feed_rss(username: str) -> str:
    """Fetch a user's RSS feed XML."""
    return _get_text(f"/user/{username}/feed.xml", accept="application/rss+xml, application/xml, */*")


@mcp.tool()
def get_docs() -> str:
    """Fetch the KarpathyTalk API docs as markdown."""
    return _get_text("/docs.md")


# ---------- Resources ----------


@mcp.resource("karpathytalk://docs")
def docs_resource() -> str:
    """The KarpathyTalk API documentation."""
    return _get_text("/docs.md")


@mcp.resource("karpathytalk://users/{username}")
def user_resource(username: str) -> str:
    """A user profile as markdown."""
    return _get_text(f"/user/{username}/md")


@mcp.resource("karpathytalk://posts/{post_id}")
def post_resource(post_id: str) -> str:
    """A post as markdown (with frontmatter)."""
    return _get_text(f"/posts/{post_id}/md")


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
