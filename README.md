# Ubique Product Checker

Tracks product availability by checking whether a product page shows a usable **Add to Cart** or **Buy Now** button. You add product URLs in a web UI, run a scan, and each URL is marked `available`, `unavailable`, or `error` (the page could not be read, usually because the retailer blocked the scraper).

## Services

| Service | Code | Port (host) |
|---------|------|-------------|
| Frontend (Next.js) | `frontend/` | 3000 |
| Backend API (FastAPI) | `backend/app/` | 8080 (container port 8000) |
| Worker (Celery) | `backend/app/tasks/scan_tasks.py` | — |
| MongoDB | stores URLs, scan results, scan jobs, logs | 27017 |
| Redis | Celery message queue | 6379 |

The API never scrapes pages itself. `POST /api/scan/run` creates a scan job and hands it to the worker through Redis, and the frontend polls the job for progress. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Quick start (Docker)

From `product-checker/`:

```powershell
copy .env.example .env
docker compose up -d --build
```

- UI: http://localhost:3000
- API: http://localhost:8080
- API docs (Swagger): http://localhost:8080/docs

If you see `dockerDesktopLinuxEngine` pipe errors on Windows, start Docker Desktop and make sure it is using Linux containers.

`docker-compose.yml` does not load `.env` into the backend and worker containers. They use the values set in the compose file plus the defaults in `backend/app/config.py`. `SCRAPINGBEE_API_KEY` is the exception: Compose reads it from `.env` and passes it through.

## Running a scan

1. Add URLs in the UI.
2. Click **Run Scan**.
3. Watch the progress bar. The worker scrapes each URL and results appear when the job finishes.

Logs:

```powershell
docker compose logs -f backend
docker compose logs -f worker
```

## Local development (no Docker)

Full instructions are in [SETUP.md](SETUP.md). In short, you need MongoDB and Redis running (Docker is easiest), then three terminals:

```powershell
# 1. API
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m playwright install chromium
python run.py                 # serves on BACKEND_PORT (8080)

# 2. Worker (same venv)
cd backend
celery -A app.celery_app.celery_app worker -l INFO --concurrency=2 --pool=solo

# 3. Frontend
cd frontend
npm ci
npm run dev
```

On Windows, Celery's default process pool doesn't work, so use `--pool=solo` (or `--pool=threads`).

## How a page is checked

1. **Fetch.** `scraper/scraper.py` tries Playwright (a real Chromium browser) first, then ScrapingBee if `SCRAPINGBEE_API_KEY` is set, then a plain HTTP request. Set `SCRAPER_SCRAPINGBEE_FIRST=true` to try ScrapingBee first.
2. **Block check.** If the page is a CAPTCHA, "access denied", or similar challenge page, the result is `error`, not `unavailable`.
3. **Detect.** `scraper/detector.py` looks for buy buttons using `scraper/detection_rules.json` and checks for "out of stock" wording.
4. **Variants.** When Playwright fetched the page, it also selects each size or color option and checks whether the buy button becomes usable. The product counts as available if any variant is purchasable.

Details: [docs/DETECTION_EXPLAINED.md](docs/DETECTION_EXPLAINED.md).

## Getting past bot blocking

Big retailers often serve CAPTCHA or "robot or human" pages to automated browsers. You can pass the check once by hand and reuse the cookies:

```powershell
$env:BOOTSTRAP_URL="https://www.target.com/p/-/A-88920975"
python scraper\bootstrap_state.py
```

A browser window opens. Solve any challenge, and once the product page loads, the script saves cookies to `scraper/storage_state/<domain>.json`. Later scans load that file automatically. These files contain session cookies and are git-ignored.

Scans that run in Docker get blocked more often than local runs, because the container's browser is headless Linux Chromium claiming to be Windows Chrome. See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md#scans-blocked-in-docker-but-not-locally).

## Documentation

- [SETUP.md](SETUP.md): installation and configuration reference
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): components, data flow, database collections
- [docs/API_REFERENCE.md](docs/API_REFERENCE.md): HTTP endpoints
- [docs/DETECTION_EXPLAINED.md](docs/DETECTION_EXPLAINED.md): how availability is decided
- [SCRAPINGBEE.md](SCRAPINGBEE.md): optional ScrapingBee integration
- [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md): working on the code, adding site rules
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md): common problems
- [FAILURE_MODES.md](FAILURE_MODES.md): known risks and weak spots

## Repository layout

```
backend/app/
  api/            FastAPI routes: urls.py, scan.py, logs.py
  tasks/          Celery tasks: enqueue_scan fan-out, scrape_one_url
  celery_app.py   Celery configuration
  config.py       Settings (env vars and defaults)
  database.py     MongoDB connection and indexes
frontend/src/     Next.js pages, components, API client
scraper/
  scraper.py            fetch chain, block detection, variant probing
  detector.py           HTML button detection
  detection_rules.json  site-specific and generic selectors
  bootstrap_state.py    save cookies after solving a challenge by hand
  benchmark_methods.py  compare fetch methods on golden_urls.py
scripts/debug/    one-off analysis scripts from detection tuning (some are outdated)
```
