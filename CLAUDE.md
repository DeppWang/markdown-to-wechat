# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Does

Publishes Markdown articles from Obsidian notes and Hexo blog posts to WeChat Official Account (公众号) as draft articles. Converts Markdown to WeChat-compatible styled HTML, uploads images to WeChat permanent media storage, and creates drafts via the WeChat API.

## Commands

```bash
# Setup
python3 -m venv venv && . venv/bin/activate
pip install markdown Pygments werobot pyquery requests

# Run
python3 sync.py                  # Hexo blog posts → WeChat drafts (last 7 days)
python3 obsidian_to_wechat.py    # Obsidian notes → WeChat drafts (last 3 days, tagged only)
```

Required environment variables: `WECHAT_APP_ID`, `WECHAT_APP_SECRET`.

Hard-coded paths to update for your system: `HEXO_BLOG_POST_PATH`, `OBSIDIAN_PATH`, `BLOG_URL`, `AUTHOR`.

## Architecture

**Two entry points, one shared library:**

- `sync.py` — Core library + Hexo entry point. Owns all rendering, image upload, WeChat API, and caching logic. Scans `HEXO_BLOG_POST_PATH` for `.md` files modified in the last 7 days.
- `obsidian_to_wechat.py` — Obsidian entry point. Imports helpers from `sync.py`. Scans `OBSIDIAN_PATH` for `.md` files modified in the last 3 days that have the `Obsidian-to-Wechat-Tag` tag in their first line.

**Processing pipeline (both entry points):**
1. Scan directory for recently modified `.md` files
2. Check `cache.bin` (pickle) to skip already-processed files (MD5 digest)
3. Extract images from markdown, download, and upload to WeChat permanent media
4. Convert markdown → HTML via `markdown` library with `codehilite`/`tables`/`toc` extensions
5. Apply WeChat-compatible styling using `assets/*.tmpl` templates (paragraph, code, heading, link, figure styles)
6. Replace image URLs with uploaded WeChat media URLs
7. POST to `https://api.weixin.qq.com/cgi-bin/draft/add` to create draft
8. Update cache with file digest

**Key class:** `NewClient` in `sync.py` manages WeChat API access tokens with 2-hour expiry caching.

## Templates

HTML/CSS templates live in `assets/*.tmpl` and are loaded by `gen_css()`. Keep filenames stable. If you change styling in scripts, update the matching template and vice versa.

## Testing

No automated tests. Validate by running scripts locally and checking generated `origin.html` (raw) and `result.html` (styled). If adding tests, place under `tests/` as `test_*.py`.

## Code Style

Python 3, 4-space indentation, `snake_case` functions/variables, `UPPER_SNAKE_CASE` constants. Commit messages are short and imperative (e.g., "fix code color", "update code").
