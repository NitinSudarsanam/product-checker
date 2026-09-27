# Setup and Configuration

## Prerequisites

- **Docker Desktop** (Linux containers) for the Docker setup, or
- **Local setup:** Python 3.11+, Node.js 18+, and Docker (or local installs) for MongoDB 7 and Redis 7

## Docker

```powershell
cd product-checker
copy .env.example .env
docker compose up -d --build
```

This starts five containers: `mongodb`, `redis`, `backend`, `worker`, and `frontend`.

| What | URL |
|------|-----|
| UI | http://localhost:3000 |
| API | http://localhost:8080 |
| Swagger docs | http://localhost:8080/docs |
| Health check | http://localhost:8080/health |

`start.bat` does the same thing (copies `.env` if missing, then runs Compose). Its final message still lists port 8000, but the API is on 8080.

Stop everything with `docker compose down`, or `docker compose down -v` to also delete the MongoDB data volume.

To run more scans in parallel, add workers:

```powershell
docker compose up -d --scale worker=3
```

Each worker runs up to 2 Celery tasks, and each task can open a Chromium browser (roughly 200 MB each).

### How configuration reaches the containers

The backend and worker containers do **not** read `.env`. Their settings come from the `environment:` blocks in `docker-compose.yml`, and anything not set there falls back to the defaults in `backend/app/config.py`. The only value passed through from `.env` is `SCRAPINGBEE_API_KEY`. To change a setting in Docker (for example `SCRAPER_CHECK_VARIANTS`), add it to the compose file.

## Local setup (no Docker for the app)

1. **Start MongoDB and Redis:**

   ```powershell
   docker run -d --name ubique-mongo -p 27017:27017 mongo:7.0
   docker run -d --name ubique-redis -p 6379:6379 redis:7.2-alpine
   ```

2. **Create `.env`** in `product-checker/` from `.env.example`. The defaults point at `localhost` for MongoDB and Redis.

3. **Backend API:**

   ```powershell
   cd backend
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   python -m playwright install chromium
   python run.py
   ```

   `run.py` sets the Windows asyncio event-loop policy that Playwright needs, then serves on `BACKEND_PORT` (8080).

4. **Worker** (second terminal, same virtual environment):

   ```powershell
   cd backend
   .venv\Scripts\activate
   celery -A app.celery_app.celery_app worker -l INFO --concurrency=2 --pool=solo
   ```

   Celery's default process pool does not run on Windows, so use `--pool=solo` or `--pool=threads`.

5. **Frontend** (third terminal):

   ```powershell
   cd frontend
   npm ci
   npm run dev
   ```

   The frontend reads the API address from `NEXT_PUBLIC_API_URL` in `frontend/.env.local` (defaults to `http://localhost:8080`).

`start-dev.bat` starts MongoDB, the API (inside a conda environment named `product-checker`), and the frontend. It does **not** start Redis or the worker, so scans stay queued until you start those yourself.

### Testing the scraper on its own

```powershell
cd scraper
python scraper.py
```

