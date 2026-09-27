# Architecture

## Components

```
Browser (localhost:3000)
   │  HTTP, polls job status every 5 s
   ▼
Frontend ── Next.js + React (frontend/src)
   │  axios → NEXT_PUBLIC_API_URL (localhost:8080)
   ▼
Backend API ── FastAPI (backend/app)
   │  reads/writes MongoDB (Motor, async)
   │  POST /api/scan/run → creates scan_jobs doc, sends Celery task
   ▼
Redis ── Celery broker + result backend
   │
   ▼
Worker ── Celery (backend/app/tasks/scan_tasks.py)
   │  one scrape_one_url task per URL
   │  calls scraper.scrape_url(), writes results with PyMongo (sync)
   ▼
Scraper ── scraper/scraper.py + scraper/detector.py
   │  Playwright (Chromium, Firefox for a few sites) → ScrapingBee → plain HTTP
   ▼
Retailer product pages
```

The API process imports the scraper package but never runs a scrape itself. All scraping happens in worker processes, so a slow or hung page can't tie up the API.

## Scan lifecycle

1. **Start.** The frontend calls `POST /api/scan/run`, optionally with a list of `url_ids`. The API checks the IDs, inserts a `scan_jobs` document with `status: "queued"` and a new `job_id`, sends the `enqueue_scan` Celery task, and returns the `job_id` right away.
2. **Fan out.** `enqueue_scan` sets the job to `running`, loads the URLs, records `total_urls`, and queues one `scrape_one_url` task per URL.
3. **Scrape.** Each `scrape_one_url`:
   - skips the work if the job was cancelled,
   - runs `scrape_url()` inside `asyncio.wait_for` with a per-URL time budget,
   - inserts a `scan_results` document (including errors and timeouts),
   - increments the job's counters (`completed`, `success` or `error`, `available_count`, `unavailable_count`, `method_counts.<method>`),
   - recalculates `rate_urls_per_sec`, `eta_seconds`, and `availability_summary`,
   - marks the job `done` once `completed == total_urls`.
4. **Poll.** The frontend calls `GET /api/scan/{job_id}/status` every 5 seconds (for up to 30 minutes) and shows progress. When the job reaches `done`, `failed`, or `cancelled`, it reloads `GET /api/scan/results/latest`.

### Timeouts

Three layers stop a single URL from running forever:

| Layer | Default | Where |
|-------|---------|-------|
| Page navigation | `SCRAPER_TIMEOUT` (30 s), 5× for Amazon and Walmart | `_playwright_scrape` |
| Variant probing | 45 s (30 s for Amazon and Walmart) | `_playwright_scrape` |
| Whole URL | `max(timeout + 60, timeout × 12 + 180)` = 540 s | `scrape_one_url` (`asyncio.wait_for`) |
| Celery soft / hard limit | 1080 s / 1200 s | `scrape_one_url` task options |

Celery is configured with `task_acks_late` and `task_reject_on_worker_lost`, so if a worker process dies mid-task, the task goes back on the queue instead of disappearing.

## Scraper

`scrape_url(url)` in `scraper/scraper.py`:

1. **Fetch HTML.** Tries each method until one returns a page that isn't a block page:
   - **Playwright** (default first). Launches Chromium (Firefox for Staples and Office Depot, which hit HTTP/2 errors in Chromium), applies stealth scripts, loads saved cookies from `scraper/storage_state/<domain>.json`, skips images, fonts, and media, waits for a buy button, and grabs the HTML. It also records whether a buy button is actually clickable in the live page, then probes variants. If blocked, it retries once without saved cookies, and for Walmart and Target once more through ScrapingBee's proxy.
   - **ScrapingBee** (only if `SCRAPINGBEE_API_KEY` is set). Returns rendered HTML from a residential IP. No variant checks.
   - **Plain HTTP** (aiohttp). No JavaScript, no variant checks.
   - With `SCRAPER_SCRAPINGBEE_FIRST=true`, ScrapingBee is tried before Playwright.
