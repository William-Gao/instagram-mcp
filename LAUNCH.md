# Launch playbook for instagram-mcp

This file is for the author's reference only - delete or .gitignore before posting if you want.

---

## Hacker News (Show HN) — primary

**Title** (HN is strict, ~80 char limit, no clickbait, no emojis):

```
Show HN: Instagram MCP server that works without a Facebook Page
```

Alternates:
- `Show HN: An open-source Instagram MCP server using the Instagram Login API`
- `Show HN: Instagram MCP for Claude/Cursor (no Facebook Page needed)`

**URL field**: `https://github.com/William-Gao/instagram-mcp`

**Post body** (HN doesn't render markdown well; keep it plain):

```
Hey HN — I built this because there was a gap in the MCP ecosystem.

When I tried to give Claude access to my Instagram account, I found that
every existing Instagram MCP server fell into one of two categories:

1. Servers using the Facebook Graph API path. These require linking your IG
   to a Facebook Page and using an EAA-prefixed token. Fine if you have a
   business setup, painful otherwise.

2. Servers using instagrapi (username/password login + private API scraping).
   These can — and do — get accounts banned.

Meta launched the "Instagram API with Instagram Login" flow in July 2024
specifically so creators can call the official API without a Facebook Page,
using IGAA-prefixed tokens via graph.instagram.com. As of this week, the
only MCP server supporting that flow exposed 4 tools.

So I built one with 27. 24 of them have been verified live against a real
account (mine). 3 are stubs that return a clear "this endpoint doesn't exist
on graph.instagram.com" error rather than silently failing — those features
are genuinely impossible without the Facebook Graph API path, and the
README points you at the right MCPs for those use cases.

What's covered: profile, media (read + insights), publishing (image / video /
Reel / carousel with container polling), comment management (post / reply /
delete / hide / toggle), account insights, and DMs (gated behind Meta App
Review for Advanced Access, like everything else in that space).

Stack: Python 3.10+, FastMCP, httpx. MIT licensed.

Happy to answer questions about the Instagram Login API gotchas — there are
a lot of them and most aren't well-documented.

https://github.com/William-Gao/instagram-mcp
```

**Best time to post**: Tue–Thu, 9am-10am Eastern (peak HN traffic). Avoid Mondays (queue clogged) and Fridays/weekends (low engagement).

**Watch for early traction**: First 90 minutes determine front-page potential. Reply to every comment within the first 2 hours.

---

## Reddit

### r/LocalLLaMA

**Title**: `Instagram MCP server using the official Instagram Login API (no Facebook Page, no scraping)`

**Body**:
```
I built this to fill a gap I hit while wiring up my IG account to Claude.

Most existing Instagram MCP servers either require a linked Facebook Page
(graph.facebook.com path) or use instagrapi-style private APIs that can get
accounts banned. Meta has had an "Instagram API with Instagram Login" flow
since mid-2024 that uses graph.instagram.com directly — but the only MCP
server supporting it had 4 tools.

This one has 27 (24 verified live). MIT licensed. Python + FastMCP.

Coverage: profile, media + insights, publishing (image/video/Reel/carousel),
comment management, account insights, and DMs (latter gated behind Meta App
Review like everywhere else).

https://github.com/William-Gao/instagram-mcp

Comparison table with the other Instagram MCPs is in the README. PRs welcome.
```

### r/ClaudeAI

**Title**: `Open-sourced an Instagram MCP server that works with Claude Desktop/Code without needing a Facebook Page`

(Same body, framed more for Claude users.)

### r/mcp (if it exists / when it grows)

Same content.

---

## X / Twitter

**Thread (5-7 tweets):**

1/ I open-sourced an Instagram MCP server that works with @AnthropicAI Claude (Desktop, Code) and any other MCP client without needing a Facebook Page.

The gap: every other IG MCP either requires a linked FB Page or uses private API scraping. Mine uses the official Instagram Login API.

https://github.com/William-Gao/instagram-mcp

2/ Background: Meta launched "Instagram API with Instagram Login" in July 2024. It uses IGAA-prefixed tokens via graph.instagram.com, no FB Page needed.

But until now the only MCP server supporting that flow exposed 4 tools. I built one with 27.

3/ Tool coverage:
- Profile + media browsing
- Insights (account-level + per-media)
- Publishing: image, video, Reel, carousel with container-status polling
- Comment management: post, reply, hide, delete, toggle comments on a post
- DMs (behind Meta App Review)

4/ 24/27 verified live against a real IG account. The 3 unsupported tools (business_discovery, hashtag search) genuinely don't exist on graph.instagram.com — they're stubs that return a clear "use a FB-Graph MCP for this" error, and the README points you at the right ones.

5/ Stack: Python 3.10+, FastMCP (`mcp>=1.2`), httpx. MIT licensed.

Configs included for Claude Desktop, Claude Code, and Cursor.

If you've been frustrated trying to wire IG into your agent, give it a spin: https://github.com/William-Gao/instagram-mcp

6/ This is a community-first project — PRs welcome, especially:
- Test coverage
- OAuth helpers (currently you BYO token)
- Better error messages when Meta rotates an endpoint
- Support for new IG Platform features as Meta ships them

---

## Tips for the launch day

1. Make sure your GitHub profile bio/links look polished — visitors will click through.
2. Pin a tweet linking the repo for the first 24h.
3. If HN comments roll in, respond fast and avoid getting defensive about limitations. The 🚫 stubs are HN-bait — own the trade-off.
4. If you get >50 stars in the first day, consider submitting to:
   - Awesome MCP Servers list (https://github.com/punkpeye/awesome-mcp-servers) — PR an entry
   - `mcpservers.org`
5. Track issues for any "can you also..." asks and ship them within the first week to keep momentum.
