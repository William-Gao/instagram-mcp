# Security Policy

## Supported versions

This project is pre-1.0; only the latest `main` receives security fixes.

| Version | Supported |
|---------|-----------|
| `main` (latest) | ✅ |
| older tags | ❌ |

## Reporting a vulnerability

Please report security issues **privately** — do not open a public issue for
anything exploitable.

- Use GitHub's **[Private vulnerability reporting](https://github.com/William-Gao/instagram-mcp/security/advisories/new)**
  (Security → Report a vulnerability), or
- open a regular issue **only** for non-sensitive, low-risk concerns.

Please include repro steps and affected version/commit. We aim to acknowledge
within a few days.

## Handling credentials (important for users)

This server handles **Instagram/Facebook access tokens**, which grant direct API
access to a connected account. To use it safely:

- Keep tokens in a local, **gitignored `.env`** (this repo ignores `.env`). Never
  commit tokens, and never paste them into issues, logs, or screenshots.
- Treat the **Facebook App Secret** as highly sensitive; prefer extending tokens
  via Meta's own tooling so the secret never leaves Meta's UI. Rotate it (Meta
  dashboard → App Settings → Basic) if it may have been exposed.
- Long-lived Instagram tokens expire after ~60 days; Facebook Page tokens are
  effectively non-expiring but data access lapses (~90 days). A dead token can
  only be replaced via interactive re-authorization — there is no programmatic
  recovery.
- This server uses **only official Meta APIs** (no scraping / private mobile API),
  which keeps connected accounts in good standing.