2. **Block check.** `_looks_blocked_html()` looks for phrases like "robot or human", "captcha", "access denied", and "page not found". A match makes the result `error` with `error_message: "blocked:<phrase>"`.
3. **Detect.** `detector.detect_all_buttons()` parses the HTML and decides `add_to_cart`, `buy_now`, and `status`.
4. **Combine.** Variant results win over HTML detection. The live-page button check can overrule the HTML. Wayfair results from ScrapingBee get a second opinion from Playwright. See [DETECTION_EXPLAINED.md](DETECTION_EXPLAINED.md).

Concurrency inside one worker process is capped by semaphores: `PLAYWRIGHT_MAX_CONCURRENT` (2) browsers and `SCRAPINGBEE_MAX_CONCURRENT` (5) ScrapingBee calls.

## Database

MongoDB database `ubique_product_checker`. Indexes are created when the API starts (`backend/app/database.py`).

### `urls`

| Field | Type | Notes |
|-------|------|-------|
| `_id` | ObjectId | |
| `url` | string | unique index |
| `created_at` | datetime | |
| `group_name` | string, optional | |

### `scan_results`

One document per URL per scan. Indexed on `url`, `url_id`, and `scanned_at`.

| Field | Type | Notes |
|-------|------|-------|
| `url`, `url_id` | string | `url_id` is the string form of `urls._id` |
| `job_id` | string | the scan job that produced it |
| `scanned_at` | datetime | UTC |
| `status` | string | `available`, `unavailable`, or `error` |
| `add_to_cart`, `buy_now` | bool | |
| `error_message` | string, optional | e.g. `blocked:captcha`, `Scan timed out after 540s` |
| `response_time` | float | seconds |
| `scrape_method` | string | method behind the final result: `playwright`, `scrapingbee`, `static`, or `error` |
| `html_primary_source` | string | method that returned HTML first |
| `variants` | object | `{label: "available" \| "unavailable"}` |
| `variants_checked` | bool | |
| `unavailability_override` | bool | "out of stock" wording forced `unavailable` |

### `scan_jobs`

One document per scan. Unique index on `job_id`, plus `created_at` and `status`.

| Field | Notes |
|-------|-------|
| `job_id`, `status` | status is `queued`, `running`, `done`, `failed`, or `cancelled` |
| `created_at`, `started_at`, `finished_at`, `last_update_at` | |
| `total_urls`, `completed`, `success`, `error` | progress counters |
| `available_count`, `unavailable_count` | counted over successful scrapes only |
| `availability_summary` | `all_available`, `some_unavailable`, `none_available`, or `unknown` |
| `rate_urls_per_sec`, `eta_seconds` | |
| `method_counts` | `{scrapingbee, playwright, static}` |
| `url_ids` | IDs requested, or null for all URLs |

### `logs`

Application events (`event_type`, `details`, `timestamp`, `level`). A TTL index deletes entries after 30 days.

## Docker

`docker-compose.yml` runs five services on one bridge network:

| Service | Image / build | Host port |
|---------|---------------|-----------|
| `mongodb` | `mongo:7.0`, data in the `mongodb_data` volume | 27017 |
| `redis` | `redis:7.2-alpine` | 6379 |
| `backend` | `backend/Dockerfile`, runs uvicorn | 8080 → 8000 |
| `worker` | same image, runs `celery ... worker --concurrency=2` | — |
| `frontend` | `frontend/Dockerfile` | 3000 |

Both `backend` and `worker` mount `./scraper` at `/app/scraper`, so rule edits and saved cookies are shared with the host without rebuilding. The backend image is `python:3.11-slim` with Chromium's system libraries and `playwright install chromium`. It has no display server, so the browser always runs headless in Docker.

## Frontend

| File | Role |
|------|------|
| `src/pages/index.tsx` | page layout, scan start, job polling, notifications |
| `src/components/URLInput.tsx` | paste or type URLs, optional group name |
| `src/components/URLList.tsx` | stored URLs, delete |
| `src/components/ResultsTable.tsx` | latest result per URL, method badge, variants |
| `src/components/StatsCard.tsx` | totals from `/api/logs/stats` |
| `src/lib/api.ts` | axios client for every endpoint |
