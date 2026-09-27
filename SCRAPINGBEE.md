# ScrapingBee Integration

[ScrapingBee](https://www.scrapingbee.com/) is a paid scraping API. It fetches a page through residential proxies (home internet connections rather than data-center servers) and can render JavaScript before returning the HTML. Retailers that block data-center IP addresses often let these requests through.

It's optional. Set the key in `.env` to enable it, or leave it empty to skip ScrapingBee entirely:

```env
SCRAPINGBEE_API_KEY=your_key_here
SCRAPINGBEE_COUNTRY_CODE=us
```

In Docker, `docker-compose.yml` passes `SCRAPINGBEE_API_KEY` from `.env` to the backend and worker. Other ScrapingBee settings need to be added to the compose file.

## Where it fits

ScrapingBee is used in two ways.

**1. As a fetch method.** By default it's the second choice:

```
Playwright  →  ScrapingBee  →  plain HTTP
```

With `SCRAPER_SCRAPINGBEE_FIRST=true` the order becomes ScrapingBee → Playwright → plain HTTP. HTML that looks like a CAPTCHA or block page is discarded and the next method is tried.

**2. As a proxy for Playwright.** When Playwright is blocked on Walmart or Target (after its retry without saved cookies), it launches once more with ScrapingBee as its proxy (`proxy.scrapingbee.com:8886`). The browser still runs locally, so variant checks still work, but traffic leaves from a residential IP.

**Wayfair exception.** If ScrapingBee's HTML says a Wayfair product is available, Playwright re-checks the page and its answer wins. ScrapingBee's Wayfair snapshots have often been out of date.

## Methods compared

| | Playwright | ScrapingBee | Plain HTTP |
|---|---|---|---|
| Runs JavaScript | Yes (local browser) | Yes (in their cloud) | No |
| Gets past bot blocking | Stealth scripts and saved cookies | Residential IPs | Rarely |
| Variant checks | Yes | No | No |
| Typical time per URL | 10–60 s with variants | 5–15 s | 1–3 s |
| Cost | Local CPU and RAM | Credits per request | Free |

ScrapingBee returns one HTML snapshot. It can't click size or color options, so results that come from ScrapingBee have `variants_checked: false`.

## Request settings

From `fetch_scrapingbee_html()` in `scraper/scraper.py`:

| Parameter | All sites | Walmart and Target |
|-----------|-----------|--------------------|
| `render_js` | `true` | `true`, then `false` if the first attempt returns a 5xx |
| `premium_proxy` | `true` | `true` |
| `stealth_proxy` | — | `true` |
| `wait` | 3500 ms | 8000 ms |
| `block_resources` | `false` | `true` |
| `session_id` | — | random, to keep the same IP for a few minutes |
| `country_code` | `SCRAPINGBEE_COUNTRY_CODE` | same |
| `transparent_status_code`, `forward_headers` | `true` | `true` |

The Python SDK is synchronous, so calls run in a thread pool (`SCRAPINGBEE_MAX_WORKERS`, default 5) to avoid blocking the event loop. Each call times out after `max(15, SCRAPER_TIMEOUT × 3)` seconds.

## Credits

Premium proxies with JavaScript rendering cost about 25 credits per request, and stealth proxies (used for Walmart and Target) cost considerably more. Check ScrapingBee's current pricing and your dashboard before scanning large lists.

To limit spend or avoid 429 errors on low plans:

- `SCRAPINGBEE_MAX_CONCURRENT` (default 5): requests in flight at once
- `SCRAPINGBEE_RPS` (default 0 = off): requests-per-second cap

## Errors

ScrapingBee failures never fail the scan on their own. The scraper logs the problem and moves to the next method.

| Response | Behaviour |
|----------|-----------|
| 200 | HTML used |
| Non-200 with at least 20 KB of HTML | HTML still used. Block-page detection decides if it's real |
| 401 (bad key), 402 (out of credits), 429 (rate limited), other | Logged, next method tried |
| Timeout or exception | Logged, next method tried |

The API logs `ScrapingBee enabled (key_len=N)` or `ScrapingBee disabled` at startup, and the scraper logs `ScrapingBee=on/off` when imported. Check those if you're not sure the key is being picked up.
