# Multi-Platform Posting API

A FastAPI service that publishes one short message (max 200 characters, exactly one CTA link) to **6 platforms at once**: Telegram, Mastodon, Bluesky, GitHub Gist, Dev.to and Discord. Each platform is handled on its own, so if one fails the others still post.

## Features
- `POST /posting` validates the message, then posts to every platform **concurrently** (`asyncio.gather`)
- Validation: max 200 characters, exactly one CTA link, valid URL, with clear 422 errors
- Per-platform result: platform, status, posted URL, public access, posting time and error
- Failures are isolated: a bad token, timeout or API error on one platform never stops the rest
- Credentials only from environment variables (`.env`)
- `GET /health` shows which platforms are configured
- Swagger docs at `/docs`, plus pytest tests

## Platforms
| Platform | API | Auth | Public |
|---|---|---|---|
| Telegram | Bot API `sendMessage` | Bot token | Yes |
| Mastodon | `POST /api/v1/statuses` | Bearer token | Yes |
| Bluesky | AT Protocol `createSession` + `createRecord` | App password, then JWT | Yes |
| GitHub Gist | `POST /gists` | Personal access token (gist scope) | Yes |
| Dev.to | `POST /api/articles` | `api-key` header | Yes |
| Discord | Webhook | Webhook URL | No (server members only) |

X/Twitter (paid API), LinkedIn and Meta (app review) and Reddit (API approval) were left out because they can't be used without paid access or approval.

## Project structure
```
app/
  main.py               # FastAPI app, routes, validation error handler
  schemas.py            # Request/response models and validation rules
  config.py             # Settings from environment / .env
  platforms/
    base.py             # BasePlatform: shared error handling (template method)
    telegram.py  mastodon.py  bluesky.py  github_gist.py  devto.py  discord.py
  services/
    posting_service.py  # Runs all platforms concurrently
tests/test_posting.py   # Validation and failure-isolation tests
scripts/test_platform.py  # Post to one platform, for debugging
screenshots/            # Proof of the working implementation
```

**Design:** every platform extends `BasePlatform` and implements only `is_configured()` and `publish()`. `BasePlatform.post()` turns any error into a `failed` result, so one platform can never crash the request. To add a platform, write one class and add it to `PLATFORM_CLASSES`.

## Setup
```bash
git clone https://github.com/Savan7002/auto_post_system.git
cd auto_post_system
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # then add your keys
```
A platform with no keys is skipped and reported as `failed: Not configured`; the others still run. Check which platforms are ready at http://localhost:4000/health.

## Getting the API keys
| Platform | Where to get it | `.env` keys |
|---|---|---|
| Telegram | Create a bot with @BotFather, create a **public** channel, and add the bot as a channel admin with "Post Messages" | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHANNEL` (e.g. `@my_channel`) |
| Mastodon | Preferences → Development → New application, scope `write:statuses` | `MASTODON_ACCESS_TOKEN` (`MASTODON_BASE_URL` if not mastodon.social) |
| Bluesky | Settings → Privacy and security → App passwords | `BLUESKY_HANDLE`, `BLUESKY_APP_PASSWORD` |
| GitHub Gist | Settings → Developer settings → Personal access tokens (classic), `gist` scope only | `GITHUB_TOKEN` |
| Dev.to | Settings → Extensions → DEV Community API Keys | `DEVTO_API_KEY` |
| Discord | Server Settings → Integrations → Webhooks → New Webhook | `DISCORD_WEBHOOK_URL` |

## Run
```bash
uvicorn app.main:app --host 0.0.0.0 --port 4000
```
Open http://localhost:4000/docs

## Sample request
```bash
curl -X POST http://localhost:4000/posting \
  -H "Content-Type: application/json" \
  -d '{"message": "My multi-platform posting API is live! https://github.com/Savan7002"}'
```

## Sample response: all succeeded
```json
{
  "message": "My multi-platform posting API is live! https://github.com/Savan7002",
  "total_platforms": 6,
  "succeeded": 6,
  "failed": 0,
  "results": [
    {
      "platform": "Telegram",
      "status": "success",
      "posted_url": "https://t.me/savan_test_posts/3",
      "public_access": true,
      "posted_at": "2026-11-19T19:09:30.536670Z",
      "error": null
    },
    {
      "platform": "Discord",
      "status": "success",
      "posted_url": "https://discord.com/channels/1573047496639516773/1573047497562128445/1573052619604103328",
      "public_access": false,
      "posted_at": "2026-11-19T19:09:31.045214Z",
      "error": null
    }
  ]
}
```
_(Shortened: Mastodon, Bluesky, GitHub Gist and Dev.to have the same shape. The full output is in the Swagger screenshot below.)_

All six `posted_at` times fall within about 1.3 seconds, which shows the platforms are called concurrently, not one after another.

## Sample response: one platform failed, the others still posted
GitHub Gist was given a wrong token on purpose. The other 5 platforms still posted.
```json
{
  "message": "Learn Python in 30 days! https://www.python.org/",
  "total_platforms": 6,
  "succeeded": 5,
  "failed": 1,
  "results": [
    {
      "platform": "Telegram",
      "status": "success",
      "posted_url": "https://t.me/savan_test_posts/4",
      "public_access": true,
      "posted_at": "2026-11-20T05:38:15.648252Z",
      "error": null
    },
    {
      "platform": "GitHub Gist",
      "status": "failed",
      "posted_url": null,
      "public_access": false,
      "posted_at": null,
      "error": "HTTP 401: Bad credentials"
    }
  ]
}
```
_(Shortened: Mastodon, Bluesky, Dev.to and Discord succeeded, as shown in the screenshot below.)_

## Sample validation error (422)
```json
{
  "detail": "Validation failed",
  "errors": [{"field": "message", "message": "Message must contain exactly one CTA link, but 2 were found: https://a.com, https://b.com"}]
}
```

## Tests
```bash
python -m pytest -v
```
The tests use fake platforms, so they never call real APIs and need no keys. They cover the validation rules, unconfigured platforms, and a crashing platform that must not stop the others.

## Debugging a single platform
To test one integration on its own, without starting the server:
```bash
python scripts/test_platform.py <telegram|mastodon|bluesky|gist|devto|discord>
```
It posts a test message to that platform only and prints the result.

## Screenshots
![Swagger response](screenshots/swagger.png)
![One platform failed](screenshots/partial-failure.png)
![Terminal log](screenshots/terminal-log.png)
![Live posts](screenshots/posts.png)

## Security
- No credentials in the code or the repo; `.env` is git-ignored
- Narrow scopes: gist-only GitHub token, `write:statuses` on Mastodon, an app password on Bluesky
- The httpx request logger is set to WARNING, because some APIs put tokens in URLs