This runs a quick smoke test against `example.com`. To test a real product page, see [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md#testing-a-single-url).

## Environment variables

Read by `backend/app/config.py` (names are case-insensitive).

### Core

| Variable | Default | Purpose |
|----------|---------|---------|
| `MONGODB_URL` | `mongodb://localhost:27017` | MongoDB connection string |
| `MONGODB_DATABASE` | `ubique_product_checker` | Database name |
| `MONGODB_MAX_POOL_SIZE` | `20` | Connection pool size |
| `REDIS_URL` | `redis://localhost:6379/0` | Celery broker and result store |
| `BACKEND_HOST` / `BACKEND_PORT` | `0.0.0.0` / `8080` | Where `run.py` serves the API |
| `BACKEND_RELOAD` | `false` | Auto-reload on code changes |
| `CORS_ORIGINS` | `["http://localhost:3000","http://localhost:3001"]` | Allowed frontend origins. Accepts a JSON list or a comma-separated string |
| `SECRET_KEY` | placeholder | Not used yet. The app logs a warning if it's still the placeholder |
| `LOG_LEVEL` / `LOG_FILE` | `INFO` / `logs/app.log` | Logging. Relative paths resolve from `product-checker/` |

### Scraper

| Variable | Default | Purpose |
|----------|---------|---------|
| `SCRAPER_USE_PLAYWRIGHT` | `true` | Use a real browser. Turning it off also turns off variant checks |
| `SCRAPER_HEADLESS` | `true` | Run the browser without a window. Some sites block headless browsers more |
| `SCRAPER_CHECK_VARIANTS` | `true` | Click through size/color options and check each |
| `SCRAPER_TIMEOUT` | `30` | Page navigation timeout in seconds (5× for Amazon and Walmart) |
| `SCRAPER_SCRAPINGBEE_FIRST` | `false` | Try ScrapingBee before Playwright |
| `SCRAPER_PER_URL_TASK_TIMEOUT_SECONDS` | `0` | Total time allowed per URL. `0` means automatic (`max(timeout + 60, timeout × 12 + 180)`) |
| `PLAYWRIGHT_MAX_CONCURRENT` | `2` | Browsers open at once per worker process |

`SCRAPER_MAX_CONCURRENT` and `SCRAPER_USER_AGENT` appear in `.env.example` but nothing reads them. The user agent is hard-coded in `scraper/scraper.py`.

These three are read directly from the process environment, **not** from `.env`. Set them in your shell or in `docker-compose.yml`:

| Variable | Default | Purpose |
|----------|---------|---------|
| `SCRAPER_STORAGE_STATE_DIR` | `scraper/storage_state` | Where saved cookies are read from |
| `SCRAPER_SCREENSHOT_DIR` | empty | If set, saves a screenshot when navigation fails or a block page is detected |
| `SCRAPER_RETRY_FRESH_CONTEXT` | `true` | After a block, retry once without saved cookies |

### ScrapingBee (optional)

| Variable | Default | Purpose |
|----------|---------|---------|
| `SCRAPINGBEE_API_KEY` | empty | Enables ScrapingBee. Leave empty to skip it |
| `SCRAPINGBEE_COUNTRY_CODE` | `us` | Proxy country |
| `SCRAPINGBEE_MAX_WORKERS` | `5` | Thread pool size for the ScrapingBee client |
| `SCRAPINGBEE_MAX_CONCURRENT` | `5` | ScrapingBee requests at once |
| `SCRAPINGBEE_RPS` | `0` | Requests-per-second cap. `0` disables it |

### Celery

| Variable | Default | Purpose |
|----------|---------|---------|
| `CELERY_CONCURRENCY` | `2` | Informational. The actual value is the `--concurrency` flag on the worker command |
| `CELERY_SCRAPE_TASK_SOFT_TIME_LIMIT` | `1080` | Seconds before Celery interrupts a scrape task |
| `CELERY_SCRAPE_TASK_TIME_LIMIT` | `1200` | Seconds before Celery kills a scrape task |

## Before deploying anywhere public

- `docker-compose.yml` publishes MongoDB (27017) and Redis (6379) on all interfaces with no authentication. Remove those `ports:` entries or add credentials.
- There is no login on the API and no rate limit on `POST /api/scan/run`.
- Set `CORS_ORIGINS` to your real frontend origin.
- Build the frontend with the correct `NEXT_PUBLIC_API_URL`. It's baked in at build time.
- Expect more bot blocking from a cloud server than from a home connection. See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md#scans-blocked-in-docker-but-not-locally).

## Backup and restore

```powershell
docker exec ubique-mongodb mongodump --out /backup
docker cp ubique-mongodb:/backup ./backup

docker cp ./backup ubique-mongodb:/backup
docker exec ubique-mongodb mongorestore /backup
```
