# Troubleshooting

Start with the logs. Most problems show up in one of these:

```powershell
docker compose ps                       # are all 5 services up?
docker compose logs -f worker           # scraping
docker compose logs -f backend          # API
curl http://localhost:8080/health       # {"status":"healthy","database":"connected"}
```

---

## Startup

### `dockerDesktopLinuxEngine` pipe error, or `docker` not found

Docker Desktop isn't running, or it's set to Windows containers. Start Docker Desktop and switch to Linux containers.

### Port already in use (3000, 8080, 27017, 6379)

```powershell
netstat -ano | findstr :8080
taskkill /PID <PID> /F
```

Or change the host side of the mapping in `docker-compose.yml`, e.g. `"8081:8000"`. If you move the API port, also update `NEXT_PUBLIC_API_URL` for the frontend and rebuild it.

### `/health` says `degraded`

The API can't reach MongoDB. In Docker, check `docker compose logs mongodb`. Locally, make sure MongoDB is running and `MONGODB_URL` in `.env` points at it (`mongodb://localhost:27017`).

---

## Scans

### Scan stays "queued" and never progresses

Nothing is consuming the queue. Check that:

- the `worker` container is running (`docker compose ps`), or locally, that you started the Celery worker,
- Redis is running and `REDIS_URL` matches on both the API and the worker.

`start-dev.bat` doesn't start Redis or the worker. Start them yourself (see [../SETUP.md](../SETUP.md#local-setup-no-docker-for-the-app)).

On Windows, a local worker started without `--pool=solo` (or `--pool=threads`) may start but never run tasks.

### Every URL is `error`

Look at `error_message` on the results (or in the results table):

