# KarpathyTalk MCP Server

A [Model Context Protocol](https://modelcontextprotocol.io) server that wraps
the public read-only [KarpathyTalk](https://karpathytalk.com) API so MCP-aware
clients (Claude Desktop, Claude Code, etc.) can browse users, posts, and
threads as tools and resources.

The KarpathyTalk API is read-open and write-human: this server only performs
`GET` requests, needs no credentials, and cannot post on your behalf.

## Tools

- `get_user(username)` — user profile JSON
- `get_user_markdown(username)` — user profile as markdown
- `get_post(post_id)` — single post JSON (includes author + counts)
- `get_post_markdown(post_id, raw=False)` — post markdown (`/md` or `/raw`)
- `list_posts(author?, has_parent?, parent_post_id?, before?, limit?)` —
  filtered feed of posts
- `get_thread(post_id, limit?)` — a post plus its direct replies
- `get_user_feed_rss(username)` — raw RSS XML
- `get_docs()` — the KarpathyTalk API docs as markdown

## Resources

- `karpathytalk://docs`
- `karpathytalk://users/{username}`
- `karpathytalk://posts/{post_id}`

## Install

Requires Python 3.10+.

```bash
cd mcp-server
pip install -r requirements.txt
```

Or with `uv`:

```bash
uv pip install -r mcp-server/requirements.txt
```

## Run

The server speaks MCP over stdio:

```bash
python mcp-server/server.py
```

Point at a different host (e.g. a local dev instance) with:

```bash
KARPATHYTALK_BASE_URL=http://localhost:8080 python mcp-server/server.py
```

## Wire it into Claude Desktop

Add an entry to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "karpathytalk": {
      "command": "python",
      "args": ["/absolute/path/to/KarpathyTalk/mcp-server/server.py"]
    }
  }
}
```

## Wire it into Claude Code

```bash
claude mcp add karpathytalk -- python /absolute/path/to/KarpathyTalk/mcp-server/server.py
```

## Example prompts

- "Use karpathytalk to show me karpathy's latest root posts."
- "Fetch post 4 and all of its direct replies."
- "Give me the raw markdown of post 12."
