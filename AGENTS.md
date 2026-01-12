# Repository Guidelines

## Project Structure & Module Organization
`sync.py` is the main script for pushing Hexo markdown posts to WeChat and owns most rendering helpers. `obsidian_to_wechat.py` publishes Obsidian notes and reuses helpers from `sync.py`. Template snippets live in `assets/*.tmpl` and are loaded by `gen_css`, so keep filenames stable. Generated artifacts like `origin.html`, `result.html`, and `cache.bin` are local outputs and should remain untracked.

## Build, Test, and Development Commands
- `python3 -m venv venv` and `. venv/bin/activate` to create and activate a local environment.
- `pip install markdown Pygments werobot pyquery requests` to install runtime dependencies.
- `python3 sync.py` pulls posts from `HEXO_BLOG_POST_PATH` and uploads recent items (last 7 days) to WeChat drafts.
- `python3 obsidian_to_wechat.py` scans `OBSIDIAN_PATH` for recent notes (last 3 days) and uploads tagged entries.

Set `WECHAT_APP_ID` and `WECHAT_APP_SECRET` in your environment. Update hard-coded paths or metadata (for example, `HEXO_BLOG_POST_PATH`, `OBSIDIAN_PATH`, `BLOG_URL`, `AUTHOR`) before running locally.

## Coding Style & Naming Conventions
Use Python 3 with 4-space indentation. Prefer snake_case for functions and variables and UPPER_SNAKE_CASE for module constants. Keep templates minimal and parameterized; avoid inline HTML changes in the scripts unless you also update the matching template.

## Testing Guidelines
There are no automated tests yet. Validate changes by running the scripts locally, checking `origin.html`/`result.html`, and confirming a WeChat draft is created. If you add tests, place them under `tests/` and name files `test_*.py`.

## Commit & Pull Request Guidelines
Commit history uses short, imperative summaries (for example, "Update code" or "fix code color"). Keep messages concise and focused. Pull requests should include a brief summary, commands run, and any configuration changes (env vars, path constants, or template edits). Include screenshots or HTML snippets when altering templates.

## Security & Configuration Tips
Never commit tokens, app secrets, or personal paths. Use environment variables for credentials and be mindful of WeChat API rate limits and media upload quotas.
