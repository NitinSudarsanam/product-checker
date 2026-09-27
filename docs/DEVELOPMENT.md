# Development Guide

For installing and running the stack, see [../SETUP.md](../SETUP.md). This page covers working on the code.

## Where things live

| Change | File(s) |
|--------|---------|
| API route | `backend/app/api/*.py`, registered in `backend/app/main.py` |
| Request/response models, URL validation | `backend/app/models/schemas.py` |
| Settings | `backend/app/config.py` (add the field there; env var names match, case-insensitive) |
| Scan job flow, progress counters | `backend/app/tasks/scan_tasks.py` |
| Fetching, block detection, variants | `scraper/scraper.py` |
| Button detection logic | `scraper/detector.py` |
| Site selectors and text | `scraper/detection_rules.json` |
| UI | `frontend/src/pages/index.tsx`, `frontend/src/components/` |
| Frontend API client | `frontend/src/lib/api.ts` |

The backend imports the scraper as a package (`from scraper import scrape_url`). In Docker, `./scraper` is mounted at `/app/scraper`. Locally, `scraper/scraper.py` adds `backend/` to `sys.path` so it can read `app.config`.

## What needs a restart

| Changed | Restart |
|---------|---------|
| `detection_rules.json`, `scraper/*.py` | worker (`docker compose restart worker`). Rules are loaded once at import |
| `backend/app/**` | backend and worker. In Docker this code is baked into the image, so rebuild with `docker compose up -d --build backend worker` |
| `docker-compose.yml` environment | `docker compose up -d` |
| frontend | `npm run dev` hot-reloads locally. Docker needs `docker compose up -d --build frontend` |

## Testing a single URL

Without the API or worker:

```python
# from product-checker/, with the backend venv active
import asyncio, sys
sys.path.insert(0, ".")
from scraper import scrape_url

r = asyncio.run(scrape_url("https://www.wayfair.com/..."))
print(r["status"], r["scrape_method"], r["error_message"], r["variants"])
```

To see what the browser saw, set `SCRAPER_SCREENSHOT_DIR` in your shell before running (it isn't read from `.env`). Screenshots are saved on navigation errors and block pages. Setting `SCRAPER_HEADLESS=false` in `.env` opens a visible browser window.

## Scraper tooling

| Script | Purpose |
|--------|---------|
| `scraper/scraper.py` | `python scraper.py` runs a smoke test against `example.com` |
| `scraper/bootstrap_state.py` | Opens a browser at `BOOTSTRAP_URL`. Solve any challenge by hand and it saves cookies to `storage_state/<domain>.json`. Options: `BOOTSTRAP_ENGINE` (chromium / firefox / webkit), `BOOTSTRAP_HEADLESS`, `BOOTSTRAP_TIMEOUT_S` (default 300), `BOOTSTRAP_READY_SELECTOR` |
| `scraper/benchmark_methods.py` | Runs Playwright and ScrapingBee against `golden_urls.py` (or `BENCH_URLS`) and saves HTML and screenshots. Output defaults to `/app/scraper/bench_artifacts` (the container path). Set `BENCH_OUT_DIR` when running on the host |
| `scraper/screenshot_urls.py` | Screenshots a list of URLs |
| `scraper/test_*.py`, `scraper/debug_*.py`, `scraper/check_*.py` | Older ad-hoc checks |
| `scripts/debug/` | One-off analysis scripts from tuning Walmart, Wayfair, and Home Depot. Several import `fetch_dynamic_html`, which no longer exists, and won't run without updating |

Output folders (`storage_state/`, `test_artifacts/`, `bench_artifacts*/`, `screenshots/`) are git-ignored. `storage_state/` holds live session cookies, so don't commit or share it.

There's no automated test suite yet. No pytest tests or frontend tests exist.

## Adding site rules

See [DETECTION_EXPLAINED.md](DETECTION_EXPLAINED.md#adding-or-fixing-a-site). In short, add the domain under `add_to_cart.domains` and/or `buy_now.domains` in `detection_rules.json` with `selectors` and `text`, then restart the worker.

If the site needs a longer wait before the button appears, add it to the host list in `_playwright_scrape()` that waits for common add-to-cart hooks (currently Kohl's, Lowe's, Office Depot, Overstock, Staples). If it has product-area containers where "out of stock" wording is trustworthy, add them to `_product_scope_elements()` in `detector.py`.

## Adding an API endpoint

1. Add a route in `backend/app/api/` (or a new router module).
2. Register new routers with `app.include_router(...)` in `backend/app/main.py`.
3. Add a function to `frontend/src/lib/api.ts`.
4. Document it in [API_REFERENCE.md](API_REFERENCE.md).

Anything slow (network, browser) belongs in a Celery task in `backend/app/tasks/`, not in the request handler. Tasks are synchronous and use PyMongo. They run async scraper code with `asyncio.run()`.

## Windows notes

- Playwright needs the Proactor event loop. `scraper.py`, `main.py`, and `run.py` set `WindowsProactorEventLoopPolicy`, so start the API with `python run.py` rather than `uvicorn --reload`.
- Run Celery with `--pool=solo` (or `--pool=threads`). The default process pool doesn't work on Windows.

## Useful commands

```powershell
docker compose logs -f worker                 # watch scraping
docker compose logs --tail=100 backend
docker exec -it ubique-mongodb mongosh ubique_product_checker
docker compose down; docker compose build --no-cache; docker compose up -d
```

## Commit messages

Conventional commits: `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`.
