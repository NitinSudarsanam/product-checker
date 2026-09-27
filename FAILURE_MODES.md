# Failure Modes

Known ways the system can fail or give wrong answers, grouped by component. Items already fixed in the code are listed at the end with where the fix lives.

Severity: **CRIT** (data exposure or outage) / **HIGH** (feature broken) / **MED** (degraded or wrong results) / **LOW** (minor).

---

## Open

### Scraper: fetching

| # | Mode | Sev | Notes |
|---|------|-----|-------|
| 1.1 | ScrapingBee key invalid, out of credits, or rate limited (401 / 402 / 429) | MED | Logged, then falls back to the next method. Easy to miss that credits ran out |
| 1.2 | ScrapingBee returns stale or pre-render HTML | MED | Only Wayfair gets a Playwright second opinion |
| 1.3 | Residential proxy still blocked | MED | Aggressive sites (Nike, etc.) block residential IPs too |
| 1.4 | `country_code=us` for non-US product pages | MED | Region redirects or "not available in your country" pages |
| 2.1 | Playwright browsers not installed | HIGH | Launch error, the result is `error` |
| 2.2 | **Firefox not installed in the Docker image** | HIGH | `scraper.py` uses Firefox for Staples and Office Depot, but `backend/Dockerfile` only runs `playwright install chromium` |
| 2.3 | New browser launched per URL | MED | ~200 MB each. Capped by worker concurrency and `PLAYWRIGHT_MAX_CONCURRENT`, but not pooled |
| 2.4 | Stealth scripts detected (Cloudflare, PerimeterX, Akamai) | MED | Block page leads to an `error` result |
| 2.5 | Docker fingerprint mismatch | HIGH | Windows user agent on Linux Chromium, headless, few fonts, software graphics. Blocked far more than local runs. See TROUBLESHOOTING |
| 2.6 | Saved cookies expire or are fingerprint-bound | MED | `storage_state/*.json` stops helping without warning. Re-run `bootstrap_state.py` |
| 3.1 | Plain HTTP gets a JavaScript shell | MED | No buttons in the HTML means a false `unavailable` when it's the only method that worked |
| 3.2 | Plain HTTP rate-limited (429), no retry | LOW | |

### Scraper: detection

| # | Mode | Sev | Notes |
|---|------|-----|-------|
| 4.1 | Site not in `detection_rules.json` | MED | Falls back to generic selectors and text, which may miss |
| 4.2 | Generic text matches the wrong control | LOW | e.g. "Add to registry" matching partial "add to" rules |
| 4.3 | Button is an image with no text or alt | MED | Not detected |
| 4.4 | Non-English pages | MED | All patterns are English |
| 4.5 | "Pre-order", "Sign in to see price", region-locked buttons | MED | Can be misclassified either way |
| 4.6 | Variant probing hits its cap (25 to 30 options, 30 to 45 s) | MED | Unprobed variants are ignored, so a product with stock only in a later variant can read `unavailable` |
| 4.7 | Out-of-stock wording for another variant or seller inside the product area | MED | `unavailability_override` gives a false `unavailable` |
| 4.8 | Block-page phrases appear on a real page | LOW | e.g. "page not found" in page copy leads to a false `error` |

### Backend and worker

| # | Mode | Sev | Notes |
|---|------|-----|-------|
| 5.1 | No guard against overlapping scans | HIGH | `POST /api/scan/run` always creates a new job. Double clicks or scripts can queue the same URLs many times |
| 5.2 | No way to cancel a job | MED | Workers honour `status: "cancelled"`, but no endpoint sets it |
| 5.3 | `error_message` returns raw exception text | LOW | Can leak internal paths or hostnames to the client |
| 5.4 | Module-level `asyncio.Semaphore` shared across `asyncio.run()` calls | MED | Fine with the default prefork pool (one task per process). With `--pool=threads`, two tasks waiting on it can raise "bound to a different event loop" |
| 5.5 | `/health` doesn't check Redis or workers | LOW | Reports healthy while scans can't run |
| 5.6 | Redirects aren't checked against the SSRF blocklist | MED | URLs are validated when added, but a public URL can redirect the browser to an internal address |

### Database

| # | Mode | Sev | Notes |
|---|------|-----|-------|
| 6.1 | MongoDB down | CRIT | API starts but `/health` is `degraded`, and all reads and writes fail |
| 6.2 | **MongoDB and Redis published on all interfaces with no auth** | CRIT | `docker-compose.yml` maps 27017 and 6379 to the host. Anyone who can reach the machine can read or modify data |
| 6.3 | `scan_results` and `scan_jobs` grow without limit | MED | Only `logs` has a TTL |
| 6.4 | Network failure during a worker write | MED | Result lost, no retry |

### Frontend

| # | Mode | Sev | Notes |
|---|------|-----|-------|
| 7.1 | Polling stops after 30 minutes | LOW | Very large scans keep running. Refresh to see results |
| 7.2 | `NEXT_PUBLIC_API_URL` missing at build time | HIGH | Falls back to `http://localhost:8080` with a console warning |
| 7.3 | Latest results capped at 500 URLs | LOW | `getLatestResults(500)` |
| 7.4 | No virtualization for long lists | LOW | Slow rendering with thousands of URLs |

### Configuration