| `error_message` | Cause |
|-----------------|-------|
| `blocked:captcha`, `blocked:robot or human`, `blocked:access denied` … | The retailer served a bot-check page. See [Blocked by the retailer](#blocked-by-the-retailer) |
| `All fetch methods failed …` | No method returned usable HTML. Check the worker log for the underlying Playwright, ScrapingBee, or HTTP error |
| `Scan timed out after Ns` | The URL used its whole time budget. Usually slow variant probing or slow page loads. Raise `SCRAPER_PER_URL_TASK_TIMEOUT_SECONDS` or set `SCRAPER_CHECK_VARIANTS=false` |
| `Worker hit Celery soft time limit …` | Raise `CELERY_SCRAPE_TASK_SOFT_TIME_LIMIT` / `CELERY_SCRAPE_TASK_TIME_LIMIT` |
| `Executable doesn't exist` / `playwright install` in the worker log | Browsers aren't installed. Run `python -m playwright install chromium` (and `firefox` if you scan Staples or Office Depot) |

**Staples and Office Depot in Docker:** the scraper uses Firefox for these two sites, but `backend/Dockerfile` only installs Chromium. Until `playwright install firefox` is added to the Dockerfile, Playwright fails on them in Docker and they fall back to ScrapingBee or plain HTTP.

### Blocked by the retailer

Amazon, Target, Walmart, Kohl's, Staples, and Home Depot regularly block automated browsers. Options, cheapest first:

1. **Save cookies after solving a challenge by hand:**

   ```powershell
   $env:BOOTSTRAP_URL="https://www.target.com/p/-/A-88920975"
   python scraper\bootstrap_state.py
   ```

   Later scans load `scraper/storage_state/target.com.json` automatically. Cookies expire, so repeat this when blocks come back.
2. **Run with a visible browser** by setting `SCRAPER_HEADLESS=false` (only works locally, not in Docker).
3. **Enable ScrapingBee** with `SCRAPINGBEE_API_KEY`. See [../SCRAPINGBEE.md](../SCRAPINGBEE.md).
4. **Use the retailer's official API** where one exists (e.g. Amazon Product Advertising API).

Set `SCRAPER_SCREENSHOT_DIR` in the environment to save a screenshot of each block page.

### Scans blocked in Docker but not locally

Sites check whether a browser looks like a real person's. The Docker setup gives away more signals than a local run:

- **Mismatched fingerprint.** The scraper tells sites it's Chrome 120 on Windows. Inside the container it's actually Linux Chromium, and page JavaScript can see that: `navigator.platform` is `Linux x86_64`, only the Liberation fonts are installed, and there's no GPU, so graphics are software-rendered. Chromium's real version doesn't match 120 either. Locally on Windows these line up.
- **Always headless.** The container has no display, and `docker-compose.yml` doesn't set `SCRAPER_HEADLESS`, so the default (`true`) applies. Headless browsers are easier to detect. `.env` isn't loaded into the containers, so setting it there has no effect.
- **Data-center IP**, if the containers run on a cloud server rather than your own PC. Many retailers block data-center IP ranges outright. Docker Desktop on your PC uses your home IP, so this doesn't apply there.
- **Cookies from a different browser.** Files in `storage_state/` created on Windows are reused by the Linux browser. Anti-bot services tie their cookies to a fingerprint, so this can look suspicious.

To confirm, open a fingerprint test page such as `https://bot.sannysoft.com` with the scraper in both environments and compare screenshots.

Possible fixes: send a Linux user agent in the container (or don't override it), install more fonts in `backend/Dockerfile`, run a visible browser under `xvfb-run` with `SCRAPER_HEADLESS=false`, use real Chrome (`playwright install chrome`, `channel="chrome"`), run `bootstrap_state.py` inside the container, and on cloud servers route through a residential proxy.

### Product shows `unavailable` but is in stock

1. Check `error_message`. If it's set, it's a fetch or block problem, not detection.
2. Check `unavailability_override`. If true, "out of stock" or similar wording was found in the product area (possibly for another variant or seller). See [DETECTION_EXPLAINED.md](DETECTION_EXPLAINED.md#4-out-of-stock-override).
3. Check `variants`. If every variant is unavailable, the default selection may be out of stock while others weren't probed. Variant probing is capped at 25 to 30 options.
4. Open the page yourself and inspect the buy button. If the site isn't covered by `detection_rules.json`, add a rule and restart the worker.

### Product shows `available` but is out of stock

Usually the site renders a normal-looking button and only disables it with JavaScript, or it uses wording the detector doesn't know ("Pre-order", "Sign in to see price"). Add the site's disabled class or wording to `_DISABLED_CLASSES`, `_NEGATIVE_BUY_TEXT`, or `_UNAVAILABLE_SIGNALS` in `scraper/detector.py`.

### Scans are slow

Each URL can take 10 to 60 seconds with Playwright and variant checks. To go faster:

- add workers: `docker compose up -d --scale worker=3` (about 200 MB of RAM per browser),
- set `SCRAPER_CHECK_VARIANTS=false`,
- enable ScrapingBee and set `SCRAPER_SCRAPINGBEE_FIRST=true` (faster, but no variant checks, and costs credits).

The frontend stops polling after 30 minutes. If a very large scan outlives that, the job keeps running. Refresh the page later to see results.

---

## Frontend

### "Failed to fetch" / network errors

- The frontend calls `NEXT_PUBLIC_API_URL` (default `http://localhost:8080`). Check the browser's Network tab for the address it's actually using.
- For CORS errors, add the frontend's origin to `CORS_ORIGINS`. It accepts a JSON list or a comma-separated string. In Docker, set it in `docker-compose.yml`.
- `NEXT_PUBLIC_API_URL` is baked in at build time. After changing it, rebuild with `docker compose up -d --build frontend`.

### Progress bar never finishes

Open `GET /api/scan/{job_id}/status` directly. If `completed` stops increasing, check the worker log for a crash or a stuck URL. The per-URL timeout should eventually record an error for it.

---

## Data

### Reset everything

```powershell
curl -X DELETE http://localhost:8080/api/urls           # URLs and results
curl -X DELETE http://localhost:8080/api/scan/results   # results only
docker compose down -v                                  # also wipes the MongoDB volume
```

### Inspect the database

```powershell
docker exec -it ubique-mongodb mongosh ubique_product_checker
db.scan_jobs.find().sort({created_at:-1}).limit(1)
db.scan_results.find({status:"error"}, {url:1, error_message:1})
```

---

## Local Python and Node problems

- **Playwright install fails:** `python -m playwright install --with-deps chromium` on Linux. On Windows, plain `install chromium` is enough.
- **`NotImplementedError` from asyncio on Windows:** start the API with `python run.py`, which sets the Proactor event loop Playwright needs.
- **npm errors:** delete `frontend/node_modules`, then `npm ci`. Use Node 18 or newer.