| # | Mode | Sev | Notes |
|---|------|-----|-------|
| 8.1 | Docker containers ignore `.env` | HIGH | Only `SCRAPINGBEE_API_KEY` is passed through. Other settings must go in `docker-compose.yml` |
| 8.2 | Some scraper settings are read only from the process environment | MED | `SCRAPER_SCREENSHOT_DIR`, `SCRAPER_STORAGE_STATE_DIR`, and `SCRAPER_RETRY_FRESH_CONTEXT` do nothing in `.env` |
| 8.3 | Dead settings | LOW | `SCRAPER_MAX_CONCURRENT` and `SCRAPER_USER_AGENT` are defined but unused |
| 8.4 | `SECRET_KEY` left as placeholder | LOW | Logged as a warning. Nothing uses it yet |

### Security

| # | Mode | Sev | Notes |
|---|------|-----|-------|
| 10.1 | No authentication on any endpoint | HIGH | Anyone who can reach the API can add, delete, or scan |
| 10.2 | No rate limit on `/api/scan/run` | HIGH | Easy resource exhaustion (browsers, ScrapingBee credits) |
| 10.3 | `storage_state/` holds live session cookies | HIGH | Git-ignored, but don't copy it into images or share it |
| 10.4 | URLs (possibly with personal data in query strings) are logged | MED | |

### Deployment and scripts

| # | Mode | Sev | Notes |
|---|------|-----|-------|
| 11.1 | `start-dev.bat` doesn't start Redis or the worker | HIGH | Scans stay `queued` forever |
| 11.2 | `start-dev.bat` assumes a conda env named `product-checker` | MED | |
| 11.3 | `start.bat` prints port 8000 | LOW | The API is on 8080 |
| 11.4 | Local Windows worker without `--pool=solo` / `threads` | HIGH | Celery's prefork pool doesn't work on Windows |
| 11.5 | `scripts/debug/*` import `fetch_dynamic_html` | LOW | That function no longer exists, so those scripts fail |

### Logging

| # | Mode | Sev | Notes |
|---|------|-----|-------|
| 12.1 | `RotatingFileHandler` does blocking I/O in async code | LOW | |
| 12.2 | File rotation race on Windows with several processes | LOW | API and worker can share `logs/app.log` |

---

## Fixed

| Was | Mode | Fix |
|-----|------|-----|
| Detector crashed on missing or malformed `detection_rules.json` | CRIT | Falls back to built-in rules (`detector.py`, `_FALLBACK_RULES`) |
| Scans ran as FastAPI background tasks and died with the API | HIGH | Moved to Celery workers with `task_acks_late` and `task_reject_on_worker_lost` (`celery_app.py`) |
| No per-URL timeout | HIGH | `asyncio.wait_for` plus Celery soft and hard limits (`scan_tasks.py`) |
| Frontend polled by timestamp, broke across time zones, capped at 100 results | MED | Polls `GET /api/scan/{job_id}/status`. Latest results limit raised to 500 |
| `CORS_ORIGINS` JSON parsed as comma-split | HIGH | Validator accepts JSON or CSV (`config.py`) |
| `.env` not found from other working directories | HIGH | Absolute path from the project root (`config.py`) |
| Relative `LOG_FILE` scattered logs | LOW | Resolved against the project root |
| Unknown `.env` keys rejected | LOW | `extra: "ignore"` |
| Port drift between 8000 and 8080 | MED | Backend, frontend, and `.env.example` all use 8080 |
| No MongoDB indexes | MED | Created at startup (`database.py`) |
| Logs collection grew forever | MED | 30-day TTL index |
| URL delete missed scan results (`url_id` type mismatch) | MED | `url_id` stored and queried as a string |
| SSRF via `file://`, localhost, private IPs | HIGH | Rejected when URLs are added (`schemas.py`, `_is_ssrf_unsafe`). Redirects are still open (5.6) |
| CORS allowed all methods | MED | Limited to GET, POST, DELETE, OPTIONS |
| Divs acting as buttons skipped | MED | `<div>`/`<span>` with `role="button"` or btn/button classes are candidates |
| Button wait matched "Add to wishlist" | MED | Waits for "Add to Cart" / "Add to Bag" and specific add-to-cart hooks |
| Disabled or loading buttons counted as available | MED | HTML checks for disabled, `aria-busy`, and out-of-stock text, plus a live-page clickable check |
| Default variant out of stock but others in stock | MED | Variant probing (selects, radios, listboxes) |
| `playwright-stealth`, `scrapingbee` missing from requirements | HIGH | Added to `backend/requirements.txt` |
| `HEADLESS=False` default opened windows on servers | LOW | Default is `true` |
| Windows selector event loop broke Playwright | HIGH | Proactor policy set in `scraper.py`, `main.py`, `run.py` |

## Suggested next fixes

1. Remove the MongoDB and Redis `ports:` from `docker-compose.yml` or add auth (6.2).
2. Add `playwright install firefox` to `backend/Dockerfile` (2.2).
3. Refuse `POST /api/scan/run` while a job is queued or running, and add a cancel endpoint (5.1, 5.2).
4. Add basic auth and a rate limit to the API (10.1, 10.2).
5. Make the Docker browser fingerprint consistent: Linux user agent, fonts, and Xvfb or real Chrome (2.5).
6. Fix `start-dev.bat` to start Redis and the worker, and `start.bat`'s port message (11.1, 11.3).
